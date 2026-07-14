# database/seed.py


from database.db import Base, SessionLocal, engine
from database.models import (
    User,
    Product,
    Order,
    OrderItem,
    RefundRequest,
    SupportTicket,
)


def seed() -> None:
    # 1. 테이블 생성 (이미 있으면 건드리지 않음)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 이미 데이터가 있으면 중복 삽입 방지
        if db.query(User).first() is not None:
            print("이미 시드 데이터가 존재합니다. 삽입을 건너뜁니다.")
            return

        # 2. 고객 5명
        users = [
            User(name="고객1", email="user1@test.com"),
            User(name="고객2", email="user2@test.com"),
            User(name="고객3", email="user3@test.com"),
            User(name="고객4", email="user4@test.com"),
            User(name="고객5", email="user5@test.com"),
        ]
        db.add_all(users)
        db.flush()  # id 값을 미리 확보하기 위해 flush

        # 3. 상품 10개 (가격대 다양하게)
        products = [
            Product(name="머그컵", price=8000, description="심플한 도자기 머그컵", is_active=True),
            Product(name="텀블러 500ml", price=12000, description="보온보냉 텀블러", is_active=True),
            Product(name="양말 5종 세트", price=9900, description="면 혼방 양말 세트", is_active=True),
            Product(name="노트북 파우치", price=25000, description="13인치용 파우치", is_active=True),
            Product(name="보조배터리 10000mAh", price=32000, description="고속충전 지원", is_active=True),
            Product(name="LED 스탠드 조명", price=38000, description="밝기 조절 가능", is_active=True),
            Product(name="후드집업", price=45000, description="기모 안감 후드집업", is_active=True),
            Product(name="캠핑 의자", price=65000, description="접이식 캠핑 의자", is_active=True),
            Product(name="무선이어폰", price=89000, description="노이즈캔슬링 지원", is_active=True),
            Product(name="블루투스 스피커", price=120000, description="방수 기능 포함", is_active=True),
        ]
        db.add_all(products)
        db.flush()

        # 편하게 참조하기 위해 이름으로 딕셔너리 구성
        p = {product.name: product for product in products}
        u = {f"고객{i+1}": users[i] for i in range(5)}

        # 4. 주문 11개 + order_items
        # (user, order_number, status, items=[(product_name, qty)])
        order_specs = [
            (u["고객1"], "A1001", "delivered", [("텀블러 500ml", 2), ("머그컵", 1)]),
            (u["고객1"], "A1002", "cancelled", [("후드집업", 1)]),
            (u["고객2"], "A1003", "shipped", [("무선이어폰", 1)]),
            (u["고객2"], "A1004", "preparing", [("보조배터리 10000mAh", 1), ("양말 5종 세트", 1)]),
            (u["고객3"], "A1005", "refunded", [("블루투스 스피커", 1)]),
            (u["고객3"], "A1006", "delivered", [("LED 스탠드 조명", 1), ("노트북 파우치", 1)]),
            (u["고객4"], "A1007", "shipped", [("캠핑 의자", 1)]),
            (u["고객4"], "A1008", "preparing", [("텀블러 500ml", 3)]),
            (u["고객4"], "A1009", "delivered", [("머그컵", 2), ("양말 5종 세트", 1)]),
            (u["고객5"], "A1010", "delivered", [("무선이어폰", 1), ("보조배터리 10000mAh", 1)]),
            (u["고객5"], "A1011", "cancelled", [("후드집업", 1)]),
        ]

        order_by_number = {}

        for user, order_number, status, items in order_specs:
            total_amount = sum(p[name].price * qty for name, qty in items)

            order = Order(
                user_id=user.id,
                order_number=order_number,
                status=status,
                total_amount=total_amount,
            )
            db.add(order)
            db.flush()  # order.id 확보

            for name, qty in items:
                product = p[name]
                db.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=qty,
                        unit_price=product.price,  # 주문 당시 가격 보존
                    )
                )

            order_by_number[order_number] = order

        db.flush()

        # 5. 환불 요청 
        # - A1001: 이미 pending 존재 → 중복 환불 차단 테스트용
        
        db.add_all(
            [
                RefundRequest(
                    user_id=u["고객1"].id,
                    order_id=order_by_number["A1001"].id,
                    reason="사이즈가 맞지 않아 환불 원합니다",
                    status="pending",
                ),
                
            ]
        )

        # 6. 지원 문의 4건 (reason 4종, status 3종 모두 포함)
        db.add_all(
            [
                SupportTicket(
                    user_id=u["고객2"].id,
                    question="택배사 조회 연동 되나요?",
                    reason="필요한 Tool이 없음",
                    status="open",
                ),
                SupportTicket(
                    user_id=u["고객3"].id,
                    question="포인트 적립 정책이 뭔가요?",
                    reason="정책 문서에 관련 내용 없음",
                    status="in_progress",
                ),
                SupportTicket(
                    user_id=u["고객5"].id,
                    question="교환은 어떻게 하나요?",
                    reason="지원하지 않는 업무",
                    status="resolved",
                ),
                SupportTicket(
                    user_id=u["고객4"].id,
                    question="복잡한 건인데 사람이 직접 봐주세요",
                    reason="사람의 확인이 필요함",
                    status="open",
                ),
            ]
        )

        db.commit()
        print("시드 데이터 삽입 완료")
        print(f"users={len(users)}, products={len(products)}, orders={len(order_specs)}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()






# seed.py 역할
# database/models.py에 정의된 테이블 구조를 바탕으로 app.db 파일과
# 실제 테이블을 생성하고, 개발·테스트용 샘플 데이터를 채워 넣는다.

# 이 파일은 한 번 실행하고 끝나는 스크립트다.
# 다시 초기화하고 싶으면 app.db 파일을 삭제하고 재실행하면 된다.

# 샘플 데이터는 무작위가 아니라, 다음 업무 규칙이 전부 최소 한 번씩
# 걸리도록 의도적으로 설계했다.

# - 주문 상태 5종(preparing/shipped/delivered/cancelled/refunded) 전부 존재
# - 환불 가능/불가 상태 케이스 모두 존재
# - 이미 pending 환불요청이 있는 주문 (중복 환불 차단 테스트용)
# - 아직 환불요청 없는 delivered 주문 (정상 환불 신청 테스트용)
# - 다른 고객 소유의 주문 (본인 주문 아님 차단 테스트용)
# - 지원 문의 reason 4종, status 3종 전부 존재
