# graph/tools.py

"""
tools.py 역할
Gemini(Agent Node)가 호출할 수 있는 Tool 7개를 정의한다.

각 Tool은 해당 Service 메서드를 호출하고, 성공하면 결과를,
실패(이름 붙은 예외)하면 그 상황에 맞는 안내 문장을 만들어
{success, code, message, data} 형태로 통일해서 반환한다.

- code: 성공이면 "SUCCESS", 실패면 발생한 예외 클래스명을 그대로 씀
        (type(e).__name__), 정책 검색의 "정책 없음"만 예외로
        "POLICY_NOT_FOUND"를 씀 (예외가 아니라 정상 반환값이라서)
- data: ORM 객체를 그대로 넣지 않고, 필요한 필드만 뽑은 plain dict/list

이 파일이 하지 않는 일:
- 업무 규칙 판단 (Service 담당)
- DB 세션·트랜잭션 관리 (Service 담당)
- Tool 선택, 대화 흐름, 최종 응답 문구 결정 (Agent Node의 Gemini 담당)
- "지원하지 않는 업무" vs "필요한 Tool이 없음" 판단 (agent_prompt.py 담당)

user_id는 Gemini에게 파라미터로 노출하지 않고, create_tools() 인자로
받아 클로저로 고정한다 — 다른 고객 정보 조회를 원천 차단하기 위함이다.

이름 모르는(예상 못한) 시스템 예외는 원칙적으로 안 잡고 그대로 전파한다.
단, save_support_ticket은 다른 Tool이 전부 실패했을 때 가는 마지막
안전망이라 예외적으로 Exception까지 잡아 사과 문구로 응답한다.
"""

from langchain_core.tools import tool

from application.rag_service import RagService
from infrastructure.llm_client import LlmClientError
from infrastructure.vector_store import VectorStoreError
from prompts.rag_prompt import RagPromptError, NO_POLICY_ANSWER_MESSAGE
from datetime import timedelta

from services.product_service import (
    ProductService,
    ProductSearchConditionRequiredError,
    ProductPriceTypeError,
    ProductPriceInvalidError,
    ProductPriceRangeError,
    ProductIdRequiredError,
    ProductIdTypeError,
    ProductNotFoundError,
)
from services.order_service import (
    OrderService,
    OrderNumberRequiredError,
    OrderNumberTypeError,
    OrderNotFoundError,
    OrderQuantityRequiredError,
    OrderQuantityTypeError,
    OrderQuantityInvalidError,
)
from services.refund_service import (
    RefundService,
    RefundReasonRequiredError,
    RefundNotAllowedError,
    DuplicateRefundRequestError,
)
from services.support_ticket_service import (
    SupportTicketService,
    SupportTicketQuestionRequiredError,
    InvalidSupportTicketReasonError,
    SupportTicketUserNotFoundError,
)


ORDER_STATUS_LABELS = {
    "preparing": "상품 준비 중",
    "shipped": "배송 중",
    "delivered": "배송 완료",
    "cancelled": "주문 취소",
    "refunded": "환불 완료",
}

KST_OFFSET = timedelta(hours=9)

def _status_label(status: str) -> str:
    """DB status 값을 고객에게 보여줄 한글 표현으로 바꾼다. 매핑에 없으면 원본 그대로."""
    return ORDER_STATUS_LABELS.get(status, status)


def _item_summary(items: list[dict]) -> str:
    """상품 목록을 "대표상품명 외 N건" 형태로 요약한다. LLM이 직접 세지 않도록 서버에서 미리 계산."""
    if not items:
        return "-"
    first_name = items[0]["product_name"]
    if len(items) > 1:
        return f"{first_name} 외 {len(items) - 1}건"
    return first_name


def _format_order_time(created_at) -> str | None:
    """DB에 UTC로 저장된 주문 시각을 KST(UTC+9) 문자열로 변환한다."""
    if created_at is None:
        return None
    return (created_at + KST_OFFSET).strftime("%Y-%m-%d %H:%M")


