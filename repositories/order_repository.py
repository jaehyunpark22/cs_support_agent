# repositories/order_repository.py

"""
order_repository.py 역할
orders 테이블에 대한 DB 조회만 전담한다.

핵심 규칙: 고객 본인의 주문 조회는 반드시 user_id와 order_number를
동시에 조건으로 사용한다. 이렇게 쿼리 자체에 두 조건을 같이 걸어두면,
다른 고객의 주문번호를 입력해도 아예 조회 결과가 없는 것처럼 처리되어
"다른 사람의 주문이 존재한다"는 사실 자체가 노출되지 않는다.

이 파일은 환불 가능 여부 같은 업무 규칙을 판단하지 않는다.
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

    def get_by_id(self, order_id: int) -> Order | None:
        """
        ID로 주문 1건 조회 (내부 처리용).
        예: 환불 요청을 생성할 때 이미 확인된 order_id로 다시 조회할 때 사용.
        고객 본인 확인이 이미 끝난 상황에서만 써야 한다.
        """
        return self.db.get(Order, order_id)

    def get_by_user(self, user_id: int) -> list[Order]:
        """특정 고객의 전체 주문 목록을 조회한다."""
        return (
            self.db.query(Order)
            .filter(Order.user_id == user_id)
            .order_by(Order.id)
            .all()
        )

    def get_all(self) -> list[Order]:
        """전체 주문 목록을 조회한다. (관리자 화면용)"""
        return self.db.query(Order).order_by(Order.id).all()