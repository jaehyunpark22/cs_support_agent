# app/routers/page_router.py

"""
page_router.py 역할
브라우저에서 접속하는 HTML 페이지(첫 화면, 채팅 화면, 관리자 화면)를 파일 그대로 돌려준다.
CSS/JS는 이 파일이 아니라 main.py가 마운트한 /static 경로로 서빙된다.

Jinja2를 쓰지 않는다. 지금 페이지들은 서버가 채워 넣을 동적 값이 전혀 없어서
(고객 번호는 브라우저가 URL에서 직접 읽음) 템플릿 엔진이 할 일이 없다.
그냥 파일을 그대로 전달만 하면 되므로 FileResponse를 쓴다.

이 파일이 하지 않는 일:
- 챗봇 응답 생성 (chat_router.py의 POST /chat 담당 — 이 파일과 완전히 무관)
- 관리자 데이터 조회/변경 (admin_router.py 담당 — 이 파일은 admin.html을 돌려주기만 함)
- 업무 로직, DB 접근
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/")
def index():
    return FileResponse("templates/index.html")


@router.get("/chat")
def chat_page():
    return FileResponse("templates/chat.html")


@router.get("/admin")
def admin_page():
    return FileResponse("templates/admin.html")