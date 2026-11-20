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


# 没有迁移工具：新增列在这里登记，启动时对旧库补列。(表, 列, DDL)
_ADDED_COLUMNS = [
    ("environment", "allow_fund", "BOOLEAN NOT NULL DEFAULT 0"),
    ("run", "suite_id", "INTEGER"),
    ("run", "schedule_id", "INTEGER"),
    ("run", "title", "VARCHAR(200) NOT NULL DEFAULT ''"),
]


def _add_missing_columns() -> None:
    with engine.begin() as conn:
        for table, column, ddl in _ADDED_COLUMNS:
            cols = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})")}
            if cols and column not in cols:  # 表不存在（cols 为空）时由 create_all 负责建表
                conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_db() -> None:
    from sentinel.backend import models  # noqa: F401  注册模型
    Base.metadata.create_all(engine)
    _add_missing_columns()
