from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = "sqlite:///./app.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()



# engine
# → DB 연결 관리자

# SessionLocal
# → Session을 만들어주는 공장

# db = SessionLocal()
# → 실제 DB 작업용 Session

# get_db()
# → 요청마다 Session을 빌려주고 끝나면 닫음