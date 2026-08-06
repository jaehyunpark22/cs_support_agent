# services/product_service.py

"""
product_service.py 역할
상품 검색에 사용할 키워드와 가격 조건을 정리·검증하고,
검증된 값을 ProductRepository에 전달한다.

또한 주문 기능에서 사용할, 상품번호(id) 하나가 실제로
주문 가능한 상품인지(존재 + 판매중) 확인하는 기능도 제공한다.

DB 조회 자체는 ProductRepository가 담당하며,
사용자 질문을 해석하거나 고객에게 보여줄 답변 문장을 만드는 것은
이 파일의 책임이 아니다.

Repository 검색 결과가 없으면 빈 리스트를 그대로 반환한다.
"""


from database.models import Product
from repositories.product_repository import ProductRepository


class ProductServiceError(Exception):
    """상품 서비스 예외의 기본 클래스"""


class ProductSearchConditionRequiredError(ProductServiceError):
    """상품 검색 조건이 하나도 없는 경우"""


class ProductPriceTypeError(ProductServiceError):
    """상품 가격 조건이 int가 아닌 경우"""


class ProductPriceInvalidError(ProductServiceError):
    """상품 가격 조건이 1원 미만인 경우"""


class ProductPriceRangeError(ProductServiceError):
    """최소 가격이 최대 가격보다 큰 경우"""


class ProductIdRequiredError(ProductServiceError):
    """상품번호가 입력되지 않은 경우"""


class ProductIdTypeError(ProductServiceError):
    """상품번호가 int가 아닌 경우"""


class ProductNotFoundError(ProductServiceError):
    """상품이 존재하지 않거나 판매중지 상태인 경우 (구분하지 않음)"""


class ProductService:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def search_products(
        self,
        keywords: list[str] | None = None,
        price_min: int | None = None,
        price_max: int | None = None,
    ) -> list[Product]:
        """
        상품 검색 조건을 정리·검증한 뒤 상품 목록을 조회한다.

        keywords=None은 빈 리스트로 처리한다.
        키워드는 strip 후 빈 값을 제거하고, 입력 순서를 유지하며 중복을 제거한다.
        가격은 입력된 경우 int이면서 1원 이상이어야 한다.
        최소 가격은 최대 가격보다 클 수 없다.
        검색 조건이 모두 없으면 예외를 발생시킨다.
        """
        normalized_keywords = self._normalize_keywords(keywords)
        self._validate_price("최소 가격", price_min)
        self._validate_price("최대 가격", price_max)

        if price_min is not None and price_max is not None and price_min > price_max:
            raise ProductPriceRangeError("최소 가격은 최대 가격보다 클 수 없습니다.")

        if not normalized_keywords and price_min is None and price_max is None:
            raise ProductSearchConditionRequiredError(
                "상품 종류, 색상, 브랜드, 특징 또는 가격 조건이 필요합니다."
            )

        return self.product_repository.search(
            keywords=normalized_keywords,
            price_min=price_min,
            price_max=price_max,
        )

    def get_active_product(self, product_id: int) -> Product:
        """
        주문 가능한 상품인지 확인하고 반환한다.

        product_id는 정수여야 하며, 존재하지 않거나 판매중지(is_active=False)
        상품이면 ProductNotFoundError를 발생시킨다 (두 경우를 구분하지 않는다).
        """
        if product_id is None:
            raise ProductIdRequiredError("상품번호가 필요합니다.")

        if not isinstance(product_id, int) or isinstance(product_id, bool):
            raise ProductIdTypeError("상품번호는 정수여야 합니다.")

        product = self.product_repository.get_by_id(product_id)
        if product is None or not product.is_active:
            raise ProductNotFoundError("주문 가능한 상품이 아닙니다.")

        return product

    @staticmethod
    def _normalize_keywords(keywords: list[str] | None) -> list[str]:
        normalized_keywords = []
        seen = set()

        for keyword in keywords or []:
            keyword = keyword.strip()

            if not keyword or keyword in seen:
                continue

            normalized_keywords.append(keyword)
            seen.add(keyword)

        return normalized_keywords

    @staticmethod
    def _validate_price(field_name: str, price: int | None) -> None:
        if price is None:
            return

        if not isinstance(price, int) or isinstance(price, bool):
            raise ProductPriceTypeError(f"{field_name}은 정수여야 합니다.")

        if price < 1:
            raise ProductPriceInvalidError(f"{field_name}은 1원 이상이어야 합니다.")