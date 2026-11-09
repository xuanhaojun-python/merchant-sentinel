from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from sentinel.backend import settings


class Base(DeclarativeBase):
    pass


settings.ensure_dirs()
engine = create_engine(
    f"sqlite:///{settings.DATA_DIR / 'sentinel.db'}",
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_conn, _):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("PRAGMA journal_mode=WAL")
    cur.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from sentinel.backend import models  # noqa: F401  注册模型
    Base.metadata.create_all(engine)
