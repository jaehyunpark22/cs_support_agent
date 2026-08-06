"""
RAG 파이프라인에서 공통으로 사용할 설정값을 관리한다.
환경 변수, 정책 문서 경로, ChromaDB 저장 경로, Gemini 모델,
청크 크기와 검색 개수 등을 한곳에서 정의한다.
문서 청킹, 임베딩 생성, 검색, 답변 생성은 담당하지 않는다.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 최상위 폴더
BASE_DIR = Path(__file__).resolve().parent

# 주요 파일 및 폴더 경로
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

# RAG에 사용할 정책 문서
POLICY_FILES = (
    DATA_DIR / "order_policy.txt",
    DATA_DIR / "refund_policy.txt",
    DATA_DIR / "shipping_policy.txt",
    DATA_DIR / "chatbot_guide.txt",
)

# .env 환경 변수 불러오기
load_dotenv(dotenv_path=ENV_PATH)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini 모델
EMBEDDING_MODEL = "gemini-embedding-001"
LLM_MODEL = "gemini-2.5-flash-lite"
# "gemini-3.1-flash-lite" "gemini-2.5-flash-lite"

# 답변 생성 시 창의성 정도 (0에 가까울수록 문서 내용에 충실하게 답변)
# RAG는 정책 문서에 있는 사실을 그대로 전달하는 게 목적이므로 낮게 설정
LLM_TEMPERATURE = 0.2

# ChromaDB 컬렉션 이름
COLLECTION_NAME = "policy_documents"

# 문서 청킹 설정
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50

# 질문과 관련된 청크 검색 개수
TOP_K = 3


def validate_rag_config() -> None:
    """RAG 실행에 필요한 환경 변수, 문서, 설정값을 검사한다."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            ".env에서 GEMINI_API_KEY를 찾을 수 없습니다."
        )

    missing_files = [
        path.name
        for path in POLICY_FILES
        if not path.is_file()
    ]
    if missing_files:
        missing_names = ", ".join(missing_files)
        raise RuntimeError(
            f"정책 문서를 찾을 수 없습니다: {missing_names}"
        )

    if CHUNK_SIZE <= 0:
        raise RuntimeError("CHUNK_SIZE는 0보다 커야 합니다.")

    if CHUNK_OVERLAP < 0:
        raise RuntimeError("CHUNK_OVERLAP은 0 이상이어야 합니다.")

    if CHUNK_OVERLAP >= CHUNK_SIZE:
        raise RuntimeError("CHUNK_OVERLAP은 CHUNK_SIZE보다 작아야 합니다.")

    if TOP_K <= 0:
        raise RuntimeError("TOP_K는 0보다 커야 합니다.")

    if not (0.0 <= LLM_TEMPERATURE <= 2.0):
        raise RuntimeError("LLM_TEMPERATURE는 0.0~2.0 사이여야 합니다.")