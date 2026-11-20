from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Project ──
class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    root_path: str = Field(min_length=1)


class ProjectOut(ORM):
    id: int
    name: str
    description: str
    root_path: str
    created_at: datetime
    case_count: int = 0
    env_count: int = 0


# ── Environment ──
class EnvironmentIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    base_url: str = Field(min_length=1)
    email: str = ""
    password: str = ""
    headless: bool = True
    is_default: bool = False
    allow_fund: bool = False


class EnvironmentOut(ORM):
    id: int
    project_id: int
    name: str
    base_url: str
    email: str
    password: str
    headless: bool
    is_default: bool
    allow_fund: bool


# ── TestCase ──
class CaseOut(ORM):
    id: int
    project_id: int
    nodeid: str
    file: str
    name: str
    markers: list[str]
    docstring: str
    remark: str
    tags: list[str]
    status: str
    synced_at: datetime
    last_outcome: str | None = None


class CaseUpdate(BaseModel):
    remark: str | None = None
    tags: list[str] | None = None


class SyncResult(BaseModel):
    added: int
    updated: int
    removed: int
    errors: list[dict]


# ── Run ──
class RunCreate(BaseModel):
    project_id: int
    environment_id: int | None = None
    nodeids: list[str] = Field(min_length=1)


class CaseResultOut(ORM):
    id: int
    nodeid: str
    test_case_id: int | None
    outcome: str
    duration: float
    steps: list[str]
    error: str
    screenshot: str


class RunOut(ORM):
    id: int
    project_id: int
    environment_id: int | None
    environment_name: str
    trigger: str
    suite_id: int | None = None
    schedule_id: int | None = None
    title: str = ""
    status: str
    selected_nodeids: list[str]
    total: int
    passed: int
    failed: int
    skipped: int
    duration: float
    exit_code: int | None
    message: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class RunDetail(RunOut):
    results: list[CaseResultOut]


class Page(BaseModel):
    items: list
    total: int


# ── Suite ──
class SuiteIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    nodeids: list[str] = []
    marker_expr: str = ""


class SuiteOut(ORM):
    id: int
    project_id: int
    name: str
    description: str
    nodeids: list[str]
    marker_expr: str
    created_at: datetime
    updated_at: datetime
    case_count: int = 0          # 展开后的有效用例数
    missing: list[str] = []      # 静态列表中已不存在 / 已移除的用例
    last_run: RunOut | None = None


class SuitePreviewIn(BaseModel):
    nodeids: list[str] = []
    marker_expr: str = ""


class SuiteRunIn(BaseModel):
    environment_id: int | None = None


# ── Schedule ──
class ScheduleIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    suite_id: int
    environment_id: int | None = None
    cron: str = Field(min_length=1)
    enabled: bool = True
    channel_ids: list[int] = []
    notify_on: str = Field("failed", pattern="^(always|failed|never)$")


class ScheduleOut(ORM):
    id: int
    project_id: int
    suite_id: int
    environment_id: int | None
    name: str
    cron: str
    enabled: bool
    channel_ids: list[int]
    notify_on: str
    last_run_id: int | None
    last_run_at: datetime | None
    created_at: datetime
    suite_name: str = ""
    environment_name: str = ""
    next_run_at: datetime | None = None
    last_status: str | None = None


# ── Notification ──
class ChannelIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(pattern="^(feishu|wecom|dingtalk|webhook)$")
    url: str = Field(min_length=1, pattern="^https?://")
    secret: str = ""
    enabled: bool = True


class ChannelOut(ORM):
    id: int
    name: str
    type: str
    url: str
    secret: str
    enabled: bool
    created_at: datetime


class NotificationOut(ORM):
    id: int
    channel_id: int | None
    channel_name: str
    channel_type: str
    run_id: int | None
    project_id: int | None
    title: str
    content: str
    status: str
    response: str
    created_at: datetime


class NotifyRunIn(BaseModel):
    channel_ids: list[int] = Field(min_length=1)


# ── Element ──
class ElementOut(ORM):
    id: int
    project_id: int
    page: str
    name: str
    selector: str
    kind: str
    file: str
    line: int
    refs: int
    remark: str
    status: str
    synced_at: datetime


class ElementUpdate(BaseModel):
    remark: str


class ElementSyncResult(BaseModel):
    added: int
    updated: int
    removed: int
    errors: list[dict]


# ── Script ──
class ScriptIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    content: str = ""


class ScriptOut(ORM):
    id: int
    project_id: int
    name: str
    description: str
    source: str
    url: str
    content: str
    status: str
    message: str
    exported_path: str
    last_run_id: int | None
    created_at: datetime
    updated_at: datetime
    last_status: str | None = None


class RecordIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    url: str = ""
    environment_id: int | None = None   # url 为空时使用该环境的 base_url
    device: str = ""                    # 可选设备模拟，如 "iPhone 13"


class ScriptExportIn(BaseModel):
    filename: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_]+$")
