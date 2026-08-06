# repositories/order_repository.py

"""
order_repository.py 역할
orders 테이블에 대한 DB 조회와 새 주문 저장을 전담한다.

핵심 규칙: 고객 본인의 주문 조회는 반드시 user_id와 order_number를
동시에 조건으로 사용한다. 이렇게 쿼리 자체에 두 조건을 같이 걸어두면,
다른 고객의 주문번호를 입력해도 조회 결과가 없는 것처럼 처리되어
다른 고객의 주문 존재 여부가 노출되지 않는다.

save()는 새 Order 객체를 세션에 추가하고 flush까지 수행해
order.id를 즉시 사용할 수 있게 한다 (RefundRepository.save()와 동일한 관례).
commit과 rollback 같은 트랜잭션 확정은 이 파일이 아니라 OrderService가 담당한다.

주문번호(order_number)는 순차 조회로 계산하지 않는다.
동시에 여러 주문이 들어오면 "마지막 번호+1" 계산이 서로 충돌할 수 있기 때문이다.
대신 OrderService가 DB가 자동 발급하는 Order.id를 기반으로
"A" + (1000 + id) 형식의 번호를 만든다. 그래서 이 파일은
get_last_order_number() 같은 메서드를 제공하지 않는다.

이 파일은 주문 가능 여부, 상품 검증, 금액 계산, 주문번호 생성,
환불 가능 여부 같은 업무 규칙을 판단하지 않는다.
"""

from sqlalchemy.orm import Session

from database.models import Order


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_order_number(
        self, user_id: int, order_number: str
    ) -> Order | None:
        """
        본인 주문 조회 전용 (고객용 Tool에서 사용).
        user_id와 order_number가 동시에 일치해야만 결과가 나온다.
        다른 고객의 주문번호를 입력하면 그냥 None이 반환된다.
        """
        return (
            self.db.query(Order)
            .filter(
                Order.user_id == user_id,
                Order.order_number == order_number,
            )
            .first()
        )

    def get_by_user(self, user_id: int) -> list[Order]:
        """특정 고객이 소유한 전체 주문 목록을 조회한다."""
        return (
            self.db.query(Order)
            .filter(Order.user_id == user_id)
            .order_by(Order.id)
            .all()
        )

    def get_all(self) -> list[Order]:
        """전체 주문 목록을 조회한다. 관리자 기능에서 사용한다."""
        return self.db.query(Order).order_by(Order.id).all()

    def save(self, order: Order) -> Order:
        """
        새로운 주문을 세션에 추가하고 flush한다.
        flush 직후 order.id가 채워지므로, 호출하는 쪽(OrderService)이
        바로 이어서 order.id 기반의 주문번호를 만들 수 있다.
        commit은 하지 않는다 — 트랜잭션 확정은 Service의 책임이다.
        """
        self.db.add(order)
        self.db.flush()
        return order