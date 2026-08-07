# CS Support Agent

> LangGraph 기반 쇼핑몰 고객지원 에이전트 입니다.
> 고객의 자연어 요청을 분석해 적절한 Tool을 선택하고, 정책 안내부터 상품 검색·주문·환불 요청까지 처리합니다.

CS Support Agent는 정책 문서에 답변하는 단순 RAG 챗봇을 넘어, 고객의 요청에 따라 **정책 검색과 실제 업무 데이터 처리까지 수행하는 쇼핑몰 고객지원 에이전트**입니다.

LLM은 고객의 의도를 파악하고 필요한 Tool을 선택합니다. 상품 검색, 주문 금액 계산, 주문 생성, 환불 가능 여부 확인, DB 저장처럼 정확성이 필요한 작업은 서버의 Service와 Repository 계층에서 처리합니다.

지원 범위를 벗어나거나 정책 문서에서 답을 찾지 못한 문의는 단순히 거절하고 종료하지 않고, 상담원이 이후 확인할 수 있도록 문의 내역으로 저장합니다.

<!-- 대표 화면 또는 시연 GIF 추가 -->
<img width="834" height="471" alt="image" src="https://github.com/user-attachments/assets/aec97a24-db57-4c88-9b92-3d0df765da46" />

<img width="666" height="881" alt="image" src="https://github.com/user-attachments/assets/dc6da9b5-0a29-48cc-a3e6-cb08ab915674" />

<img width="961" height="763" alt="image" src="https://github.com/user-attachments/assets/fb6911d2-9276-49c4-8db6-bed86424ec5b" />

---

## 프로젝트 소개

일반적인 RAG 챗봇은 문서를 검색해 질문에 답변하는 데 집중하지만, 실제 쇼핑몰 고객지원에서는 다음과 같은 업무도 함께 처리해야 합니다.

* 배송·주문·환불 정책 안내
* 고객이 원하는 상품 검색
* 본인 주문 목록 및 상세 조회 
* 상품 주문 및 주문 전 예상 금액 확인
* 고객의 명확한 동의 후 주문 생성
* 주문 상태와 중복 요청을 확인한 환불 접수
* 자동으로 처리할 수 없는 문의 내역 저장 후 상담원 접수

이 프로젝트는 LangGraph와 LangChain Tool Calling을 이용해 고객 요청에 적합한 기능을 Agent가 직접 선택하도록 구성했습니다. LLM이 모든 업무 규칙과 계산을 담당하지 않도록 역할을 분리했습니다.

```text
LLM
├── 고객 요청과 의도 파악
├── 필요한 Tool 선택
├── 자연어를 구조화된 Tool 인자로 변환
├── Tool 실행 결과 해석
└── 최종 답변 생성

Server
├── 입력값 검증
├── 상품·주문·환불 업무 규칙 판단
├── 가격과 합계 계산
├── 고객 주문 소유권 확인
├── DB 조회 및 저장
└── 트랜잭션 관리
```

이 모든 처리가 가능하려면 실제 쇼핑몰과 동일한 수준의 데이터 구조가 먼저 필요합니다. Agent가 다룰 DB 엔티티 6개와 테이블 간 관계, 자연어 검색·동시성 안전 주문번호 생성 같은 Agent 특성에 맞춘 샘플 데이터까지 직접 설계했습니다.

```text
DB 엔티티 (6개)
├── User            # 고객 정보
├── Product         # 상품 정보 (자연어 검색용 keywords 포함)
├── Order           # 주문 정보
├── OrderItem       # 주문에 포함된 상품·수량·당시 가격
├── RefundRequest   # 주문에 대한 환불 요청
└── SupportTicket   # Agent가 처리하지 못한 문의
```

