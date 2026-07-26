"""
사용자 질문과 검색된 정책 청크를 Gemini용 RAG 프롬프트로 만든다.

질문 임베딩, 정책 검색, Gemini API 호출은 이 파일의 책임이 아니다.
"""

NO_POLICY_ANSWER_MESSAGE = "죄송합니다. 문의하신 내용은 정책 문서에서 확인할 수 없어 상담원 확인이 필요합니다."


class RagPromptError(Exception):
    """RAG 프롬프트 생성 중 발생하는 모든 오류."""


class QuestionRequiredError(RagPromptError):
    """사용자 질문이 없거나 올바르지 않은 경우."""


class PolicyChunksRequiredError(RagPromptError):
    """검색된 정책 청크 목록이 없는 경우."""


class InvalidPolicyChunkError(RagPromptError):
    """정책 청크에 올바르지 않은 값이 포함된 경우."""


def build_rag_prompt(question: str, chunks: list[str]) -> str:
    """사용자 질문과 검색된 정책 청크를 Gemini 프롬프트로 만든다."""
    if not isinstance(question, str) or not question.strip():
        raise QuestionRequiredError("사용자 질문이 필요합니다.")
    if not isinstance(chunks, list) or not chunks:
        raise PolicyChunksRequiredError("검색된 정책 청크가 필요합니다.")
    if any(not isinstance(chunk, str) or not chunk.strip() for chunk in chunks):
        raise InvalidPolicyChunkError("정책 청크는 비어 있지 않은 문자열이어야 합니다.")

    context = "\n\n".join(
        f"[정책 문서 {index}]\n{chunk.strip()}"
        for index, chunk in enumerate(chunks, start=1)
    )

    return f"""당신은 쇼핑몰 고객센터 상담원입니다.

다음 규칙을 반드시 지켜 답변하세요.

- 제공된 정책 문서만 근거로 답변하세요.
- 정책 문서에 없는 내용은 추측하지 마세요.
- 사용자 질문과 관계없는 정책 내용은 답변에서 제외하세요.
- 정책 문서에서 확인할 수 있는 범위까지만 답변하세요.
- 고객이 이해하기 쉽도록 짧고 명확하게 답변하세요.
- 정책 문서에서 질문에 대한 답을 확인할 수 없다면 다른 내용을 추가하지 말고 다음 문장을 그대로 반환하세요.

{NO_POLICY_ANSWER_MESSAGE}

[정책 문서]
{context}

[사용자 질문]
{question.strip()}
"""