from infrastructure.llm_client import GeminiClient
from infrastructure.vector_store import VectorStore
from application.rag_service import RagService

llm_client = GeminiClient()
vector_store = VectorStore()
rag_service = RagService(llm_client, vector_store)

# 1. 정책 문서로 답변 가능한 질문
question1 = "배송은 얼마나 걸리나요?"
answer1 = rag_service.answer_question(question1)
print("질문:", question1)
print("답변:", answer1)

print("---")

# 2. 정책 문서에 없는 질문 (NO_POLICY_ANSWER_MESSAGE가 나오는지 확인용)
question2 = "우주여행 상품도 판매하나요?"
answer2 = rag_service.answer_question(question2)
print("질문:", question2)
print("답변:", answer2)



# 질문: 배송은 얼마나 걸리나요?
# 답변: 상품은 주문 확인 후 준비 과정을 거쳐 발송되며, 일반적인 배송 기간은 상품 발송 후 영업일 기준 2일에서 5일 정도입니다. 주말과 공휴일은 배송 기간에 포함되지 않습니다. 도서·산간 지역은 일반 지역보다 배송이 1일에서 3일 정도 더 걸릴 수 있습니다.
# ---
# 질문: 우주여행 상품도 판매하나요?
# 답변: 죄송합니다. 문의하신 내용은 정책 문서에서 확인할 수 없어 상담원 확인이 필요합니다.