# Service 레이어 예외 설계

[← README로 돌아가기](../README.md)

Service 4개가 정의한 예외는 전부 **업무 규칙 위반**을 나타냅니다. 각 예외가 어느
메서드에서 발생하고, 어느 Tool이 이를 잡아 고객에게 어떤 문구로 안내하는지까지
함께 정리했습니다.

인프라 장애(API 호출 실패 등)를 나타내는 `infrastructure/llm_client.py`의 예외들은
성격이 달라 이 문서에서는 다루지 않습니다.

---

## product_service.py

```
ProductServiceError (기반 클래스)
 │
 ├─ ProductSearchConditionRequiredError
 │    발생 위치: search_products() — 키워드도, 가격 조건도 하나도 없을 때
 │    처리 Tool: search_products
 │    안내 문구: "찾으시는 상품의 종류나 색상, 가격대를 알려주시겠어요?"
 │
 ├─ ProductPriceTypeError
 │    발생 위치: search_products() — 가격 조건이 int가 아닐 때
 │    처리 Tool: search_products
 │    안내 문구: "가격 조건을 다시 확인해주세요."
 │
 ├─ ProductPriceInvalidError
 │    발생 위치: search_products() — 가격 조건이 1원 미만일 때
 │    처리 Tool: search_products
 │    안내 문구: "가격 조건을 다시 확인해주세요." (위와 동일 문구로 처리)
 │
 ├─ ProductPriceRangeError
 │    발생 위치: search_products() — 최소 가격이 최대 가격보다 클 때
 │    처리 Tool: search_products
 │    안내 문구: "최소 가격이 최대 가격보다 클 수 없어요. 다시 확인해주시겠어요?"
 │
 ├─ ProductIdRequiredError
 │    발생 위치: get_active_product() — product_id가 None일 때
 │    처리 Tool: preview_order, create_order (product_service를 경유해 전파됨)
 │    안내 문구: "주문하실 상품을 다시 한번 알려주시겠어요?"
 │
 ├─ ProductIdTypeError
 │    발생 위치: get_active_product() — product_id가 int가 아닐 때
 │                (bool도 명시적으로 제외: isinstance(product_id, bool) 체크)
 │    처리 Tool: preview_order, create_order
 │    안내 문구: "주문하실 상품을 다시 한번 알려주시겠어요?" (위와 동일)
 │
 └─ ProductNotFoundError
      발생 위치: get_active_product() — 상품이 없거나 비활성 상태일 때 (구분하지 않음)
      처리 Tool: preview_order, create_order
      안내 문구: "죄송해요, 해당 상품은 현재 주문하실 수 없어요."
```

---

## order_service.py

```
OrderServiceError (기반 클래스)
 │
 ├─ OrderNumberRequiredError
 │    발생 위치: get_customer_order() — 주문번호가 없거나 빈 문자열일 때
 │    처리 Tool: get_orders, request_refund (order_service를 경유해 전파됨)
 │    안내 문구: "주문번호를 다시 한번 확인해주시겠어요?"
 │
 ├─ OrderNumberTypeError
 │    발생 위치: get_customer_order() — 주문번호가 문자열이 아닐 때
 │    처리 Tool: get_orders, request_refund
 │    안내 문구: "주문번호를 다시 한번 확인해주시겠어요?" (위와 동일)
 │
 ├─ OrderNotFoundError
 │    발생 위치: get_customer_order() — 해당 user_id 소유의 주문이 없을 때
 │                (존재하지 않는 경우와 다른 고객 소유인 경우를 구분하지 않음)
 │    처리 Tool: get_orders, request_refund
 │    안내 문구: "주문을 확인할 수 없어요. 주문번호를 다시 한번 확인해주시겠어요?"
 │
 ├─ OrderQuantityRequiredError
 │    발생 위치: _validate_quantity() — 수량이 None일 때
 │    처리 Tool: preview_order, create_order
 │    안내 문구: "몇 개 주문하실지 다시 한번 알려주시겠어요?"
 │
 ├─ OrderQuantityTypeError
 │    발생 위치: _validate_quantity() — 수량이 int가 아닐 때 (bool도 제외)
 │    처리 Tool: preview_order, create_order
 │    안내 문구: "몇 개 주문하실지 다시 한번 알려주시겠어요?" (위와 동일)
 │
 └─ OrderQuantityInvalidError
      발생 위치: _validate_quantity() — 수량이 1개 미만일 때
      처리 Tool: preview_order, create_order
      안내 문구: "몇 개 주문하실지 다시 한번 알려주시겠어요?" (위와 동일)
```

`preview_order`, `create_order` Tool은 이 예외들 외에 `ProductIdRequiredError`,
`ProductIdTypeError`, `ProductNotFoundError`도 함께 잡습니다. `OrderService`가
내부에서 `product_service.get_active_product()`를 호출하기 때문입니다.

---

## refund_service.py

