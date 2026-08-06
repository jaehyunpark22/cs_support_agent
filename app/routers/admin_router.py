# app/routers/admin_router.py

"""
admin_router.py 역할
관리자가 지원 문의/주문/환불 현황을 조회하고, 지원 문의의 처리 상태를
변경하는 HTTP 엔드포인트를 제공한다.

관리자 기능은 Agent/Graph를 거치지 않고 Service를 직접 호출한다
(v12에서 확정). agent_service.py의 _build_graph()를 재사용하지 않고,
필요한 Repository/Service만 이 파일에서 직접 조립한다
(RagService/Tool/그래프는 관리자 기능에 필요 없다).

Repository/Service 조립 순서는 agent_service.py의 _build_graph()와
동일한 규칙을 따른다: product_repository → order_repository →
refund_repository → support_ticket_repository → user_repository
→ product_service → order_service → refund_service → support_ticket_service.
(product_service는 admin 기능에서 실제로 쓰이진 않지만, order_service
생성자가 요구해서 조립 순서에 포함한다.)

환불 승인/상태변경 기능은 없다 (v12에서 확정, 조회만 제공).

시간 표시는 tools.py의 _format_order_time과 같은 방식(UTC → KST 변환)을
쓰되, tools.py는 Agent 전용 모듈이라 직접 import하지 않고 이 파일에
동일한 패턴으로 별도 구현한다.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas import (
    AdminOrderListResponse,
    AdminOrderResponse,
    AdminRefundListResponse,
    AdminRefundResponse,
    AdminTicketListResponse,
    AdminTicketResponse,
    AdminTicketStatusUpdateRequest,
)
from database.db import get_db
from repositories.order_repository import OrderRepository
from repositories.product_repository import ProductRepository
from repositories.refund_repository import RefundRepository
from repositories.support_ticket_repository import SupportTicketRepository
from repositories.user_repository import UserRepository
from services.order_service import OrderService
from services.product_service import ProductService
from services.refund_service import RefundService
from services.support_ticket_service import (
    InvalidSupportTicketStatusError,
    SupportTicketNotFoundError,
    SupportTicketService,
)

router = APIRouter(prefix="/admin")

KST_OFFSET = timedelta(hours=9)


def _format_kst(dt: datetime | None) -> str:
    """DB에 UTC로 저장된 시각을 KST 문자열로 변환한다."""
    if dt is None:
        return "-"
    return (dt + KST_OFFSET).strftime("%Y-%m-%d %H:%M")


def _build_admin_services(db: Session) -> tuple[OrderService, RefundService, SupportTicketService]:
    """관리자 기능에 필요한 Service만 조립한다 (RagService/Tool/그래프 제외)."""
    product_repository = ProductRepository(db)
    order_repository = OrderRepository(db)
    refund_repository = RefundRepository(db)
    support_ticket_repository = SupportTicketRepository(db)
    user_repository = UserRepository(db)

    product_service = ProductService(product_repository)
    order_service = OrderService(db, order_repository, product_service)
    refund_service = RefundService(refund_repository, order_service, db)
    support_ticket_service = SupportTicketService(support_ticket_repository, user_repository, db)

    return order_service, refund_service, support_ticket_service


@router.get("/tickets", response_model=AdminTicketListResponse)
def get_tickets(db: Session = Depends(get_db)) -> AdminTicketListResponse:
    """전체 지원 문의 목록을 조회한다."""
    _, _, support_ticket_service = _build_admin_services(db)
    tickets = support_ticket_service.get_all_tickets()

    return AdminTicketListResponse(
        tickets=[
            AdminTicketResponse(
                id=t.id,
                user_id=t.user_id,
                question=t.question,
                reason=t.reason,
                status=t.status,
                created_at=_format_kst(t.created_at),
            )
            for t in tickets
        ]
    )


@router.patch("/tickets/{ticket_id}/status", response_model=AdminTicketResponse)
def update_ticket_status(
    ticket_id: int,
    request: AdminTicketStatusUpdateRequest,
    db: Session = Depends(get_db),
) -> AdminTicketResponse:
    """지원 문의의 처리 상태를 변경한다."""
    _, _, support_ticket_service = _build_admin_services(db)

    try:
        ticket = support_ticket_service.update_ticket_status(ticket_id, request.status)
    except SupportTicketNotFoundError:
        raise HTTPException(status_code=404, detail="문의를 찾을 수 없습니다.")
    except InvalidSupportTicketStatusError:
        raise HTTPException(status_code=400, detail="허용되지 않은 상태값입니다.")

    return AdminTicketResponse(
        id=ticket.id,
        user_id=ticket.user_id,
        question=ticket.question,
        reason=ticket.reason,
        status=ticket.status,
        created_at=_format_kst(ticket.created_at),
    )


@router.get("/orders", response_model=AdminOrderListResponse)
def get_orders(db: Session = Depends(get_db)) -> AdminOrderListResponse:
    """전체 주문 목록을 조회한다."""
    order_service, _, _ = _build_admin_services(db)
    orders = order_service.get_all_orders()

    data = []
    for o in orders:
        item_names = [item.product.name for item in o.order_items]
        item_summary = (
            f"{item_names[0]} 외 {len(item_names) - 1}건" if len(item_names) > 1
            else (item_names[0] if item_names else "-")
        )
        data.append(
            AdminOrderResponse(
                order_number=o.order_number,
                user_id=o.user_id,
                status=o.status,
                total_amount=o.total_amount,
                item_summary=item_summary,
                created_at=_format_kst(o.created_at),
            )
        )

    return AdminOrderListResponse(orders=data)


@router.get("/refunds", response_model=AdminRefundListResponse)
def get_refunds(db: Session = Depends(get_db)) -> AdminRefundListResponse:
    """전체 환불 요청 목록을 조회한다."""
    _, refund_service, _ = _build_admin_services(db)
    refunds = refund_service.get_all_refunds()

    return AdminRefundListResponse(
        refunds=[
            AdminRefundResponse(
                order_number=r.order.order_number,
                user_id=r.user_id,
                reason=r.reason,
                status=r.status,
                created_at=_format_kst(r.created_at),
            )
            for r in refunds
        ]
    )