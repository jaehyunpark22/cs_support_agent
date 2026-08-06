# app/main.py

"""
main.py 역할
FastAPI 앱을 생성하고, 라우터를 등록하며, 서버 시작/종료 시 필요한
자원 정리를 lifespan으로 관리한다.

이 파일이 하지 않는 일:
- 요청 처리 로직 (각 router 담당)
- Repository/Service 조립, Agent 실행 (agent_service.py, admin_router.py 담당)
- checkpoint 커넥션을 직접 다루는 것 (agent_service.py의 close_checkpoint()를
  통해서만 접근한다 — _checkpoint_conn은 agent_service.py 내부 구현이라
  바깥에서 직접 참조하지 않는다)

chat_router, page_router, admin_router 3개를 등록한다.
"""


from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.admin_router import router as admin_router
from app.routers.chat_router import router as chat_router
from app.routers.page_router import router as page_router
from application.agent_service import close_checkpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    close_checkpoint()


app = FastAPI(lifespan=lifespan)
app.include_router(chat_router)
app.include_router(page_router)
app.include_router(admin_router)
app.mount("/static", StaticFiles(directory="static"), name="static")