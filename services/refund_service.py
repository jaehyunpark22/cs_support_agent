# services/refund_service.py

"""
refund_service.py 역할
환불 요청과 관련된 업무 규칙을 처리한다.

- 환불 사유는 필수다.
- 환불 가능한 주문 상태는 preparing / shipped / delivered 뿐이다.
- 동일 주문에 이미 pending 상태의 환불 요청이 있으면 중복 접수를 막는다.
- 주문 조회(본인 확인 포함)는 OrderService를 재사용한다.

실제 DB 조회와 저장은 RefundRepository가 담당하고,
이 파일은 그 결과를 가지고 판단만 한다.
환불 요청 저장은 쓰기 작업이므로, 최종 commit/rollback은
이 Service가 직접 관리한다.
"""

from sqlalchemy.orm import Session

from database.models import RefundRequest
from repositories.refund_repository import RefundRepository
from services.order_service import OrderService

REFUNDABLE_STATUSES = {"preparing", "shipped", "delivered"}


class RefundServiceError(Exception):
    """환불 업무 처리 중 발생하는 기본 예외다."""


class RefundReasonRequiredError(RefundServiceError):
    """환불 사유가 입력되지 않았을 때 발생한다."""


class RefundNotAllowedError(RefundServiceError):
    """주문 상태가 환불 가능한 상태(preparing/shipped/delivered)가 아닐 때 발생한다."""


class DuplicateRefundRequestError(RefundServiceError):
    """동일 주문에 이미 처리 중인(pending) 환불 요청이 있을 때 발생한다."""


class RefundService:
    def __init__(
        self,
        refund_repository: RefundRepository,
        order_service: OrderService,
        db: Session,
    ):
        self.refund_repository = refund_repository
        self.order_service = order_service
        self.db = db

    def request_refund(
        self, user_id: int, order_number: str, reason: str
    ) -> RefundRequest:
        """
        환불 요청을 접수한다.

        1. 환불 사유가 비어있지 않은지
        2. 주문이 존재하고 본인 것이 맞는지 (OrderService가 처리)
        3. 주문 상태가 환불 가능한 상태인지
        4. 이미 pending 환불 요청이 있는지 (중복 차단)

        전부 통과하면 저장하고 commit한다.
        """
        if reason is None or not isinstance(reason, str):
            raise RefundReasonRequiredError()

        normalized_reason = reason.strip()
        if not normalized_reason:
            raise RefundReasonRequiredError()

        order = self.order_service.get_customer_order(
            user_id=user_id, order_number=order_number
        )

        if order.status not in REFUNDABLE_STATUSES:
            raise RefundNotAllowedError()

        existing = self.refund_repository.get_pending_by_order(order.id)
        if existing is not None:
            raise DuplicateRefundRequestError()

        refund_request = RefundRequest(
            user_id=user_id,
            order_id=order.id,
            reason=normalized_reason,
            status="pending",
        )

        try:
            saved = self.refund_repository.save(refund_request)
            self.db.commit()
            self.db.refresh(saved)
        except Exception:
            self.db.rollback()
            raise

        return saved

    def get_customer_refunds(self, user_id: int) -> list[RefundRequest]:
        """현재 고객이 소유한 전체 환불 요청 목록을 조회한다."""
        return self.refund_repository.get_by_user(user_id)

    def get_all_refunds(self) -> list[RefundRequest]:
        """전체 환불 요청 목록을 조회한다. 관리자 기능에서 사용한다."""
        return self.refund_repository.get_all()