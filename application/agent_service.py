# application/agent_service.py

"""
agent_service.py 역할
Repository/Service/RagService/Tool을 조립하고, 그 결과로 만들어진 LangGraph
Agent를 통해 두 가지 기능을 제공한다:
- send_message(): 고객 메시지 하나를 실제로 처리해서 최종 답변 문자열을 돌려준다.
- get_history(): 해당 고객의 지금까지 대화 기록을 조회한다 (Agent를 실행하지 않음).

- 그래프(create_graph의 결과)는 요청마다 새로 만든다. create_tools()가 user_id를
  클로저로 고정하는 구조라, 요청마다 그 user_id 전용 tools를 새로 만들어야 하고
  그래프도 같이 새로 만들어진다 (배선도 자체는 가벼운 객체라 매번 새로 만들어도 무방).
  이 조립 과정은 send_message()와 get_history() 양쪽에서 동일하게 필요하므로
  _build_graph()로 분리해 공유한다.
- checkpointer(SqliteSaver)는 이 파일이 로드될 때 딱 한 번만 만들어서 전역으로
  재사용한다. 매 요청마다 그래프를 새로 만들어도 이미 열려있는 checkpointer를
  compile() 인자로 넘겨주기만 하면 되므로, 대화 기록은 정상적으로 이어진다.
  대화 기록용 SQLite 파일(checkpoints.db)은 업무 데이터(app.db)와 분리했다.
- 대화방은 고객당 하나이므로 thread_id는 f"customer-{user_id}"로 고정한다.

Repository/Service 조립 순서 (임의 변경 금지):
    product_repository → order_repository → refund_repository → support_ticket_repository → user_repository
    → product_service (product_repository만 받음)
    → order_service (db, order_repository, product_service — product_service 의존)
    → refund_service (refund_repository, order_service, db — order_service 의존)
    → support_ticket_service (support_ticket_repository, user_repository, db)
RagService는 별개 계열: GeminiClient(), VectorStore() 둘 다 인자 없이 생성 →
    RagService(llm_client, vector_store)

이 파일이 하지 않는 일:
- HTTP 요청/응답 처리 (app/routers/chat_router.py 담당)
- 업무 규칙 판단 (Service/Tool이 이미 다 함)
- 그래프 배선 (graph/builder.py 담당)
- Tool 정의 (graph/tools.py 담당)

입력 검증과 시스템 오류 안전망은 서로 다른 계층이라 분리했다:
- 메시지가 빈 값/문자열이 아님 → "잘못된 사용자 입력"이라 try 블록 진입 전에
  걸러내고 즉시 안내 문구를 리턴한다. Gemini 호출까지 갈 필요가 없는 케이스다.
- 그 외 Gemini 호출 실패, DB 오류 등 예상 못한 시스템 오류는 try/except로 감싸서
  사과 문구 문자열로 변환해 리턴한다 (Tool 레벨 안전망과는 별개 계층).
send_message()는 두 경우 모두 예외를 밖으로 던지지 않고 항상 문자열을 리턴한다.

SystemMessage(SYSTEM_PROMPT)는 해당 thread_id의 첫 메시지일 때만 넣는다. 매번
넣으면 대화가 이어질수록 계속 쌓이기 때문 — graph.get_state()로 기존 기록 유무를
먼저 확인한다.

get_history()는 graph.get_state()로 저장된 State만 읽고 invoke()는 호출하지
않으므로 Gemini API를 호출하지 않는다 (quota를 소모하지 않음). SystemMessage,
ToolMessage, 그리고 Tool 호출만 하고 텍스트가 없는 중간 AIMessage는 화면에 보여줄
대상이 아니므로 제외하고, 고객 메시지와 챗봇의 최종 답변 텍스트만 남긴다.
실패 시 예외를 던지지 않고 빈 리스트를 반환한다 (기록을 못 불러와도 새 대화
시작 자체는 막지 않기 위함 — chat_router.py의 GET /chat/history 참고).

마지막 리턴 값은 .content가 아니라 .text를 쓴다. Gemini 3 계열 모델은
AIMessage.content가 문자열이 아니라 사고 서명(thought signature)을 담은
콘텐츠 블록 리스트로 나오기 때문 — .text는 어떤 형태든 순수 텍스트만
안전하게 뽑아준다.
"""

