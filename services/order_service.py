# services/order_service.py

"""
order_service.py 역할
주문 조회와 관련된 업무 규칙을 처리한다.

고객 주문은 반드시 user_id와 order_number를 함께 사용해 조회한다.
주문번호 누락과 주문 조회 실패를 전용 예외로 구분하여,
Tool이 상황에 맞는 안내 문구를 반환할 수 있도록 한다.

실제 DB 조회는 OrderRepository가 담당한다.
현재는 조회 기능만 있으므로 commit과 rollback은 사용하지 않는다.
"""

from database.models import Order
from repositories.order_repository import OrderRepository


class OrderServiceError(Exception):
    """주문 업무 처리 중 발생하는 기본 예외다."""


class OrderNumberRequiredError(OrderServiceError):
    """주문번호가 입력되지 않았을 때 발생한다."""


class OrderNotFoundError(OrderServiceError):
    """
    고객의 주문을 확인할 수 없을 때 발생한다.

    주문번호가 존재하지 않는 경우와 다른 고객의 주문인 경우를
    구분하지 않아 다른 고객의 주문 존재 여부가 노출되지 않도록 한다.
    """


class OrderService:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    def get_customer_order(self, user_id: int, order_number: str) -> Order:
        """현재 고객이 소유한 주문 1건을 조회한다."""
        normalized_order_number = order_number.strip().upper()

        if not normalized_order_number:
            raise OrderNumberRequiredError()

        order = self.order_repository.get_by_user_and_order_number(
            user_id=user_id,
            order_number=normalized_order_number,
        )

        if order is None:
            raise OrderNotFoundError()

        return order

    def get_customer_orders(self, user_id: int) -> list[Order]:
        """현재 고객이 소유한 전체 주문 목록을 조회한다."""
        return self.order_repository.get_by_user(user_id)

    def get_all_orders(self) -> list[Order]:
        """전체 주문 목록을 조회한다. 관리자 기능에서 사용한다."""
        return self.order_repository.get_all()