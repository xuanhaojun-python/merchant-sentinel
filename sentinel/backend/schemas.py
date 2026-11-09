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


class EnvironmentOut(ORM):
    id: int
    project_id: int
    name: str
    base_url: str
    email: str
    password: str
    headless: bool
    is_default: bool


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
