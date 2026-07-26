"""
정책 문서 청크를 ChromaDB에 저장하고, 질문과 비슷한 청크를 검색한다.

임베딩 벡터는 이미 계산되어 있다고 가정한다 (llm_client.py 담당).
문서 읽기, 청킹, 임베딩 계산은 이 파일의 책임이 아니다.
"""

import uuid

import chromadb

from rag_config import CHROMA_DIR, COLLECTION_NAME, TOP_K


class VectorStoreError(Exception):
    """VectorStore에서 발생하는 모든 오류."""


class VectorStore:
    """ChromaDB에 문서를 저장하고 검색하는 기능을 제공한다."""

    def __init__(self) -> None:
        try:
            client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            self._collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                configuration={"hnsw": {"space": "cosine"}},
            )
        except Exception as error:
            raise VectorStoreError("ChromaDB 연결에 실패했습니다.") from error

    def add_documents(self, texts: list[str], embeddings: list[list[float]]) -> None:
        """텍스트와 임베딩 벡터를 저장한다."""
        if not texts or not embeddings:
            raise VectorStoreError("저장할 텍스트와 임베딩이 필요합니다.")
        if len(texts) != len(embeddings):
            raise VectorStoreError("텍스트 개수와 임베딩 개수가 같아야 합니다.")

        ids = [str(uuid.uuid4()) for _ in texts]

        try:
            self._collection.add(ids=ids, documents=texts, embeddings=embeddings)
        except Exception as error:
            raise VectorStoreError("문서 저장에 실패했습니다.") from error

    def search(self, query_embedding: list[float], top_k: int = TOP_K) -> list[str]:
        """질문 벡터와 비슷한 텍스트를 top_k개 찾아서 반환한다."""
        if not query_embedding:
            raise VectorStoreError("검색할 벡터가 필요합니다.")

        try:
            result = self._collection.query(query_embeddings=[query_embedding], n_results=top_k)
        except Exception as error:
            raise VectorStoreError("검색에 실패했습니다.") from error

        return result["documents"][0]