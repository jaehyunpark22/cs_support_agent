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