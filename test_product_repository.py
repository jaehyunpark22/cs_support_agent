from database.db import SessionLocal
from repositories.product_repository import ProductRepository


db = SessionLocal()

try:
    repo = ProductRepository(db)

    # 1. 키워드 AND 검색 - "파란색 티셔츠"
    result1 = repo.search(keywords=["파란색", "티셔츠"])
    print("1. 파란색+티셔츠:", [p.name for p in result1])

    # 2. 키워드 AND 검색 - "나이키 신발"
    result2 = repo.search(keywords=["나이키", "신발"])
    print("2. 나이키+신발:", [p.name for p in result2])

    # 3. 가격만으로 검색 - 3만원 이하
    result3 = repo.search(price_max=30000)
    print("3. 3만원 이하:", [(p.name, p.price) for p in result3])

    # 4. 가격 범위 검색 - 4만원 이상 6만원 이하
    result4 = repo.search(price_min=40000, price_max=60000)
    print("4. 4~6만원:", [(p.name, p.price) for p in result4])

    # 5. 결과 없는 경우
    result5 = repo.search(keywords=["나이키", "머그컵"])
    print("5. 나이키+머그컵 (없어야 함):", result5)

    # 6. 아무 조건 없음 - 전체 활성 상품
    result6 = repo.search()
    print("6. 조건 없음 (전체 개수):", len(result6))

    # 7. 정확한 태그 매칭 검증
    result7 = repo.search(keywords=["블루"])
    print("7. '블루' 검색:", [p.name for p in result7])

finally:
    db.close()


# 1. 파란색+티셔츠: ['폴로 블루 반팔 티셔츠']
# 2. 나이키+신발: ['나이키 러닝화']
# 3. 3만원 이하: [('머그컵', 8000), ('텀블러 500ml', 12000), ('양말 5종 세트', 9900), ('노트북 파우치', 25000)]
# 4. 4~6만원: [('후드집업', 45000), ('반스 캔버스화', 59000), ('레인부츠', 42000), ('무지 청바지', 49000), ('나이키 후드티', 59000), ('유니클로 니트', 45000), ('카고 팬츠', 52000)]
# 5. 나이키+머그컵 (없어야 함): []
# 6. 조건 없음 (전체 개수): 20
# 7. '블루' 검색: ['나이키 러닝화', '폴로 블루 반팔 티셔츠', '무지 청바지']