## 프로젝트 폴더 구조

```text
cs_support_agent/
├── .venv/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── schemas.py
│   └── routers/
│       ├── __init__.py
│       ├── chat_router.py
│       ├── admin_router.py
│       └── page_router.py
│
├── application/
│   ├── __init__.py
│   ├── agent_service.py
│   └── rag_service.py
│
├── database/
│   ├── __init__.py
│   ├── db.py
│   ├── models.py
│   └── seed.py
│
├── repositories/
│   ├── __init__.py
│   ├── user_repository.py
│   ├── order_repository.py
│   ├── refund_repository.py
│   └── support_ticket_repository.py
│
├── services/
│   ├── __init__.py
│   ├── order_service.py
│   ├── refund_service.py
│   └── support_ticket_service.py
│
├── graph/
│   ├── __init__.py
│   ├── state.py
│   ├── tools.py
│   ├── nodes.py
│   └── builder.py
│
├── infrastructure/
│   ├── __init__.py
│   ├── llm_client.py
│   └── vector_store.py
│
├── prompts/
│   ├── __init__.py
│   ├── agent_prompt.py
│   └── rag_prompt.py
│
├── templates/
│   ├── index.html
│   ├── chat.html
│   └── admin.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── chat.js
│       └── admin.js
│
├── data/
│   ├── membership.txt
│   ├── refund.txt
│   └── shipping.txt
│
├── tests/
│   ├── __init__.py
│   ├── test_order_service.py
│   ├── test_refund_service.py
│   ├── test_support_ticket_service.py
│   └── test_api.py
│
├── .env
├── .env.example
├── .gitignore
├── README.md
├── ingest.py
├── rag_config.py
└── requirements.txt
```




```text
UserRepository
├── get_by_id(user_id: int) -> User | None
│     입력: 고객 ID
│     반환: 고객 1명 또는 None
│     역할: ID로 고객 1명 조회
│
└── get_all() -> list[User]
      입력: 없음
      반환: 고객 전체 목록 (ID순 정렬)
      역할: 전체 고객 목록 조회 (고객 선택 화면용)


OrderRepository
├── get_by_user_and_order_number(user_id: int, order_number: str) -> Order | None
│     입력: 고객 ID + 주문번호
│     반환: 주문 1건 또는 None
│     역할: 본인 주문 조회 전용. 두 조건이 동시에 맞아야만 결과가 나옴
│           (고객 입력 기반 조회는 반드시 이 함수를 거쳐야 함)
│
├── get_by_id(order_id: int) -> Order | None
│     입력: 주문 ID
│     반환: 주문 1건 또는 None
│     역할: ID로 주문 1건 조회. user_id 검사 없음
│           → 이미 본인 확인이 끝난 order_id로만 사용 (내부 재참조용)
│
├── get_by_user(user_id: int) -> list[Order]
│     입력: 고객 ID
│     반환: 주문 목록
│     역할: 특정 고객의 전체 주문 목록 조회
│
└── get_all() -> list[Order]
      입력: 없음
      반환: 주문 전체 목록
      역할: 전체 주문 목록 조회 (관리자 화면용)


RefundRepository
├── get_pending_by_order(order_id: int) -> RefundRequest | None
│     입력: 주문 ID
│     반환: pending 상태 환불요청 1건 또는 None
│     역할: 해당 주문에 처리 안 된 환불요청이 있는지 조회
│           (중복 접수 차단 판단의 재료 제공, 판단 자체는 안 함)
│
├── get_by_id(refund_request_id: int) -> RefundRequest | None
│     입력: 환불요청 ID
│     반환: 환불요청 1건 또는 None
│     역할: ID로 환불요청 1건 조회
│
├── save(refund_request: RefundRequest) -> RefundRequest
│     입력: RefundRequest 객체 (Service가 미리 만들어서 넘김)
│     반환: 저장된 RefundRequest 객체 (id 확보됨)
│     역할: 새 환불요청 저장. flush()만 함, commit은 Service가 담당
│
├── get_by_user(user_id: int) -> list[RefundRequest]
│     입력: 고객 ID
│     반환: 환불요청 목록
│     역할: 특정 고객의 환불요청 목록 조회
│
└── get_all() -> list[RefundRequest]
      입력: 없음
      반환: 환불요청 전체 목록
      역할: 전체 환불요청 목록 조회 (관리자 화면용)


SupportTicketRepository
├── save(support_ticket: SupportTicket) -> SupportTicket
│     입력: SupportTicket 객체 (Service가 미리 만들어서 넘김)
│     반환: 저장된 SupportTicket 객체 (id 확보됨)
│     역할: 새 지원문의 저장. flush()만 함, commit은 Service가 담당
│
├── get_by_id(support_ticket_id: int) -> SupportTicket | None
│     입력: 문의 ID
│     반환: 문의 1건 또는 None
│     역할: ID로 지원문의 1건 조회
│
├── get_by_user(user_id: int) -> list[SupportTicket]
│     입력: 고객 ID
│     반환: 문의 목록
│     역할: 특정 고객의 지원문의 목록 조회
│
└── get_all() -> list[SupportTicket]
      입력: 없음
      반환: 문의 전체 목록
      역할: 전체 지원문의 목록 조회 (관리자 화면용)
```