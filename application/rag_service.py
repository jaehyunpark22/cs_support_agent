"""
application/rag_service.py



사용자 질문을 임베딩하고 관련 정책을 검색한 뒤,
프롬프트를 만들어 Gemini의 최종 답변을 반환한다.

각 기능의 실제 처리는 GeminiClient, VectorStore,
rag_prompt에 맡기며, 발생한 예외는 상위 코드로 그대로 전달한다.

미처리 문의 저장과 Agent 판단은 이 파일에서 처리하지 않는다.



사용자 질문에 대한 RAG 기반 최종 답변을 생성한다.

질문 임베딩(GeminiClient), 정책 청크 검색(VectorStore),
프롬프트 생성(rag_prompt), 답변 생성(GeminiClient)을
순서대로 호출해 하나의 흐름으로 연결한다.

이 파일이 직접 하지 않는 일:
- 질문 임베딩 계산 자체            (llm_client.py 담당)
- ChromaDB 검색 자체              (vector_store.py 담당)
- 프롬프트 문자열 조립 자체        (rag_prompt.py 담당)
- Gemini 텍스트 생성 자체          (llm_client.py 담당)
- SupportTicket 저장 여부 판단,
  에러를 지원 문의 사유로 변환하는 판단 (agent_service.py / graph 담당)

이 파일은 하위 모듈에서 발생하는 예외
(LlmClientError, VectorStoreError, RagPromptError 및 각각의 자식 예외)를
여기서 잡지 않고 호출한 쪽으로 그대로 전달한다.
시스템 오류를 지원 문의 사유로 둔갑시키지 않기 위함이다.
"""

from infrastructure.llm_client import GeminiClient
from infrastructure.vector_store import VectorStore
from prompts.rag_prompt import build_rag_prompt


class RagService:
    """정책 질문에 대한 RAG 기반 답변 생성 흐름을 조율한다."""

    def __init__(self, llm_client: GeminiClient, vector_store: VectorStore) -> None:
        self.llm_client = llm_client
        self.vector_store = vector_store

    def answer_question(self, question: str) -> str:
        """사용자 질문에 대해 정책 문서를 근거로 한 최종 답변을 반환한다."""
        query_embedding = self.llm_client.embed_query(question)
        chunks = self.vector_store.search(query_embedding)
        prompt = build_rag_prompt(question, chunks)
        return self.llm_client.generate_text(prompt)