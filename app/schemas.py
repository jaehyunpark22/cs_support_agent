# app/schemas.py

"""
schemas.py 역할
FastAPI 라우터가 사용할 요청/응답 Pydantic 모델을 정의한다.
클라이언트와 주고받는 데이터의 모양을 검증하고 직렬화하는 것이 이 파일의 책임이다.

이 파일이 하지 않는 일:
- 업무 규칙 판단 (Service 담당)
- DB 접근 (Repository 담당)
- 실제 요청 처리 로직 (각 router 담당)

빈 입력(공백 포함) 검증은 여기서 하지 않고 agent_service.py에 맡긴다.
Pydantic의 min_length는 공백 문자열("   ")까지는 걸러내지 못해 판단 기준이
두 곳에 나뉘게 되므로, "무엇을 빈 입력으로 볼지"는 agent_service.py
한 곳에서만 판단하도록 의도적으로 남겨둔 것이다.

user_id도 1~5 범위 제약을 걸지 않았다. 현재는 UI에서 고객 1~5만 선택
가능하게 제한하고 있어 실질적으로 문제없고, 범위 제약이 실제로 필요한지는
UI 구현 시점에 판단해도 늦지 않다.

관리자용(admin) 스키마는 SupportTicketService에 상태 변경 메서드가
추가된 뒤 admin_router.py와 함께 작성했다.
"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """고객이 챗봇에 보내는 요청."""

    user_id: int
    message: str


class ChatResponse(BaseModel):
    """챗봇이 고객에게 돌려주는 응답."""

    reply: str


class HistoryMessage(BaseModel):
    """대화 기록 한 줄 (고객 발화 또는 챗봇 답변)."""

    role: str
    text: str


class HistoryResponse(BaseModel):
    """고객의 지금까지 대화 기록."""

    messages: list[HistoryMessage]


class AdminTicketResponse(BaseModel):
    """관리자 화면에 보여줄 지원 문의 1건."""

    id: int
    user_id: int
    question: str
    reason: str
    status: str
    created_at: str


class AdminTicketListResponse(BaseModel):
    """관리자 화면의 전체 지원 문의 목록."""

    tickets: list[AdminTicketResponse]


class AdminTicketStatusUpdateRequest(BaseModel):
    """관리자가 지원 문의 상태를 변경할 때 보내는 요청."""

    status: str


class AdminOrderResponse(BaseModel):
    """관리자 화면에 보여줄 주문 1건."""

    order_number: str
    user_id: int
    status: str
    total_amount: int
    item_summary: str
    created_at: str


class AdminOrderListResponse(BaseModel):
    """관리자 화면의 전체 주문 목록."""

    orders: list[AdminOrderResponse]


class AdminRefundResponse(BaseModel):
    """관리자 화면에 보여줄 환불 요청 1건."""

    order_number: str
    user_id: int
    reason: str
    status: str
    created_at: str


class AdminRefundListResponse(BaseModel):
    """관리자 화면의 전체 환불 요청 목록."""

    refunds: list[AdminRefundResponse]