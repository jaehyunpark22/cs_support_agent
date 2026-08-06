# graph/state.py

"""
state.py 역할
그래프 실행 중 모든 Node가 공유하는 데이터의 타입을 정의한다.

- messages: 대화 기록. MessagesState가 기본 제공하는 add_messages reducer로,
  Node가 새 메시지를 반환할 때마다 기존 리스트를 덮어쓰지 않고 뒤에 이어붙인다.
- user_id: 현재 대화 중인 고객(1~5). 값 하나라 reducer 불필요 —
  매번 최신값으로 그냥 덮어써지는 기본 동작으로 충분하다.

이 파일이 하지 않는 일:
- 실제 데이터 저장 (그래프가 실행되는 동안만 메모리에 존재, 영구 저장 아님)
- 업무 규칙 판단 (Service/Tool 담당)

"고객이 미리보기를 실제로 확인했는지" 코드로 강제하는 안전장치(예: last_preview
필드)는 넣지 않기로 확정했다(A안) — create_order 독스트링 경고 +
agent_prompt.py의 지시문에만 의존한다. Tool이 state를 아예 안 받는 지금
구조(user_id만 클로저로 주입)를 그대로 유지하기 위한 선택이다.
"""

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """messages 필드와 add_messages reducer는 MessagesState가 이미 제공한다."""

    user_id: int




# AgentState (state.py에서 정의한 "그릇"의 설계도)
#  └─ 이 그릇 안에 실제로 담기는 내용물이 바로 
#       messages: [HumanMessage(...), AIMessage(...), ToolMessage(...)]
#       user_id: 1