# repositories/refund_repository.py

"""
refund_repository.py 역할
refund_requests 테이블에 대한 DB 조회와 저장만 전담한다.
동일 주문에 pending 상태의 환불 요청이 있는지 조회하여
Service가 중복 환불 요청 여부를 판단할 수 있도록 한다.
환불 가능한 주문 상태인지, 주문 소유권이 확인됐는지,
환불 사유가 유효한지 등의 업무 규칙은 RefundService에서 처리한다.
커밋 시점은 이 파일이 아니라 Service가 관리한다.
"""

from sqlalchemy.orm import Session

from database.models import RefundRequest


class RefundRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_pending_by_order(self, order_id: int) -> RefundRequest | None:
        """특정 주문에 pending 상태의 환불 요청이 있는지 조회한다."""
        return (
            self.db.query(RefundRequest)
            .filter(
                RefundRequest.order_id == order_id,
                RefundRequest.status == "pending",
            )
            .first()
        )

    def get_by_id(self, refund_request_id: int) -> RefundRequest | None:
        """ID로 환불 요청 1건을 조회한다."""
        return self.db.get(RefundRequest, refund_request_id)

    def save(self, refund_request: RefundRequest) -> RefundRequest:
        """
        새로운 환불 요청을 저장한다.
        commit은 하지 않는다 — 트랜잭션 확정은 Service의 책임이다.
        """
        self.db.add(refund_request)
        self.db.flush()  # id를 확보하기 위해 flush까지만
        return refund_request

    def get_by_user(self, user_id: int) -> list[RefundRequest]:
        """특정 고객의 전체 환불 요청 목록을 조회한다."""
        return (
            self.db.query(RefundRequest)
            .filter(RefundRequest.user_id == user_id)
            .order_by(RefundRequest.id)
            .all()
        )

    def get_all(self) -> list[RefundRequest]:
        """전체 환불 요청 목록을 조회한다. 관리자 화면용이다."""
        return self.db.query(RefundRequest).order_by(RefundRequest.id).all()