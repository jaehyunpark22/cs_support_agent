# repositories/product_repository.py

"""
product_repository.py 역할
products 테이블에 대한 DB 조회만 전담한다.

키워드와 가격 범위로 상품을 검색하는 조회만 제공하며,
어떤 값으로 검색할지 판단하는 것은 이 파일의 책임이 아니다
(Gemini 추출, 질문 해석, 값 유효성 검증 등은 상위 계층의 몫).

여러 키워드가 주어지면 AND 조건으로 결합한다
(모든 키워드가 keywords 컬럼에 포함된 상품만 반환).

keywords 컬럼은 "전자기기,스피커,블루투스스피커,블루투스,방수"처럼
쉼표로 구분된 문자열이다. 단순히 LIKE '%블루%'로 검색하면
"블루투스"의 부분 문자열로도 "블루"가 매칭되어 버리므로,
컬럼 앞뒤에 쉼표를 덧붙여 "%,블루,%" 형태로 검색해
쉼표로 정확히 구분된 완전한 단어만 매칭되도록 한다.

현재는 비활성 상품(is_active=False)을 검색 결과에서 제외한다.
이 필터는 상품 활성화·비활성화 관리 기능이 아직 없는 현재 범위에서는
실질적인 영향이 없으며, 추후 관리 기능이 생기면 재검토한다.

조건에 맞는 상품이 없으면 빈 리스트를 반환한다.
"조건에 맞는 상품이 없습니다" 같은 안내 문구를 만드는 것은
이 파일이 아니라 상위 계층(Service)의 책임이다.
"""

from sqlalchemy import literal
from sqlalchemy.orm import Session

from database.models import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def search(
        self,
        keywords: list[str] | None = None,
        price_min: int | None = None,
        price_max: int | None = None,
    ) -> list[Product]:
        """
        키워드와 가격 범위로 상품을 검색한다.

        keywords가 없거나 빈 리스트면 키워드 조건 없이 가격 조건만 적용한다.
        키워드 매칭은 쉼표로 정확히 구분된 완전한 단어 기준이다
        (예: "블루"를 검색해도 "블루투스"는 매칭되지 않는다).
        price_min/price_max는 각각 생략 가능하며, 생략 시 해당 조건은 적용하지 않는다.
        keywords와 price_min, price_max가 전부 없으면 활성 상품 전체를 반환한다.
        """
        query = self.db.query(Product).filter(Product.is_active.is_(True))

        if keywords:
            wrapped_keywords = literal(",") + Product.keywords + literal(",")
            for keyword in keywords:
                query = query.filter(wrapped_keywords.like(f"%,{keyword},%"))

        if price_min is not None:
            query = query.filter(Product.price >= price_min)

        if price_max is not None:
            query = query.filter(Product.price <= price_max)

        return query.order_by(Product.id).all()

    def get_all(self) -> list[Product]:
        """활성 상태인 전체 상품 목록을 조회한다."""
        return (
            self.db.query(Product)
            .filter(Product.is_active.is_(True))
            .order_by(Product.id)
            .all()
        )