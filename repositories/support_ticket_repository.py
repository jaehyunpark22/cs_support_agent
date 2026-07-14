# repositories/support_ticket_repository.py

"""
support_ticket_repository.py 역할
support_tickets 테이블에 대한 DB 조회와 저장만 전담한다.

reason이 유효한 4가지 값 중 하나인지, status 전이가 올바른지 같은
업무 규칙은 이 파일이 판단하지 않는다. 그 판단은
services/support_ticket_service.py에서 처리한다.
커밋 시점도 이 파일이 아니라 Service가 관리한다.
"""

from sqlalchemy.orm import Session

from database.models import SupportTicket


class SupportTicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, support_ticket: SupportTicket) -> SupportTicket:
        """
        새로운 지원 문의를 저장한다.
        commit은 하지 않는다 — 트랜잭션 확정은 Service의 책임이다.
        """
        self.db.add(support_ticket)
        self.db.flush()  # id를 확보하기 위해 flush까지만
        return support_ticket

    def get_by_id(self, support_ticket_id: int) -> SupportTicket | None:
        """ID로 지원 문의 1건을 조회한다."""
        return self.db.get(SupportTicket, support_ticket_id)

    def get_by_user(self, user_id: int) -> list[SupportTicket]:
        """특정 고객의 전체 지원 문의 목록을 조회한다."""
        return (
            self.db.query(SupportTicket)
            .filter(SupportTicket.user_id == user_id)
            .order_by(SupportTicket.id)
            .all()
        )

    def get_all(self) -> list[SupportTicket]:
        """전체 지원 문의 목록을 조회한다. 관리자 화면용이다."""
        return self.db.query(SupportTicket).order_by(SupportTicket.id).all()