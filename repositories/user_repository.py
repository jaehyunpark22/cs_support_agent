# repositories/user_repository.py

"""
user_repository.py 역할
users 테이블에 대한 DB 조회만 전담한다.

이 파일은 업무 규칙을 판단하지 않는다.
고객이 실제로 존재하는지, 접근 권한이 있는지 같은 판단은
services/에서 처리한다.
"""

from sqlalchemy.orm import Session

from database.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        """ID로 고객 1명을 조회한다. 없으면 None을 반환한다."""
        return self.db.get(User, user_id)

    def get_all(self) -> list[User]:
        """전체 고객 목록을 조회한다. (고객 선택 화면용)"""
        return self.db.query(User).order_by(User.id).all()