테이블 간 관계와 전체 ERD는 [아키텍처 문서 - 데이터 모델](docs/ARCHITECTURE.md#데이터-모델)에서 다룹니다.

추가로 README에 담지 못한 내용들을 정리한 마크다운 목록입니다
- [아키텍처와 Agent 동작 원리](docs/ARCHITECTURE.md) — 설계 원칙, LLM 구성, Tool 구성, 전체 ERD, 요청 처리 흐름, 대화 상태 관리
- [Service 레이어 예외 설계](docs/EXCEPTIONS.md) — 예외 클래스별 발생 위치, 처리 Tool, 안내 문구 매핑
- [기술적 문제와 해결 과정](docs/TROUBLESHOOTING.md) — 개발 중 만난 문제 7가지와 해결 방법
- [프로젝트 회고](docs/RETROSPECTIVE.md) — 설계하며 배운 것들

---

## 주요 기능

| 기능        | 설명                                                                                 |
| --------- | ---------------------------------------------------------------------------------- |
| 정책 질문 답변  | 배송·주문·환불 정책 문서를 검색해 RAG 기반으로 답변합니다. 문서에서 답을 찾지 못한 문의는 Agent가 문의 티켓으로 접수하도록 설계했습니다. |
| 자연어 상품 검색 | 상품명뿐 아니라 브랜드·색상·종류·특징·가격대 등 여러 조건을 조합해 상품을 검색합니다.                                  |
| 주문 조회     | 현재 고객의 주문만 조회할 수 있으며, 전체 목록과 주문번호를 이용한 상세 조회를 지원합니다.                               |
| 주문 미리보기   | 상품명·단가·수량·예상 금액을 먼저 안내합니다. 이 단계에서는 주문을 DB에 저장하지 않습니다.                              |
| 주문 생성     | 고객이 주문 내용을 확인하고 명확히 동의한 경우에만 실제 주문을 생성합니다.                                         |
| 환불 요청     | 주문 상태와 중복 요청 여부를 확인한 후 주문 전체에 대한 환불 요청을 `pending` 상태로 저장합니다.                       |
| 미해결 문의 상담원 접수 | Agent가 처리하지 못한 문의를 지정된 사유와 함께 `open` 상태의 티켓으로 저장합니다.                               |
| 대화 상태 보존  | 고객별 고정 Thread와 LangGraph Checkpointer를 사용해 서버 재시작 후에도 이전 대화를 이어갑니다.                |
| 관리자 기능    | 관리자가 지원 문의 상태를 변경(`open`→`in_progress`→`resolved`)하고, 전체 주문·환불 요청 현황을 조회합니다. Agent/Graph를 거치지 않고 Service를 직접 호출합니다. |

각 기능의 상세 동작(자연어 검색 조건 변환, 주문 생성 단계, 환불 검증 순서 등)은 [아키텍처 문서](docs/ARCHITECTURE.md)에서 다룹니다.

---

## 기술 스택

* **Backend**: Python, FastAPI, SQLAlchemy 2.x, Pydantic
* **Agent**: LangGraph, LangChain Tool Calling
* **Agent LLM**: `gemini-2.5-flash-lite` (`rag_config.py`의 `LLM_MODEL`, Tool 7개 연결)
* **RAG LLM**: `gemini-2.5-flash-lite` (Agent와 동일 모델, 별도 인스턴스로 Tool 없이 텍스트 생성)
* **Embedding**: `gemini-embedding-001` (`rag_config.py`의 `EMBEDDING_MODEL`)
* **Vector Database**: ChromaDB
* **Database**: SQLite

  * `app.db`: 업무 데이터
  * `checkpoints.db`: LangGraph 대화 상태
* **Frontend**: HTML, CSS, JavaScript
* **Template Engine**: 사용하지 않음
* **UI Concept**: 번호표·영수증 형태의 고객센터 디자인 (고객 화면), 테이블·대시보드 형태 (관리자 화면)

같은 모델을 두 개의 별도 인스턴스로 나눈 이유는 [아키텍처 문서 - LLM 구성](docs/ARCHITECTURE.md#llm-구성)에서 다룹니다.

---

## 프로젝트 구조

```text
cs_support_agent/
├── app/
│   ├── routers/
│   │   ├── chat_router.py           # POST /chat, GET /chat/history
│   │   ├── page_router.py           # GET /, GET /chat, GET /admin
│   │   └── admin_router.py          # 관리자 문의 상태 변경, 주문·환불 조회 API
│   ├── main.py                      # FastAPI 앱, lifespan, 라우터 등록
│   └── schemas.py                   # 요청·응답 Pydantic Schema
│
├── application/
│   ├── agent_service.py             # 요청별 의존성 조립, 고객별 Agent 실행
│   └── rag_service.py               # 정책 문서 검색 및 RAG 답변 생성
│
├── database/
│   ├── db.py                        # SQLAlchemy Engine, Base, Session
│   ├── models.py                    # 업무 데이터 ORM Model
│   └── seed.py                      # 샘플 데이터 삽입
│
├── repositories/
│   ├── product_repository.py        # 상품 키워드·가격 검색, ID 조회
│   ├── order_repository.py          # user_id 조건 주문 조회, 저장
│   ├── refund_repository.py         # 환불 요청 조회 및 저장
│   ├── support_ticket_repository.py # 문의 티켓 조회 및 저장
│   └── user_repository.py           # 고객 조회
│
├── services/
│   ├── product_service.py           # 검색 조건 검증, 활성 상품 확인
│   ├── order_service.py             # 주문 조회·미리보기·생성
│   ├── refund_service.py            # 환불 상태 검증, 중복 요청 차단
│   └── support_ticket_service.py    # 문의 내용과 접수 사유 검증, 관리자 상태 변경
│
├── graph/
│   ├── state.py                     # AgentState 정의
│   ├── tools.py                     # 고객별 Tool 7종 생성
│   ├── nodes.py                     # Agent Node와 Tool Node
│   └── builder.py                   # Graph 배선 및 Compile
│
├── infrastructure/
│   ├── llm_client.py                # RagService 전용 Gemini Client
│   └── vector_store.py              # ChromaDB 접근 Wrapper
│
├── prompts/
│   ├── agent_prompt.py              # Agent System Prompt
│   └── rag_prompt.py                # RAG 답변 Prompt
│
├── templates/
│   ├── index.html                   # 고객 선택 화면
│   ├── chat.html                    # 고객 채팅 화면
│   └── admin.html                   # 관리자 화면 (문의/주문/환불 3개 탭)
│
├── static/
│   ├── css/
│   │   ├── style.css                # 번호표·영수증 콘셉트 디자인 (고객 화면)
│   │   └── admin.css                # 테이블·대시보드 콘셉트 디자인 (관리자 화면)
│   └── js/
│       ├── chat.js                  # 채팅 요청 및 화면 렌더링
│       └── admin.js                 # 관리자 탭 전환, API 호출, 문의 상태 변경
│
├── data/
│   ├── chatbot_guide.txt            # 챗봇 가이드 문서
│   ├── order_policy.txt             # 주문 정책 문서
│   ├── refund_policy.txt            # 환불 정책 문서
│   └── shipping_policy.txt          # 배송 정책 문서
│
├── docs/
│   ├── ARCHITECTURE.md              # 아키텍처, LLM 구성, 요청 처리 흐름
│   ├── EXCEPTIONS.md                # Service 레이어 예외와 처리 위치 매핑
│   ├── TROUBLESHOOTING.md           # 기술적 문제와 해결 과정
│   └── RETROSPECTIVE.md             # 프로젝트 회고
│
├── ingest.py                        # 정책 문서 청킹·Embedding·저장
├── rag_config.py                    # RAG와 Gemini 관련 환경 설정
├── requirements.txt                 # 의존성 패키지
├── app.db                           # 업무 데이터, 자동 생성
├── checkpoints.db                   # 대화 상태, 자동 생성
└── chroma_db/                       # 정책 문서 Vector DB, 자동 생성
```

`app.db`, `checkpoints.db`, `chroma_db/`, `.env`는 Git 저장 대상에서 제외합니다.

---

## 실행 방법

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. Gemini API 키 설정

프로젝트 루트에 `.env` 파일을 만들고 다음과 같이 작성하세요.

```dotenv
GEMINI_API_KEY=
```

Gemini API 사용량 제한으로 인해 반복적인 Agent 테스트 중 호출 제한이 발생할 수 있습니다. 정확한 할당량은 사용 중인 모델과 계정의 현재 API 제한을 확인해야 합니다.

### 3. 업무 DB 초기화

```bash
python -m database.seed
```

다음과 같은 테스트용 샘플 데이터가 삽입됩니다.

* 고객 5명
* 상품 20개
* 주문 11건
* 환불 요청 샘플
* 문의 티켓 샘플

이미 데이터가 존재하면 중복 삽입하지 않습니다.

업무 데이터를 완전히 초기화하려면 서버를 종료한 뒤 `app.db` 파일을 삭제하고 다시 실행합니다.

```bash
rm app.db
python -m database.seed
```

### 4. 정책 문서 인덱싱

```bash
python ingest.py
```

`data/` 폴더의 정책 문서는 다음 과정을 거쳐 ChromaDB에 저장됩니다.

```text
문서 로드
→ 청킹
→ Gemini Embedding 생성
→ ChromaDB 저장
```

정책 문서를 수정한 경우 `ingest.py`를 다시 실행해야 합니다. 현재 인덱싱 과정은 기존 Vector Store를 초기화한 뒤 새로운 문서로 다시 생성합니다.

### 5. 서버 실행

```bash
uvicorn app.main:app --reload
```

브라우저에서 다음 주소로 접속합니다.

```text
http://localhost:8000
```

고객 1~5번 중 하나를 선택한 뒤 채팅을 시작할 수 있습니다.

---

## 사용 방법

1. 첫 화면에서 고객 번호를 선택합니다.
2. 선택한 고객의 `user_id`가 `/chat?user=N` 형태로 전달됩니다.
3. `chat.js`가 URL의 `user` 값을 읽어 현재 고객 번호를 확인합니다.
4. `/chat/history?user_id=N` 요청으로 이전 대화를 불러옵니다.
5. 고객별 `thread_id`를 기준으로 저장된 대화 State를 조회합니다.
6. 채팅창에서 정책 질문이나 상품·주문·환불 관련 요청을 입력합니다.
7. Agent가 적절한 Tool을 선택해 업무를 처리하고 결과를 안내합니다.

로그인과 회원가입 기능은 구현하지 않았으며, 테스트용으로 미리 생성된 고객 5명을 선택하는 방식입니다. 같은 고객 번호로 다시 접속하면 `thread_id=customer-{user_id}`에 저장된 이전 대화를 `checkpoints.db`에서 복원합니다.

### 관리자 사용 방법

1. 첫 화면에서 "관리자" 티켓을 선택하면 `/admin`으로 이동합니다.
2. 문의 관리·주문 조회·환불 요청 3개 탭에서 각각의 목록을 확인할 수 있습니다.
3. 문의 관리 탭의 상태 드롭다운을 변경하면 별도 저장 버튼 없이 즉시 반영됩니다.
4. 주문 조회, 환불 요청 탭은 조회 전용이며 상태를 바꾸는 기능은 없습니다.

관리자 기능은 Agent와 LangGraph를 거치지 않고 admin_router.py가 Service를 직접 호출합니다. 자연어 해석이 필요 없는 단순 조회·상태 변경이라 Tool Calling 구조를 거칠 이유가 없다고 판단했습니다.

---

## API

| Method | Endpoint                          | 설명                        |
| ------ | ---------------------------------- | ------------------------- |
| `GET`  | `/`                               | 고객 선택 화면                  |
| `GET`  | `/chat?user={user_id}`            | 고객별 채팅 화면                 |
| `POST` | `/chat`                           | 고객 메시지를 Agent에 전달하고 답변 반환 |
| `GET`  | `/chat/history?user_id={user_id}` | 고객별 저장된 대화 기록 조회          |
| `GET`  | `/admin`                          | 관리자 대시보드 화면               |
| `GET`  | `/admin/tickets`                  | 전체 지원 문의 목록 조회 (관리자)      |
| `PATCH`| `/admin/tickets/{ticket_id}/status` | 지원 문의 상태 변경 (관리자)      |
| `GET`  | `/admin/orders`                   | 전체 주문 목록 조회 (관리자)         |
| `GET`  | `/admin/refunds`                  | 전체 환불 요청 목록 조회 (관리자)      |

---

## 현재 지원 범위

* 로그인과 회원가입 없이 미리 생성된 고객 5명을 선택하는 방식
* 고객 한 명당 하나의 고정 대화 Thread 사용
* 상품명·종류·브랜드·색상·특징·가격 범위를 조합한 상품 검색
* 주문 1건당 상품 1종과 수량만 지원
* 장바구니와 여러 상품 동시 주문은 지원하지 않음
* 주문 전체 환불 요청만 지원
* 부분 환불과 환불 승인·완료 처리는 지원하지 않음
* 관리자 페이지에서 지원 문의 상태 변경(`open`/`in_progress`/`resolved`), 전체 주문·환불 요청 조회 가능
* 정책 문서를 수정한 경우 ChromaDB 재인덱싱 필요
* Agent Prompt 또는 State 구조 변경 후 기존 Checkpoint 초기화가 필요할 수 있음

---

## 더 알아보기

- [아키텍처와 Agent 동작 원리](docs/ARCHITECTURE.md) — 설계 원칙, LLM 구성, Tool 구성, 요청 처리 흐름, 대화 상태 관리
- [Service 레이어 예외 설계](docs/EXCEPTIONS.md) — 예외 클래스별 발생 위치, 처리 Tool, 안내 문구 매핑
- [기술적 문제와 해결 과정](docs/TROUBLESHOOTING.md) — 개발 중 만난 문제 7가지와 해결 방법
- [프로젝트 회고](docs/RETROSPECTIVE.md) — 설계하며 배운 것들
