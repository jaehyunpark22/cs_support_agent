# graph/nodes.py

"""
nodes.py 역할
그래프의 정거장(Node) 2개를 정의한다: Agent Node, Tool Node.

Agent Node → Gemini(①번, Tool Calling용)를 호출해 응답을 받는다.
             호출마다 state["messages"] 전체를 통째로 보내고,
             새로 생긴 응답 하나만 {"messages": [response]} 형태로 반환한다
             (state 전체를 직접 수정하지 않음 — reducer가 병합을 담당).

Tool Node   → tool_calls를 순서대로 하나씩 실행하는 자체 구현을 사용한다.
             LangGraph 내장 ToolNode는 AIMessage 하나에 tool_calls가 여러 개
             있으면 스레드풀로 동시에 실행하는데, 우리 Tool 7개는 전부
             agent_service.py가 만든 같은 SQLAlchemy db(Session)를 공유해서
             동시 접근 시 "concurrent operations are not permitted" 에러가
             실제로 재현됐다. 그래서 병렬 대신 순차 실행으로 직접 구현한다.
             우리 Tool 7개는 전부 자기 안에서 예외를 이미 처리해 항상 dict를
             반환하므로(save_support_ticket은 이름 없는 예외까지), 이 Node에서
             별도 예외 처리는 하지 않는다.

이 파일이 하지 않는 일:
- 다음 Node를 뭘로 갈지 판단 (조건부 엣지, builder.py 담당)
- Tool 실제 실행 로직 자체 (각 Tool 함수 내부, tools.py 담당)
- 시스템 프롬프트 내용 채우기 (agent_service.py가 SystemMessage로 미리 넣어둠)

Gemini 호출(llm_with_tools.invoke) 자체가 실패하는 경우는 여기서 안 잡는다.
Tool과 달리 Agent Node가 죽으면 대화를 이어갈 주체 자체가 없어서
"부드럽게 감싸는" 이점이 없기 때문 — agent_service.py의 전역 안전망에 맡긴다.

user_id별로 매번 새로 만들어지는 llm_with_tools(tools.py의 create_tools()와
같은 이유)를 받기 위해, tools.py와 동일한 클로저/팩토리 패턴을 쓴다.
"""

import json

from langchain_core.messages import ToolMessage

from graph.state import AgentState


def create_agent_node(llm_with_tools):
    """요청마다 조립된 llm_with_tools(Tool 7개가 bind_tools된 모델)를 받아 Agent Node를 만든다."""

    def agent_node(state: AgentState) -> dict:
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    return agent_node


def create_tool_node(tools: list):
    """
    create_tools()가 반환한 Tool 7개 리스트를 받아, tool_calls를 순서대로
    하나씩 실행하는 Tool Node를 만든다 (내장 ToolNode의 병렬 실행 대신).
    """
    tools_by_name = {tool.name: tool for tool in tools}

    def tool_node(state: AgentState) -> dict:
        last_message = state["messages"][-1]
        results = []

        for tool_call in last_message.tool_calls:
            tool = tools_by_name[tool_call["name"]]
            output = tool.invoke(tool_call["args"])
            content = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
            results.append(
                ToolMessage(content=content, tool_call_id=tool_call["id"], name=tool_call["name"])
            )

        return {"messages": results}

    return tool_node

# # graph/nodes.py

# """
# nodes.py 역할
# 그래프의 정거장(Node) 2개를 정의한다: Agent Node, Tool Node.

# Agent Node → Gemini(①번, Tool Calling용)를 호출해 응답을 받는다.
#              호출마다 state["messages"] 전체를 통째로 보내고,
#              새로 생긴 응답 하나만 {"messages": [response]} 형태로 반환한다
#              (state 전체를 직접 수정하지 않음 — reducer가 병합을 담당).

# Tool Node   → LangGraph 내장 ToolNode를 그대로 사용한다. 우리 Tool 7개는
#              전부 자기 안에서 예외를 이미 처리해 항상 dict를 반환하므로
#              (save_support_ticket은 이름 없는 예외까지), ToolNode의
#              기본 예외 처리 동작에 기댈 일이 없어 커스터마이징 불필요.

# 이 파일이 하지 않는 일:
# - 다음 Node를 뭘로 갈지 판단 (조건부 엣지, builder.py 담당)
# - Tool 실제 실행 (ToolNode가 담당, 우리가 로직을 새로 안 짬)
# - 시스템 프롬프트 내용 채우기 (agent_service.py가 SystemMessage로 미리 넣어둠)

# Gemini 호출(llm_with_tools.invoke) 자체가 실패하는 경우는 여기서 안 잡는다.
# Tool과 달리 Agent Node가 죽으면 대화를 이어갈 주체 자체가 없어서
# "부드럽게 감싸는" 이점이 없기 때문 — agent_service.py의 전역 안전망에 맡긴다.

# user_id별로 매번 새로 만들어지는 llm_with_tools(tools.py의 create_tools()와
# 같은 이유)를 받기 위해, tools.py와 동일한 클로저/팩토리 패턴을 쓴다.
# """

# from langgraph.prebuilt import ToolNode

# from graph.state import AgentState


# def create_agent_node(llm_with_tools):
#     """요청마다 조립된 llm_with_tools(Tool 7개가 bind_tools된 모델)를 받아 Agent Node를 만든다."""

#     def agent_node(state: AgentState) -> dict:
#         response = llm_with_tools.invoke(state["messages"])
#         return {"messages": [response]}

#     return agent_node


# def create_tool_node(tools: list) -> ToolNode:
#     """create_tools()가 반환한 Tool 7개 리스트를 받아 LangGraph 내장 ToolNode를 만든다."""
#     return ToolNode(tools)