```
RefundServiceError (기반 클래스)
 │
 ├─ RefundReasonRequiredError
 │    발생 위치: request_refund() — 환불 사유가 없거나 빈 문자열일 때
 │    처리 Tool: request_refund
 │    안내 문구: "환불 사유를 알려주시겠어요?"
 │
 ├─ RefundNotAllowedError
 │    발생 위치: request_refund() — 주문 상태가 preparing/shipped/delivered가
 │                아닐 때 (예: 이미 cancelled, refunded인 주문)
 │    처리 Tool: request_refund
 │    안내 문구: "죄송해요, 이 주문은 현재 상태에서는 환불이 어려워요."
 │
 └─ DuplicateRefundRequestError
      발생 위치: request_refund() — 같은 주문에 이미 pending 환불 요청이 있을 때
      처리 Tool: request_refund
      안내 문구: "이미 처리 중인 환불 요청이 있어요."
```

`request_refund` Tool은 이 3종 외에 `OrderNumberRequiredError`,
`OrderNumberTypeError`, `OrderNotFoundError`도 함께 잡습니다. `RefundService`가
내부에서 `order_service.get_customer_order()`를 호출해 주문 소유권을 확인하기
때문입니다.

---

## support_ticket_service.py

```
SupportTicketServiceError (기반 클래스)
 │
 ├─ SupportTicketQuestionRequiredError
 │    발생 위치: create_ticket() — 질문 내용이 없거나 빈 문자열일 때
 │    처리 Tool: save_support_ticket
 │    안내 문구: "어떤 점이 궁금하신지 알려주시겠어요?"
 │
 ├─ InvalidSupportTicketReasonError
 │    발생 위치: create_ticket() — reason이 허용된 4개 값
 │                (지원하지 않는 업무 / 정책 문서에 관련 내용 없음 /
 │                필요한 Tool이 없음 / 사람의 확인이 필요함) 중 하나가 아닐 때
 │    처리 Tool: save_support_ticket
 │    안내 문구: "문의 접수 중 문제가 발생했어요."
 │
 └─ SupportTicketUserNotFoundError
      발생 위치: create_ticket() — user_repository로 조회한 고객이 없을 때
      처리 Tool: save_support_ticket
      안내 문구: "고객 정보를 확인할 수 없어요."
```

`save_support_ticket` Tool은 이 3종 예외 외에도 **이름 없는 모든 시스템 예외
(`Exception`)까지 별도로 잡습니다.** 다른 Tool이 전부 실패했을 때 마지막으로
호출되는 안전망이기 때문에, 여기서만 예외적으로 포괄적인 예외 처리를 둡니다.

```
except Exception:
    안내 문구: "죄송해요, 일시적인 오류가 발생했어요. 잠시 후 다시 시도해주세요."
```

---

## admin_router.py (Tool을 거치지 않는 예외 처리)

관리자 기능은 Agent/Graph/Tool을 거치지 않고 admin_router.py가 Service를
직접 호출합니다. 그래서 아래 2개 예외는 Tool이 아니라 **admin_router.py가
직접 잡아 HTTP 상태 코드로 변환**합니다. 위의 다른 예외들과 처리 위치가
다르다는 점에서 구별됩니다.

```
SupportTicketNotFoundError
  발생 위치: update_ticket_status() — 존재하지 않는 ticket_id로 상태를
              변경하려 할 때
  처리 위치: admin_router.py의 update_ticket_status() (Tool 아님)
  응답: HTTP 404, "문의를 찾을 수 없습니다."

InvalidSupportTicketStatusError
  발생 위치: update_ticket_status() — status가 open / in_progress / resolved
              중 하나가 아닐 때
  처리 위치: admin_router.py의 update_ticket_status() (Tool 아님)
  응답: HTTP 400, "허용되지 않은 상태값입니다."
```

---

## 설계 노트

**Service 간 의존이 예외 전파로 그대로 드러납니다.** `OrderService`가
`ProductService`를 의존하기 때문에 `preview_order`/`create_order`가
`Product*` 계열 예외를 그대로 던질 수 있고, `RefundService`가 `OrderService`를
의존하기 때문에 `request_refund`가 `Order*` 계열 예외를 그대로 던질 수 있습니다.
각 Service는 이런 예외를 감싸지 않고 그대로 전파시키며, 예외를 실제로
`{success, code, message, data}` 형태로 변환하는 책임은 전부 Tool 계층에
있습니다.

**"없음"과 "권한 없음"을 구분하지 않는 패턴이 반복됩니다.** `OrderNotFoundError`
(존재하지 않음 vs 다른 고객 소유), `ProductNotFoundError`(존재하지 않음 vs
판매중지)는 둘 다 원인을 구분해서 알려주지 않습니다. 다른 고객의 주문 존재
여부 같은 정보가 노출되지 않도록 하기 위한 의도적인 설계입니다.

**관리자 기능만 예외 처리 위치가 다릅니다.** 나머지 예외는 전부 Tool 계층에서
`{success, code, message, data}` 형태로 변환되지만, admin_router.py의 2개
예외는 Tool을 거치지 않고 라우터가 직접 `HTTPException`으로 변환합니다.
관리자 기능이 Agent/Tool을 거치지 않는다는 설계와 일관된 결과입니다.

---

## 더 알아보기

- [← README로 돌아가기](../README.md)
- [아키텍처와 Agent 동작 원리](ARCHITECTURE.md) — 설계 원칙, LLM 구성, Tool 구성, 요청 처리 흐름, 대화 상태 관리
- [기술적 문제와 해결 과정](TROUBLESHOOTING.md) — 개발 중 만난 문제 7가지와 해결 방법
- [프로젝트 회고](RETROSPECTIVE.md) — 설계하며 배운 것들