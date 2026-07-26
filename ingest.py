"""
정책 문서를 읽고 청킹한 뒤 임베딩하여 ChromaDB에 저장한다.

기존 ChromaDB가 있으면 삭제하고 현재 정책 문서 전체를 새로 저장한다.
질문 검색과 답변 생성은 이 파일의 책임이 아니다.
"""

import shutil
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from infrastructure.llm_client import GeminiClient
from infrastructure.vector_store import VectorStore
from rag_config import CHROMA_DIR, CHUNK_OVERLAP, CHUNK_SIZE, POLICY_FILES, validate_rag_config


def load_and_split_documents() -> list[str]:
    """정책 문서들을 하나씩 읽고 청크 목록으로 반환한다."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    chunks: list[str] = []

    for file_path in POLICY_FILES:
        text = Path(file_path).read_text(encoding="utf-8")
        chunks.extend(text_splitter.split_text(text))

    return chunks


def reset_vector_store() -> None:
    """기존 ChromaDB 저장 폴더를 삭제한다."""
    chroma_path = Path(CHROMA_DIR)

    if chroma_path.exists():
        shutil.rmtree(chroma_path)


def main() -> None:
    """정책 문서 전체를 임베딩하여 ChromaDB에 새로 저장한다."""
    validate_rag_config()

    chunks = load_and_split_documents()

    llm_client = GeminiClient()
    embeddings = llm_client.embed_documents(chunks)

    reset_vector_store()

    vector_store = VectorStore()
    vector_store.add_documents(chunks, embeddings)

    print("정책 문서 적재 완료")
    print(f"문서 수: {len(POLICY_FILES)}")
    print(f"청크 수: {len(chunks)}")


if __name__ == "__main__":
    main()