import sqlite3

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from sqlalchemy.orm import Session

from application.rag_service import RagService
from graph.builder import create_graph
from graph.tools import create_tools
from infrastructure.llm_client import GeminiClient
from infrastructure.vector_store import VectorStore
from prompts.agent_prompt import SYSTEM_PROMPT
from repositories.order_repository import OrderRepository
from repositories.product_repository import ProductRepository
from repositories.refund_repository import RefundRepository
from repositories.support_ticket_repository import SupportTicketRepository
from repositories.user_repository import UserRepository
from services.order_service import OrderService
from services.product_service import ProductService
from services.refund_service import RefundService
from services.support_ticket_service import SupportTicketService


RECURSION_LIMIT = 15


_checkpoint_conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(_checkpoint_conn)


def close_checkpoint() -> None:
    """서버 종료 시 checkpoint DB 커넥션을 닫는다. app/main.py의 lifespan에서 호출한다."""
    _checkpoint_conn.close()


def _build_graph(db: Session, user_id: int):
    """
    Repository/Service/RagService/Tool을 조립해 요청 전용 그래프를 만든다.
    send_message()와 get_history() 양쪽이 이 함수를 공유해서, 조립 로직이
    두 곳에 중복되지 않도록 한다.
    """
    product_repository = ProductRepository(db)
    order_repository = OrderRepository(db)
    refund_repository = RefundRepository(db)
    support_ticket_repository = SupportTicketRepository(db)
    user_repository = UserRepository(db)

    product_service = ProductService(product_repository)
    order_service = OrderService(db, order_repository, product_service)
    refund_service = RefundService(refund_repository, order_service, db)
    support_ticket_service = SupportTicketService(support_ticket_repository, user_repository, db)

    llm_client = GeminiClient()
    vector_store = VectorStore()
    rag_service = RagService(llm_client, vector_store)

    tools = create_tools(
        user_id=user_id,
        product_service=product_service,
        order_service=order_service,
        refund_service=refund_service,
        support_ticket_service=support_ticket_service,
        rag_service=rag_service,
    )
    return create_graph(tools, checkpointer=checkpointer)


def send_message(db: Session, user_id: int, message: str) -> str:
    """고객(user_id)이 보낸 메시지 하나를 처리해서 최종 답변 문자열을 돌려준다."""
    if not isinstance(message, str) or not message.strip():
        return "메시지를 입력해주세요."

    try:
        graph = _build_graph(db, user_id)
        config = {
            "configurable": {"thread_id": f"customer-{user_id}"},
            "recursion_limit": RECURSION_LIMIT,
        }

        existing_state = graph.get_state(config)
        input_messages = [HumanMessage(content=message)]
        if not existing_state.values.get("messages"):
            input_messages = [SystemMessage(content=SYSTEM_PROMPT)] + input_messages

        result = graph.invoke({"messages": input_messages, "user_id": user_id}, config=config)

        for m in result["messages"]:  # !!!!!!!!!디버깅 코드!!!!!!!!!        
          print("[DEBUG]", type(m).__name__, getattr(m, "tool_calls", None), str(m.content)[:100])

        return result["messages"][-1].text

    except Exception as e:
        print(f"[ERROR] agent_service.send_message 오류: {type(e).__name__}: {e}")
        return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."


def get_history(db: Session, user_id: int) -> list[dict]:
    """
    해당 고객의 지금까지 대화 기록을 조회한다. Agent를 실행하지 않고
    체크포인터에 저장된 State만 읽는다.
    """
    try:
        graph = _build_graph(db, user_id)
        config = {"configurable": {"thread_id": f"customer-{user_id}"}}
        state = graph.get_state(config)
        messages = state.values.get("messages", [])
    except Exception as e:
        print(f"[ERROR] agent_service.get_history 오류: {type(e).__name__}: {e}")
        return []

    history = []
    for m in messages:
        if isinstance(m, HumanMessage):
            history.append({"role": "customer", "text": m.content})
        elif isinstance(m, AIMessage) and m.text.strip():
            history.append({"role": "bot", "text": m.text})
    return history