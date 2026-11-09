from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sentinel.backend.db import Base


def _now() -> datetime:
    return datetime.now()


class Project(Base):
    __tablename__ = "project"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    root_path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    environments: Mapped[list["Environment"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    cases: Mapped[list["TestCase"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    runs: Mapped[list["Run"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Environment(Base):
    __tablename__ = "environment"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50))
    base_url: Mapped[str] = mapped_column(String(500))
    email: Mapped[str] = mapped_column(String(200), default="")
    password: Mapped[str] = mapped_column(String(200), default="")
    headless: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped[Project] = relationship(back_populates="environments")


class TestCase(Base):
    __tablename__ = "test_case"
    __table_args__ = (UniqueConstraint("project_id", "nodeid"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"))
    nodeid: Mapped[str] = mapped_column(String(500))
    file: Mapped[str] = mapped_column(String(300))
    name: Mapped[str] = mapped_column(String(200))
    markers: Mapped[list] = mapped_column(JSON, default=list)
    docstring: Mapped[str] = mapped_column(Text, default="")
    remark: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active / removed
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    project: Mapped[Project] = relationship(back_populates="cases")


class Run(Base):
    __tablename__ = "run"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"))
    environment_id: Mapped[int | None] = mapped_column(ForeignKey("environment.id", ondelete="SET NULL"), nullable=True)
    environment_name: Mapped[str] = mapped_column(String(50), default="")
    trigger: Mapped[str] = mapped_column(String(20), default="manual")
    # queued / running / passed / failed / error / stopped / interrupted
    status: Mapped[str] = mapped_column(String(20), default="queued")
    selected_nodeids: Mapped[list] = mapped_column(JSON, default=list)
    total: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    duration: Mapped[float] = mapped_column(Float, default=0)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project: Mapped[Project] = relationship(back_populates="runs")
    results: Mapped[list["CaseResult"]] = relationship(back_populates="run", cascade="all, delete-orphan", order_by="CaseResult.id")


class CaseResult(Base):
    __tablename__ = "case_result"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id", ondelete="CASCADE"))
    test_case_id: Mapped[int | None] = mapped_column(ForeignKey("test_case.id", ondelete="SET NULL"), nullable=True)
    nodeid: Mapped[str] = mapped_column(String(500))
    outcome: Mapped[str] = mapped_column(String(20))  # passed / failed / skipped / error
    duration: Mapped[float] = mapped_column(Float, default=0)
    steps: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str] = mapped_column(Text, default="")
    screenshot: Mapped[str] = mapped_column(String(300), default="")  # 相对 run_dir 的文件名

    run: Mapped[Run] = relationship(back_populates="results")


FINISHED_STATUSES = ("passed", "failed", "error", "stopped", "interrupted")
