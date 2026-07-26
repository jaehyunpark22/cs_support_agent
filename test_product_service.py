from database.db import SessionLocal
from repositories.product_repository import ProductRepository
from services.product_service import (
    ProductService,
    ProductSearchConditionRequiredError,
    ProductPriceTypeError,
    ProductPriceInvalidError,
    ProductPriceRangeError,
)

db = SessionLocal()
repo = ProductRepository(db)
service = ProductService(repo)

# 1. 정상 케이스 - 키워드 정제 (공백/빈값/중복 제거)
result1 = service.search_products(keywords=["파란색", " ", "파란색", " 티셔츠 ", ""])
print("1. 정제된 키워드 검색:", [p.name for p in result1])

# 2. 키워드 없이 가격만
result2 = service.search_products(price_max=30000)
print("2. 3만원 이하:", [p.name for p in result2])

# 3. price_min/price_max 둘 다 정상 범위
result3 = service.search_products(price_min=40000, price_max=60000)
print("3. 4~6만원:", [p.name for p in result3])

# 4. 조건 전부 없음 -> 예외
try:
    service.search_products()
except ProductSearchConditionRequiredError as e:
    print("4. ProductSearchConditionRequiredError 정상 발생:", e)

# 5. price_min > price_max -> 예외
try:
    service.search_products(price_min=60000, price_max=30000)
except ProductPriceRangeError as e:
    print("5. ProductPriceRangeError(범위 역전) 정상 발생:", e)

# 6. 가격 0원 -> 예외 (1원 미만 단일 값 문제)
try:
    service.search_products(price_max=0)
except ProductPriceInvalidError as e:
    print("6. ProductPriceInvalidError(0원) 정상 발생:", e)

# 7. 가격이 문자열로 들어옴 -> 예외
try:
    service.search_products(price_max="30000")
except ProductPriceTypeError as e:
    print("7. ProductPriceTypeError 정상 발생:", e)

# 8. 결과 없는 정상 조합 -> 빈 리스트
result8 = service.search_products(keywords=["나이키", "머그컵"])
print("8. 결과 없음 (빈 리스트여야 함):", result8)

db.close()


# 1. 정제된 키워드 검색: ['폴로 블루 반팔 티셔츠']
# 2. 3만원 이하: ['머그컵', '텀블러 500ml', '양말 5종 세트', '노트북 파우치']
# 3. 4~6만원: ['후드집업', '반스 캔버스화', '레인부츠', '무지 청바지', '나이키 후드티', '유니클로 니트', '카고 팬츠']
# 4. ProductSearchConditionRequiredError 정상 발생: 상품 종류, 색상, 브랜드, 특징 또는 가격 조건이 필요합니다.
# 5. ProductPriceRangeError(범위 역전) 정상 발생: 최소 가격은 최대 가격보다 클 수 없습니다.
# 6. ProductPriceInvalidError(0원) 정상 발생: 최대 가격은 1원 이상이어야 합니다.
# 7. ProductPriceTypeError 정상 발생: 최대 가격은 정수여야 합니다.
# 8. 결과 없음 (빈 리스트여야 함): []