def create_tools(
    user_id: int,
    product_service: ProductService,
    order_service: OrderService,
    refund_service: RefundService,
    support_ticket_service: SupportTicketService,
    rag_service: RagService,
) -> list:
    """현재 고객(user_id)과 이미 조립된 Service들을 받아 Gemini에게 넘길 Tool 목록을 만든다."""

    @tool
    def search_policy(question: str | None = None) -> dict:
        """배송 기간, 환불 규정, 주문 절차 등 정책 문서에 기반한 질문에 답변한다."""
        try:
            answer = rag_service.answer_question(question)
        except (LlmClientError, VectorStoreError, RagPromptError) as e:
            print(f"[ERROR] search_policy 시스템 오류: {type(e).__name__}: {e}")
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "죄송해요, 지금 정책 검색에 문제가 생겼어요. 잠시 후 다시 시도해주세요.",
                "data": None,
            }

        if answer.strip() == NO_POLICY_ANSWER_MESSAGE:
            return {"success": False, "code": "POLICY_NOT_FOUND", "message": answer, "data": None}

        return {"success": True, "code": "SUCCESS", "message": answer, "data": None}

    @tool
    def search_products(
        keywords: list[str] | None = None,
        price_min: int | None = None,
        price_max: int | None = None,
    ) -> dict:
        """상품 종류, 색상, 브랜드 등 키워드나 가격대로 상품을 검색한다."""
        if keywords is not None and not isinstance(keywords, list):
            return {
                "success": False,
                "code": "InvalidKeywordsType",
                "message": "찾으시는 상품 조건을 다시 한번 말씀해주시겠어요?",
                "data": None,
            }

        try:
            products = product_service.search_products(
                keywords=keywords, price_min=price_min, price_max=price_max
            )
        except ProductSearchConditionRequiredError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "찾으시는 상품의 종류나 색상, 가격대를 알려주시겠어요?",
                "data": None,
            }
        except (ProductPriceTypeError, ProductPriceInvalidError) as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "가격 조건을 다시 확인해주세요.",
                "data": None,
            }
        except ProductPriceRangeError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "최소 가격이 최대 가격보다 클 수 없어요. 다시 확인해주시겠어요?",
                "data": None,
            }

        data = [{"product_id": p.id, "name": p.name, "price": p.price} for p in products]

        if not data:
            return {
                "success": True,
                "code": "SUCCESS",
                "message": "조건에 맞는 상품을 찾지 못했어요. 다른 조건으로 찾아드릴까요?",
                "data": [],
            }

        names = ", ".join(p["name"] for p in data)
        return {
            "success": True,
            "code": "SUCCESS",
            "message": f"조건에 맞는 상품을 찾았어요: {names}",
            "data": data,
        }

    @tool
    def get_orders(order_number: str | None = None) -> dict:
        """고객 본인의 주문을 조회한다. 주문번호가 있으면 해당 주문 1건을, 없으면 전체 주문 목록을 조회한다."""
        if order_number is None:
            orders = order_service.get_customer_orders(user_id)
            data = []
            for o in orders:
                items = [
                    {"product_name": item.product.name, "quantity": item.quantity}
                    for item in o.order_items
                ]
                data.append({
                    "order_number": o.order_number,
                    "status": o.status,
                    "total_amount": o.total_amount,
                    "item_summary": _item_summary(items),
                })

            if not data:
                return {"success": True, "code": "SUCCESS", "message": "아직 주문 내역이 없어요.", "data": []}

            summary = " / ".join(
                f"{d['order_number']} | {d['item_summary']} | {_status_label(d['status'])} | {d['total_amount']:,}원"
                for d in data
            )
            return {
                "success": True,
                "code": "SUCCESS",
                "message": f"주문 내역은 다음과 같아요: {summary}",
                "data": data,
            }

        try:
            order = order_service.get_customer_order(user_id, order_number)
        except (OrderNumberRequiredError, OrderNumberTypeError) as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "주문번호를 다시 한번 확인해주시겠어요?",
                "data": None,
            }
        except OrderNotFoundError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "주문을 확인할 수 없어요. 주문번호를 다시 한번 확인해주시겠어요?",
                "data": None,
            }

        items = [
            {
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.unit_price * item.quantity,
            }
            for item in order.order_items
        ]
        data = {
            "order_number": order.order_number,
            "status": order.status,
            "order_time": _format_order_time(order.created_at),
            "total_amount": order.total_amount,
            "items": items,
        }
        item_summary = ", ".join(f"{i['product_name']} {i['quantity']}개" for i in items)
        return {
            "success": True,
            "code": "SUCCESS",
            "message": (
                f"{order.order_number} 주문은 현재 {_status_label(order.status)} 상태예요. "
                f"({item_summary}, 총 {order.total_amount:,}원)"
            ),
            "data": data,
        }

    @tool
    def preview_order(product_id: int | None = None, quantity: int | None = None) -> dict:
        """
        고객이 상품과 수량을 정했을 때, 실제 주문 전에 예상 금액을 미리 계산해서 보여준다.
        DB에 저장하지 않는다. 이 결과를 고객이 명확히 확인한 후에만 주문 생성 Tool을 호출해야 한다.
        """
        try:
            preview = order_service.preview_order(product_id, quantity)
        except (OrderQuantityRequiredError, OrderQuantityTypeError, OrderQuantityInvalidError) as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "몇 개 주문하실지 다시 한번 알려주시겠어요?",
                "data": None,
            }
        except (ProductIdRequiredError, ProductIdTypeError) as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "주문하실 상품을 다시 한번 알려주시겠어요?",
                "data": None,
            }
        except ProductNotFoundError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "죄송해요, 해당 상품은 현재 주문하실 수 없어요.",
                "data": None,
            }

        return {
            "success": True,
            "code": "SUCCESS",
            "message": (
                f"{preview['product_name']} {preview['quantity']}개, "
                f"총 {preview['total_amount']:,}원이에요. 주문하시겠어요?"
            ),
            "data": preview,
        }

    @tool
    def create_order(product_id: int | None = None, quantity: int | None = None) -> dict:
        """
        고객이 미리보기 내용을 보고 명확히 주문을 확정했을 때만 호출해서 실제 주문을 생성한다.
        고객의 명확한 동의 없이는 절대 호출하지 않는다.
        """
        try:
            order = order_service.create_order(user_id, product_id, quantity)
        except (OrderQuantityRequiredError, OrderQuantityTypeError, OrderQuantityInvalidError) as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "몇 개 주문하실지 다시 한번 알려주시겠어요?",
                "data": None,
            }
        except (ProductIdRequiredError, ProductIdTypeError) as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "주문하실 상품을 다시 한번 알려주시겠어요?",
                "data": None,
            }
        except ProductNotFoundError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "죄송해요, 해당 상품은 현재 주문하실 수 없어요.",
                "data": None,
            }

        items = [
            {"product_name": item.product.name, "quantity": item.quantity, "unit_price": item.unit_price}
            for item in order.order_items
        ]
        data = {
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": order.total_amount,
            "items": items,
        }
        return {
            "success": True,
            "code": "SUCCESS",
            "message": f"주문이 완료됐어요. 주문번호는 {order.order_number}예요.",
            "data": data,
        }

    @tool
    def request_refund(order_number: str | None = None, reason: str | None = None) -> dict:
        """고객이 주문 전체에 대한 환불을 요청할 때 사용한다. 부분 환불 요청에는 사용하지 않는다."""
        try:
            refund = refund_service.request_refund(user_id, order_number, reason)
        except RefundReasonRequiredError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "환불 사유를 알려주시겠어요?",
                "data": None,
            }
        except (OrderNumberRequiredError, OrderNumberTypeError) as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "주문번호를 다시 한번 확인해주시겠어요?",
                "data": None,
            }
        except OrderNotFoundError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "주문을 확인할 수 없어요. 주문번호를 다시 한번 확인해주시겠어요?",
                "data": None,
            }
        except RefundNotAllowedError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "죄송해요, 이 주문은 현재 상태에서는 환불이 어려워요.",
                "data": None,
            }
        except DuplicateRefundRequestError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "이미 처리 중인 환불 요청이 있어요.",
                "data": None,
            }

        data = {
            "order_number": refund.order.order_number,
            "status": refund.status,
            "reason": refund.reason,
        }
        return {
            "success": True,
            "code": "SUCCESS",
            "message": f"{refund.order.order_number} 주문의 환불 요청이 접수됐어요. 순차적으로 처리해드릴게요.",
            "data": data,
        }

    @tool
    def save_support_ticket(question: str | None = None, reason: str | None = None) -> dict:
        """
        다른 어떤 Tool로도 고객의 요청을 처리할 수 없을 때 사용하는 최후의 수단이다.
        reason은 반드시 다음 4개 값 중 하나여야 한다:
        '지원하지 않는 업무', '정책 문서에 관련 내용 없음', '필요한 Tool이 없음', '사람의 확인이 필요함'.
        """
        try:
            ticket = support_ticket_service.create_ticket(user_id, question, reason)
        except SupportTicketQuestionRequiredError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "어떤 점이 궁금하신지 알려주시겠어요?",
                "data": None,
            }
        except InvalidSupportTicketReasonError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "문의 접수 중 문제가 발생했어요.",
                "data": None,
            }
        except SupportTicketUserNotFoundError as e:
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "고객 정보를 확인할 수 없어요.",
                "data": None,
            }
        except Exception as e:
            # 안전망: 이름 없는 시스템 예외까지 전부 잡아서 사과 문구로 응답 (확정 사항)
            print(f"[ERROR] save_support_ticket 예상 못한 오류: {type(e).__name__}: {e}")
            return {
                "success": False,
                "code": type(e).__name__,
                "message": "죄송해요, 일시적인 오류가 발생했어요. 잠시 후 다시 시도해주세요.",
                "data": None,
            }

        data = {"question": ticket.question, "reason": ticket.reason, "status": ticket.status}
        return {
            "success": True,
            "code": "SUCCESS",
            "message": "문의가 접수됐어요. 담당자가 확인 후 안내드릴게요.",
            "data": data,
        }

    return [
        search_policy,
        search_products,
        get_orders,
        preview_order,
        create_order,
        request_refund,
        save_support_ticket,
    ]