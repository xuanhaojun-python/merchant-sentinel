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
    # 允许执行 fund（真实资金）用例：执行时注入 MS_ALLOW_FUND
    allow_fund: Mapped[bool] = mapped_column(Boolean, default=False)

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
    trigger: Mapped[str] = mapped_column(String(20), default="manual")  # manual / suite / schedule / script
    # 来源（套件 / 定时任务 / 脚本），不加外键：来源删除后执行记录保留，靠 title 展示
    suite_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    schedule_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(200), default="")
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


class Suite(Base):
    """套件：静态用例列表 ∪ marker 表达式匹配到的用例，执行时展开为 nodeid 列表。"""
    __tablename__ = "suite"
    __table_args__ = (UniqueConstraint("project_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    nodeids: Mapped[list] = mapped_column(JSON, default=list)
    marker_expr: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Schedule(Base):
    __tablename__ = "schedule"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"))
    suite_id: Mapped[int] = mapped_column(ForeignKey("suite.id", ondelete="CASCADE"))
    environment_id: Mapped[int | None] = mapped_column(ForeignKey("environment.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    cron: Mapped[str] = mapped_column(String(100))  # 5 段 crontab，本机时区
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    channel_ids: Mapped[list] = mapped_column(JSON, default=list)
    notify_on: Mapped[str] = mapped_column(String(20), default="failed")  # always / failed / never
    last_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    suite: Mapped[Suite] = relationship()


class NotifyChannel(Base):
    """通知渠道（全局，不分项目）：飞书 / 企业微信 / 钉钉机器人，或通用 webhook。"""
    __tablename__ = "notify_channel"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    type: Mapped[str] = mapped_column(String(20))  # feishu / wecom / dingtalk / webhook
    url: Mapped[str] = mapped_column(String(500))
    secret: Mapped[str] = mapped_column(String(200), default="")  # 飞书 / 钉钉加签密钥
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Notification(Base):
    """通知发送记录。"""
    __tablename__ = "notification"
    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("notify_channel.id", ondelete="SET NULL"), nullable=True)
    channel_name: Mapped[str] = mapped_column(String(100), default="")
    channel_type: Mapped[str] = mapped_column(String(20), default="")
    run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    project_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(300), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="success")  # success / failed
    response: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Element(Base):
    """页面元素：从 Page Object 类的大写字符串常量扫描得到。"""
    __tablename__ = "element"
    __table_args__ = (UniqueConstraint("project_id", "page", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"))
    page: Mapped[str] = mapped_column(String(100))   # 类名，如 WithdrawPage
    name: Mapped[str] = mapped_column(String(100))   # 常量名，如 AMOUNT_INPUT
    selector: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20), default="css")  # css / xpath / text / regex / path / name
    file: Mapped[str] = mapped_column(String(300))
    line: Mapped[int] = mapped_column(Integer, default=0)
    refs: Mapped[int] = mapped_column(Integer, default=0)  # 在 pages/ tests/ 中被引用的次数
    remark: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="active")  # active / removed
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Script(Base):
    """录制 / 手写的 Playwright 脚本。"""
    __tablename__ = "script"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(20), default="recorded")  # recorded / manual
    url: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="ready")  # recording / ready / failed
    message: Mapped[str] = mapped_column(Text, default="")
    exported_path: Mapped[str] = mapped_column(String(300), default="")  # 导出到工程后的相对路径
    last_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


FINISHED_STATUSES = ("passed", "failed", "error", "stopped", "interrupted")
