# 기술적 문제와 해결 과정

[← README로 돌아가기](../README.md)

---

## 1. 상품명만으로는 실제 고객의 검색 표현을 처리하기 어려운 문제

**문제**

실제 사용자는 정확한 상품명만 입력하지 않습니다.

```text
"빨간 나이키 신발"
"3만원대 운동화"
"파란색 반팔"
"5만원 이하 상품"
```

상품명만 검색하면 브랜드·색상·종류·특징·가격대를 조합한 자연어 요청을 처리하기 어렵습니다.

**해결**

상품마다 상품명·종류·브랜드·색상·특징을 포함하는 `keywords` 컬럼을 추가했습니다.

Agent가 고객의 자연어 요청을 `keywords`, `price_min`, `price_max` 형태의 검색 조건으로 변환하고, ProductService와 ProductRepository가 키워드와 가격 조건을 조합해 검색하도록 구성했습니다.

---

## 2. 자연어 가격 표현을 실제 검색 조건으로 연결하기 어려운 문제

**문제**

고객은 가격을 항상 정확한 숫자로 입력하지 않습니다.

```text
"3만원대"
"5만원 이하"
"4만원부터 7만원 사이"
```

이 표현을 그대로 Repository의 가격 조건으로 사용할 수는 없습니다.

**해결**

Agent가 자연어 가격 표현을 `price_min`과 `price_max` Tool 인자로 변환합니다.

```text
"3만원대"
→ price_min=30000
→ price_max=39999
```

ProductService는 변환된 값이 정수인지, 음수가 아닌지, 최소 가격이 최대 가격보다 크지 않은지 검증합니다.

실제 상품 필터링은 LLM이 아니라 ProductRepository의 DB 쿼리가 담당합니다.

---

## 3. 검색어가 다른 단어의 일부로 잘못 일치하는 문제

**문제**

단순한 문자열 포함 검색을 사용하면 `"블루"`를 검색했을 때 `"블루투스"`까지 검색될 수 있습니다.

**해결**

키워드를 쉼표로 구분해 저장하고, 검색 시 키워드 앞뒤의 구분자까지 함께 비교합니다.

이를 통해 다른 단어의 일부가 아니라 독립된 키워드 단위로 정확하게 검색합니다.

---

## 4. 동시에 생성되는 주문의 주문번호가 중복될 수 있는 문제

**문제**

마지막 주문번호를 조회한 뒤 1을 더하는 방식은 두 주문 요청이 동시에 들어왔을 때 같은 주문번호가 생성될 수 있습니다.

```text
요청 A: 마지막 번호 A1010 확인
요청 B: 마지막 번호 A1010 확인

요청 A: A1011 생성
요청 B: A1011 생성
```

**해결**

DB가 자동으로 생성하는 고유 `id`를 기준으로 주문번호를 만들었습니다.

Order를 먼저 임시 주문번호로 저장하고 `flush`를 통해 ID를 확보한 뒤 정식 주문번호를 생성합니다.

```text
order_number = "A" + (1000 + order.id)
```

Order와 OrderItem 저장, 주문번호 변경은 하나의 트랜잭션으로 묶고 OrderService에서 `commit` 또는 `rollback`합니다.

---

## 5. AI가 정확해야 하는 숫자를 직접 계산할 수 있는 문제

**문제**

주문 금액이나 합계처럼 정확해야 하는 값을 LLM이 직접 계산하면 실제 DB 값과 다른 응답을 생성할 위험이 있습니다.

**해결**

금액은 서버에서 계산하고 LLM은 서버가 반환한 값을 고객에게 안내만 하도록 역할을 분리했습니다.

```text
Server
단가 × 수량 계산
→ total_amount 반환

LLM
반환받은 total_amount를 고객에게 안내
```

주문 목록 합계와 주문 미리보기 금액에도 같은 원칙을 적용했습니다.

---

## 6. Python에서 `bool` 값이 정수로 처리되는 문제

**문제**

Python에서는 `bool`이 `int`의 하위 타입입니다.

```python
isinstance(True, int)  # True
```

따라서 상품 ID나 수량을 검증할 때 단순히 `int` 여부만 확인하면 `True`와 `False`가 숫자로 통과할 수 있습니다.

**해결**

상품 ID와 수량 검증에서 `bool` 값을 별도로 제외합니다.

```python
if isinstance(product_id, bool) or not isinstance(product_id, int):
    ...
```

---

## 7. 여러 Tool이 동일한 SQLAlchemy Session을 동시에 사용하는 문제

**문제**

다음처럼 하나의 메시지에서 서로 다른 검색을 동시에 요청할 수 있습니다.

```text
"6만원대 제품이랑 빨간색 제품 둘 다 보여줘"
```

LLM이 한 응답에서 여러 Tool Call을 생성하면, LangGraph 내장 Tool Node가 이를 스레드풀로 동시에 실행합니다. 이때 모든 Tool이 동일한 SQLAlchemy Session을 공유하고 있어서 다음 오류가 발생했습니다.

```text
InvalidRequestError:
This session is provisioning a new connection;
concurrent operations are not permitted
```

**원인**

동일한 SQLAlchemy Session 객체를 여러 실행 Thread가 동시에 사용했기 때문입니다.

**해결**

LangGraph 내장 Tool Node 대신, Tool Call을 하나씩 순서대로 실행하는 Tool Node를 직접 구현했습니다.

기존
```python
def create_tool_node(tools: list) -> ToolNode:
    
    return ToolNode(tools)
```
변경
```python
def create_tool_node(tools: list):
    tools_by_name = {tool.name: tool for tool in tools}

    def tool_node(state):
        results = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            output = tool.invoke(tool_call["args"])
            content = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
            results.append(
                ToolMessage(content=content, tool_call_id=tool_call["id"], name=tool_call["name"])
            )
        return {"messages": results}

    return tool_node
```

동시에 실행하는 대신 `for` 문으로 하나씩 실행하도록 바꿔서, Tool 두 개가 같은 Session을 쓰더라도 겹치는 시점이 없도록 했습니다.

디버그 로그로 동일한 시나리오(한 메시지에 서로 다른 조건의 검색 두 개)를 재현해 확인했습니다. Tool Call 2개가 포함된 AIMessage가 생성된 뒤, 두 ToolMessage가 순서대로 오류 없이 반환되는 것을 확인했습니다.

```text
[DEBUG] AIMessage [
    {'name': 'search_products', 'args': {'price_min': 40000, 'price_max': 49999}, ...},
    {'name': 'search_products', 'args': {'keywords': ['파란색'], ...}, ...}
]
[DEBUG] ToolMessage None {"success": true, ...}
[DEBUG] ToolMessage None {"success": true, ...}
```

---

## 더 알아보기

- [← README로 돌아가기](../README.md)
- [아키텍처와 Agent 동작 원리](ARCHITECTURE.md) — 설계 원칙, LLM 구성, Tool 구성, 요청 처리 흐름, 대화 상태 관리
- [Service 레이어 예외 설계](EXCEPTIONS.md) — 예외 클래스별 발생 위치, 처리 Tool, 안내 문구 매핑
- [프로젝트 회고](RETROSPECTIVE.md) — 설계하며 배운 것들