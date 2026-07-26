from prompts.rag_prompt import (
    build_rag_prompt,
    NO_POLICY_ANSWER_MESSAGE,
    QuestionRequiredError,
    PolicyChunksRequiredError,
    InvalidPolicyChunkError,
    RagPromptError,
)

question = "배송은 얼마나 걸리나요?"
chunks = [
    "일반적인 배송 기간은 상품 발송 후 영업일 기준 2일에서 5일 정도입니다. 주말과 공휴일은 배송 기간에 포함되지 않습니다.",
    "배송 상태는 마이페이지에서 확인할 수 있습니다.",
    "주문 상태가 배송중으로 변경된 이후에는 배송지 변경이 불가능합니다.",
]

# 1. 정상 케이스
prompt = build_rag_prompt(question, chunks)
print(prompt)
print("---")

# 2. 질문 없음
try:
    build_rag_prompt("", chunks)
except QuestionRequiredError as e:
    print("QuestionRequiredError 정상 발생:", e)

# 3. 청크 리스트 없음
try:
    build_rag_prompt(question, [])
except PolicyChunksRequiredError as e:
    print("PolicyChunksRequiredError 정상 발생:", e)

# 4. 청크 안에 빈 문자열 섞임
try:
    build_rag_prompt(question, ["정상 청크", "", "정상 청크2"])
except InvalidPolicyChunkError as e:
    print("InvalidPolicyChunkError 정상 발생:", e)

# 5. 자식 클래스가 부모로도 잡히는지 확인
try:
    build_rag_prompt(question, None)
except RagPromptError as e:
    print("부모 클래스(RagPromptError)로 정상 포착:", type(e).__name__, "-", e)

# 6. 질문 타입이 문자열이 아닌 경우
try:
    build_rag_prompt(123, chunks)
except QuestionRequiredError as e:
    print("타입 오류도 QuestionRequiredError로 정상 발생:", e)


# 당신은 쇼핑몰 고객센터 상담원입니다.

# 다음 규칙을 반드시 지켜 답변하세요.

# - 제공된 정책 문서만 근거로 답변하세요.
# - 정책 문서에 없는 내용은 추측하지 마세요.
# - 사용자 질문과 관계없는 정책 내용은 답변에서 제외하세요.
# - 정책 문서에서 확인할 수 있는 범위까지만 답변하세요.
# - 고객이 이해하기 쉽도록 짧고 명확하게 답변하세요.
# - 정책 문서에서 질문에 대한 답을 확인할 수 없다면 다른 내용을 추가하지 말고 다음 문장을 그대로 반환하세요.

# 죄송합니다. 문의하신 내용은 정책 문서에서 확인할 수 없어 상담원 확인이 필요합니다.

# [정책 문서]
# [정책 문서 1]
# 일반적인 배송 기간은 상품 발송 후 영업일 기준 2일에서 5일 정도입니다. 주말과 공휴일은 배송 기간에 포함되지 않습니다.

# [정책 문서 2]
# 배송 상태는 마이페이지에서 확인할 수 있습니다.

# [정책 문서 3]
# 주문 상태가 배송중으로 변경된 이후에는 배송지 변경이 불가능합니다.

# [사용자 질문]
# 배송은 얼마나 걸리나요?

# ---
# QuestionRequiredError 정상 발생: 사용자 질문이 필요합니다.
# PolicyChunksRequiredError 정상 발생: 검색된 정책 청크가 필요합니다.
# InvalidPolicyChunkError 정상 발생: 정책 청크는 비어 있지 않은 문자열이어야 합니다.
# 부모 클래스(RagPromptError)로 정상 포착: PolicyChunksRequiredError - 검색된 정책 청크가 필요합니다.
# 타입 오류도 QuestionRequiredError로 정상 발생: 사용자 질문이 필요합니다.