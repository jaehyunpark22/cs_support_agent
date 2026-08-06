# app/routers/chat_router.py

"""
chat_router.py 역할
고객이 챗봇에게 메시지를 보내는 HTTP 엔드포인트를 제공한다.
요청을 받아 검증하고, agent_service.send_message()를 호출한 뒤,
그 결과를 응답 형태로 감싸서 돌려주는 것이 이 파일의 책임이다.

이 파일이 하지 않는 일:
- 업무 규칙 판단 (Service 담당)
- DB 세션 생성/종료 (get_db가 담당, 여기서는 Depends로 받기만 함)
- Repository/Service 조립 (agent_service.py 담당)
- LangGraph Agent 실행 (agent_service.py 담당)

DB 세션은 요청마다 FastAPI가 get_db()를 통해 새로 만들어 넘겨준다.
이 세션을 그대로 agent_service.send_message()에 전달하기만 하고,
직접 쿼리를 실행하지 않는다.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.agent_service import get_history, send_message
from app.schemas import ChatRequest, ChatResponse, HistoryResponse
from database.db import get_db

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """고객 메시지 하나를 받아 Agent 응답을 돌려준다."""
    reply = send_message(db, request.user_id, request.message)
    return ChatResponse(reply=reply)


@router.get("/chat/history", response_model=HistoryResponse)
def history(user_id: int, db: Session = Depends(get_db)) -> HistoryResponse:
    """고객의 지금까지 대화 기록을 돌려준다."""
    messages = get_history(db, user_id)
    return HistoryResponse(messages=messages)