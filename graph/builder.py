# graph/builder.py

"""
builder.py 역할
state.py(설계도)와 nodes.py(정거장 2개)를 실제로 실행 가능한 그래프로 배선한다.

- Tool Calling용 Gemini(①번)를 여기서 새로 만든다. infrastructure/llm_client.py의
  GeminiClient(②번, RagService 전용, Tool Calling 미지원)와는 완전히 별개 인스턴스다.
  (문서 4-4에서 이미 확정된 설계 — LangChain 방식으로 별도 생성 후 bind_tools())
- 배선: START → agent → (tool_calls 있나?) → 있으면 tools, 없으면 END
        tools → agent  (다시 돌아옴, 반복)
- 조건부 판단은 직접 안 짜고 LangGraph 내장 tools_condition을 그대로 쓴다.
  tools_condition은 기본적으로 "tools"/END 중 하나를 반환하므로, Tool Node의
  이름을 정확히 "tools"로 지어야 별도 매핑 없이 자동으로 맞물린다.
- 전달받은 checkpointer를 그래프에 연결해 thread_id별 State를 저장하고,
  다음 요청에서 기존 대화를 이어갈 수 있게 한다.

이 파일이 하지 않는 일:
- Repository/Service 조립 (agent_service.py 담당, 이 파일은 완성된 tools
  리스트만 받는다 — "그래프 배선"과 "Service 조립"의 책임을 분리하기 위함)
- checkpointer 생성과 SQLite 연결 관리
  (애플리케이션에서 한 번 생성해 재사용하고 agent_service.py가 전달)
- thread_id 생성과 전달
  (agent_service.py가 graph.invoke() 호출 시 config로 전달)
- Tool 실패/성공 판단 (그래프는 tool_calls 유무만 기계적으로 봄, 6장 원칙 그대로.
  Tool이 항상 예외 없이 dict를 반환하도록 이미 만들어뒀으므로 에러 전용 분기 불필요)
- 반복 횟수 제한 (recursion_limit은 graph.invoke() 호출 시점의 설정,
  agent_service.py에서 다룰 사항)
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import tools_condition

from graph.nodes import create_agent_node, create_tool_node
from graph.state import AgentState
from rag_config import GEMINI_API_KEY, LLM_MODEL, LLM_TEMPERATURE


def create_graph(tools: list, checkpointer):
    """Tool 리스트와 checkpointer를 받아, State 저장 기능이 연결된 실행 가능한 그래프를 반환한다."""
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, api_key=GEMINI_API_KEY, temperature=LLM_TEMPERATURE)
    llm_with_tools = llm.bind_tools(tools)

    agent_node = create_agent_node(llm_with_tools)
    tool_node = create_tool_node(tools)

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges("agent", tools_condition)
    graph_builder.add_edge("tools", "agent")

    return graph_builder.compile(checkpointer=checkpointer)