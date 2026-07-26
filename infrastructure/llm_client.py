"""
RAG에서 사용할 Gemini 모델과의 통신을 담당한다.

Gemini 임베딩 모델과 채팅 모델을 생성하고,
정책 문서·질문 임베딩과 텍스트 답변 생성을 제공한다.
문서 읽기, 청킹, ChromaDB 저장·검색, 프롬프트 작성은 담당하지 않는다.
"""

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from rag_config import EMBEDDING_MODEL, GEMINI_API_KEY, LLM_MODEL, LLM_TEMPERATURE


class LlmClientError(Exception):
    """Gemini 클라이언트에서 발생하는 모든 오류의 부모 예외"""

class LlmClientInitializationError(LlmClientError):
    """Gemini 모델 객체를 생성할 수 없을 때 발생"""

class EmbeddingInputError(LlmClientError):
    """임베딩할 문서 또는 질문이 올바르지 않을 때 발생"""

class EmbeddingRequestError(LlmClientError):
    """Gemini 임베딩 API 호출에 실패했을 때 발생한다."""

class PromptRequiredError(LlmClientError):
    """답변 생성에 사용할 프롬프트가 비어 있을 때 발생한다."""

class ChatRequestError(LlmClientError):
    """Gemini 채팅 API 호출에 실패했을 때 발생한다."""

class InvalidModelResponseError(LlmClientError):
    """Gemini 응답이 비어 있거나 예상한 형태가 아닐 때 발생한다."""


class GeminiClient:
    """Gemini 임베딩 모델과 채팅 모델 호출을 제공한다."""

    def __init__(self) -> None:
        if not GEMINI_API_KEY:
            raise LlmClientInitializationError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

        try:
            self._embedding_model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, api_key=GEMINI_API_KEY)
            self._chat_model = ChatGoogleGenerativeAI(model=LLM_MODEL, api_key=GEMINI_API_KEY, temperature=LLM_TEMPERATURE)
        except Exception as error:
            raise LlmClientInitializationError("Gemini 모델 객체를 생성하지 못했습니다.") from error

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """여러 정책 문서 청크를 임베딩 벡터로 변환한다."""
        if not isinstance(texts, list) or not texts:
            raise EmbeddingInputError("임베딩할 문서 문자열 목록이 필요합니다.")
        normalized_texts: list[str] = []
        for text in texts:
            if not isinstance(text, str) or not text.strip():
                raise EmbeddingInputError("임베딩할 문서는 비어 있지 않은 문자열이어야 합니다.")
            normalized_texts.append(text.strip())

        try:
            vectors = self._embedding_model.embed_documents(normalized_texts)
        except Exception as error:
            raise EmbeddingRequestError("정책 문서 임베딩에 실패했습니다.") from error

        if len(vectors) != len(normalized_texts):
            raise InvalidModelResponseError("입력 문서 수와 반환된 임베딩 벡터 수가 다릅니다.")
        if any(not vector for vector in vectors):
            raise InvalidModelResponseError("비어 있는 문서 임베딩 벡터가 반환되었습니다.")
        return vectors

    def embed_query(self, query: str) -> list[float]:
        """고객 질문을 검색용 임베딩 벡터로 변환한다."""
        if not isinstance(query, str) or not query.strip():
            raise EmbeddingInputError("임베딩할 질문이 필요합니다.")
        normalized_query = query.strip()

        try:
            vector = self._embedding_model.embed_query(normalized_query)
        except Exception as error:
            raise EmbeddingRequestError("질문 임베딩에 실패했습니다.") from error

        if not vector:
            raise InvalidModelResponseError("비어 있는 질문 임베딩 벡터가 반환되었습니다.")
        return vector

    def generate_text(self, prompt: str) -> str:
        """완성된 프롬프트를 Gemini에 전달하고 텍스트 답변을 반환한다."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise PromptRequiredError("답변 생성에 사용할 프롬프트가 필요합니다.")
        normalized_prompt = prompt.strip()

        try:
            response = self._chat_model.invoke(normalized_prompt)
        except Exception as error:
            raise ChatRequestError("Gemini 답변 생성에 실패했습니다.") from error

        answer = response.text.strip()
        if not answer:
            raise InvalidModelResponseError("Gemini가 비어 있는 답변을 반환했습니다.")
        return answer