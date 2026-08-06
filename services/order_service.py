# services/order_service.py

"""
order_service.py 역할
주문 조회, 주문 미리보기, 주문 생성(상품 1종 + 수량)과 관련된 업무 규칙을 처리한다.

여러 상품을 한 번에 담는 장바구니 방식은 지원하지 않는다.
주문은 항상 상품 1종에 수량만 조절하는 형태다.

고객 주문 조회는 반드시 user_id와 order_number를 함께 사용한다.
주문번호가 존재하지 않는 경우와 다른 고객의 주문인 경우를 구분하지 않아
다른 고객의 주문 존재 여부가 노출되지 않도록 한다.

주문은 미리보기(preview_order)와 생성(create_order) 두 단계로 나뉜다.
preview_order는 상품과 수량을 검증하고 현재 가격으로 예상 금액만 계산하며
DB에는 저장하지 않는다.

create_order는 동일한 product_id와 quantity를 받아 실제 주문을 저장한다.
현재는 상품 가격 변경 관리 기능이 없으므로 미리보기 이후 가격 변경 여부는
별도로 비교하지 않는다. 다만 상품의 존재 여부와 활성 상태는 저장 직전에
다시 확인하며, 주문 금액도 저장 시점의 DB 가격으로 다시 계산한다.

고객에게 미리보기를 보여주고 최종 주문 의사를 확인하는 것은 Agent의 책임이며,
이 파일은 주문 정보 검증과 DB 저장만 담당한다.

상품이 존재하고 판매 중인지 판단하는 것은 ProductService에 위임하며,
ProductService에서 발생한 업무 예외는 감싸지 않고 그대로 전달한다.

주문번호는 DB가 자동 발급하는 Order.id를 기반으로
"A" + (1000 + id) 형식으로 생성한다. Order.id를 미리 알 수 없으므로
고유한 임시 주문번호로 먼저 저장하고, flush로 id를 확보한 뒤
실제 주문번호로 변경하여 commit한다.

실제 DB 조회와 저장은 OrderRepository가 담당한다.
주문 저장에 성공하면 commit하고, 저장 중 오류가 발생하면 rollback한 뒤
원래 예외를 그대로 전달한다.
"""

from typing import TypedDict
from uuid import uuid4

from sqlalchemy.orm import Session

from database.models import Order, OrderItem
from repositories.order_repository import OrderRepository
from services.product_service import ProductService


class OrderPreview(TypedDict):
    product_id: int
    product_name: str
    quantity: int
    unit_price: int
    total_amount: int


class OrderServiceError(Exception):
    """주문 업무 처리 중 발생하는 기본 예외다."""


class OrderNumberRequiredError(OrderServiceError):
    """주문번호가 입력되지 않았을 때 발생한다."""


class OrderNumberTypeError(OrderServiceError):
    """주문번호가 문자열이 아닐 때 발생한다."""


class OrderNotFoundError(OrderServiceError):
    """
    고객의 주문을 확인할 수 없을 때 발생한다.

    주문번호가 존재하지 않는 경우와 다른 고객의 주문인 경우를
    구분하지 않아 다른 고객의 주문 존재 여부가 노출되지 않도록 한다.
    """


class OrderQuantityRequiredError(OrderServiceError):
    """주문 수량이 입력되지 않았을 때 발생한다."""


class OrderQuantityTypeError(OrderServiceError):
    """주문 수량이 int가 아닐 때 발생한다."""


class OrderQuantityInvalidError(OrderServiceError):
    """주문 수량이 1개 미만일 때 발생한다."""


class OrderService:
    def __init__(
        self,
        db: Session,
        order_repository: OrderRepository,
        product_service: ProductService,
    ):
        self.db = db
        self.order_repository = order_repository
        self.product_service = product_service

    def get_customer_order(
        self,
        user_id: int,
        order_number: str | None,
    ) -> Order:
        """현재 고객이 소유한 주문 1건을 조회한다."""
        if order_number is None:
            raise OrderNumberRequiredError("주문번호가 필요합니다.")

        if not isinstance(order_number, str):
            raise OrderNumberTypeError("주문번호는 문자열이어야 합니다.")

        normalized_order_number = order_number.strip().upper()

        if not normalized_order_number:
            raise OrderNumberRequiredError("주문번호가 필요합니다.")

        order = self.order_repository.get_by_user_and_order_number(
            user_id=user_id,
            order_number=normalized_order_number,
        )

        if order is None:
            raise OrderNotFoundError("주문을 확인할 수 없습니다.")

        return order

    def get_customer_orders(self, user_id: int) -> list[Order]:
        """현재 고객이 소유한 전체 주문 목록을 조회한다."""
        return self.order_repository.get_by_user(user_id)

    def get_all_orders(self) -> list[Order]:
        """전체 주문 목록을 조회한다. 관리자 기능에서 사용한다."""
        return self.order_repository.get_all()

    def preview_order(
        self,
        product_id: int,
        quantity: int | None,
    ) -> OrderPreview:
        """
        상품 1종의 주문 가능 여부를 확인하고 예상 주문 내용을 반환한다.

        DB에는 저장하지 않으며, 가격과 총금액은
        Product 테이블의 현재 가격을 기준으로 계산한다.
        """
        self._validate_quantity(quantity)
        product = self.product_service.get_active_product(product_id)

        return {
            "product_id": product.id,
            "product_name": product.name,
            "quantity": quantity,
            "unit_price": product.price,
            "total_amount": product.price * quantity,
        }

    def create_order(
        self,
        user_id: int,
        product_id: int,
        quantity: int | None,
    ) -> Order:
        """
        상품 1종을 지정한 수량만큼 실제로 주문한다.

        저장 직전에 수량과 상품의 판매 가능 여부를 다시 확인하며,
        가격과 총금액은 저장 시점의 Product 테이블 값을 사용한다.
        """
        self._validate_quantity(quantity)
        product = self.product_service.get_active_product(product_id)

        order = Order(
            user_id=user_id,
            order_number=self._create_temporary_order_number(),
            status="preparing",
            total_amount=product.price * quantity,
            order_items=[
                OrderItem(
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=product.price,
                )
            ],
        )

        try:
            saved_order = self.order_repository.save(order)
            saved_order.order_number = self._create_order_number(saved_order.id)
            self.db.commit()
            self.db.refresh(saved_order)
            return saved_order
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _validate_quantity(quantity: int | None) -> None:
        if quantity is None:
            raise OrderQuantityRequiredError("주문 수량이 필요합니다.")

        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise OrderQuantityTypeError("주문 수량은 정수여야 합니다.")

        if quantity < 1:
            raise OrderQuantityInvalidError("주문 수량은 1개 이상이어야 합니다.")

    @staticmethod
    def _create_temporary_order_number() -> str:
        """flush 전에 사용할 내부용 고유 임시 주문번호를 생성한다."""
        return f"TMP-{uuid4().hex[:20].upper()}"

    @staticmethod
    def _create_order_number(order_id: int) -> str:
        """DB 주문 ID를 고객에게 보여줄 주문번호 형식으로 변환한다."""
        return f"A{1000 + order_id}"