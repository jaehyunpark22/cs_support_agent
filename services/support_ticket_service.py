# services/support_ticket_service.py

"""
support_ticket_service.py 역할
Agent가 처리하지 못한 지원 문의의 업무 규칙과 트랜잭션을 처리하고,
관리자의 상태 변경 요청도 이 파일에서 함께 처리한다.

- 질문은 필수다.
- reason은 정해진 4개 값 중 하나만 허용한다.
- status는 open / in_progress / resolved 중 하나만 허용한다.
- 존재하는 고객의 문의만 저장한다.
- 새 문의의 상태는 항상 open으로 시작한다.
- 시스템 내부 오류는 지원 문의로 저장하지 않는다.
  (이는 이 Service를 호출하는 Tool이, 프로그램 예외를
  reason으로 둔갑시켜 넘기지 않아야 지켜지는 규칙이다.)

관리자의 상태 변경(update_ticket_status)은 open→in_progress→resolved
순서를 강제하지 않는다. 관리자가 실수로 바꾼 상태를 되돌리는 것까지
막을 이유는 없다고 판단해서, "허용된 3개 값 중 하나인지"만 검증한다.

실제 DB 조회와 저장은 UserRepository와 SupportTicketRepository가 담당하고,
최종 commit과 rollback은 이 Service가 관리한다.
"""

from sqlalchemy.orm import Session

from database.models import SupportTicket
from repositories.support_ticket_repository import SupportTicketRepository
from repositories.user_repository import UserRepository

ALLOWED_SUPPORT_TICKET_REASONS = {
    "지원하지 않는 업무",
    "정책 문서에 관련 내용 없음",
    "필요한 Tool이 없음",
    "사람의 확인이 필요함",
}

ALLOWED_SUPPORT_TICKET_STATUSES = {"open", "in_progress", "resolved"}


class SupportTicketServiceError(Exception):
    """지원 문의 업무 처리 중 발생하는 기본 예외다."""


class SupportTicketQuestionRequiredError(SupportTicketServiceError):
    """문의 내용이 입력되지 않았을 때 발생한다."""


class InvalidSupportTicketReasonError(SupportTicketServiceError):
    """허용되지 않은 문의 처리 사유가 전달됐을 때 발생한다."""


class SupportTicketUserNotFoundError(SupportTicketServiceError):
    """문의를 등록하려는 고객을 확인할 수 없을 때 발생한다."""


class SupportTicketNotFoundError(SupportTicketServiceError):
    """존재하지 않는 지원 문의 ID로 상태를 변경하려 할 때 발생한다."""


class InvalidSupportTicketStatusError(SupportTicketServiceError):
    """허용되지 않은 상태값으로 변경하려 할 때 발생한다."""


class SupportTicketService:
    def __init__(
        self,
        support_ticket_repository: SupportTicketRepository,
        user_repository: UserRepository,
        db: Session,
    ):
        self.support_ticket_repository = support_ticket_repository
        self.user_repository = user_repository
        self.db = db

    def create_ticket(
        self, user_id: int, question: str, reason: str
    ) -> SupportTicket:
        """업무 규칙을 확인한 뒤 새로운 지원 문의를 저장한다."""
        if question is None or not isinstance(question, str):
            raise SupportTicketQuestionRequiredError()
        if reason is None or not isinstance(reason, str):
            raise InvalidSupportTicketReasonError()

        normalized_question = question.strip()
        normalized_reason = reason.strip()

        if not normalized_question:
            raise SupportTicketQuestionRequiredError()

        if normalized_reason not in ALLOWED_SUPPORT_TICKET_REASONS:
            raise InvalidSupportTicketReasonError()

        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise SupportTicketUserNotFoundError()

        support_ticket = SupportTicket(
            user_id=user_id,
            question=normalized_question,
            reason=normalized_reason,
            status="open",
        )

        try:
            saved = self.support_ticket_repository.save(support_ticket)
            self.db.commit()
            self.db.refresh(saved)
        except Exception:
            self.db.rollback()
            raise

        return saved

    def get_customer_tickets(self, user_id: int) -> list[SupportTicket]:
        """특정 고객의 전체 지원 문의 목록을 조회한다."""
        return self.support_ticket_repository.get_by_user(user_id)

    def get_all_tickets(self) -> list[SupportTicket]:
        """전체 지원 문의 목록을 조회한다. 관리자 기능에서 사용한다."""
        return self.support_ticket_repository.get_all()

    def update_ticket_status(self, ticket_id: int, status: str) -> SupportTicket:
        """관리자가 지원 문의의 처리 상태를 변경한다."""
        if status is None or not isinstance(status, str):
            raise InvalidSupportTicketStatusError()

        normalized_status = status.strip()
        if normalized_status not in ALLOWED_SUPPORT_TICKET_STATUSES:
            raise InvalidSupportTicketStatusError()

        ticket = self.support_ticket_repository.get_by_id(ticket_id)
        if ticket is None:
            raise SupportTicketNotFoundError()

        ticket.status = normalized_status

        try:
            self.db.commit()
            self.db.refresh(ticket)
        except Exception:
            self.db.rollback()
            raise

        return ticket