from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from sentinel.backend.api.projects import get_project
from sentinel.backend.db import get_db
from sentinel.backend.models import Run, Schedule, Suite
from sentinel.backend.schemas import RunOut, SuiteIn, SuiteOut, SuitePreviewIn, SuiteRunIn
from sentinel.backend.services.runs import enqueue_run, resolve_env
from sentinel.backend.services.suites import compile_expr, expand

router = APIRouter(prefix="/api", tags=["suites"])


def get_suite(db: Session, suite_id: int) -> Suite:
    suite = db.get(Suite, suite_id)
    if suite is None:
        raise HTTPException(404, "套件不存在")
    return suite


def _out(db: Session, s: Suite) -> SuiteOut:
    out = SuiteOut.model_validate(s)
    picked, out.missing = expand(db, s.project_id, s.nodeids, s.marker_expr)
    out.case_count = len(picked)
    last = db.query(Run).filter(Run.suite_id == s.id).order_by(Run.id.desc()).first()
    out.last_run = RunOut.model_validate(last) if last else None
    return out


def _check(db: Session, project_id: int, body: SuiteIn, suite_id: int | None = None) -> None:
    dup = db.query(Suite).filter(Suite.project_id == project_id, Suite.name == body.name, Suite.id != suite_id).first()
    if dup:
        raise HTTPException(400, "套件名称已存在")
    compile_expr(body.marker_expr)
    if not body.nodeids and not body.marker_expr.strip():
        raise HTTPException(400, "请至少选择一条用例或填写 marker 表达式")


@router.get("/projects/{project_id}/suites", response_model=list[SuiteOut])
def list_suites(project_id: int, db: Session = Depends(get_db)):
    get_project(db, project_id)
    return [_out(db, s) for s in db.query(Suite).filter(Suite.project_id == project_id).order_by(Suite.id)]


@router.post("/projects/{project_id}/suites", response_model=SuiteOut, status_code=201)
def create_suite(project_id: int, body: SuiteIn, db: Session = Depends(get_db)):
    get_project(db, project_id)
    _check(db, project_id, body)
    s = Suite(project_id=project_id, **body.model_dump())
    db.add(s)
    db.commit()
    return _out(db, s)


@router.post("/projects/{project_id}/suites/preview", response_model=dict)
def preview(project_id: int, body: SuitePreviewIn, db: Session = Depends(get_db)):
    get_project(db, project_id)
    picked, missing = expand(db, project_id, body.nodeids, body.marker_expr)
    return {"nodeids": picked, "missing": missing}


@router.get("/suites/{suite_id}", response_model=SuiteOut)
def read_suite(suite_id: int, db: Session = Depends(get_db)):
    return _out(db, get_suite(db, suite_id))


@router.put("/suites/{suite_id}", response_model=SuiteOut)
def update_suite(suite_id: int, body: SuiteIn, db: Session = Depends(get_db)):
    s = get_suite(db, suite_id)
    _check(db, s.project_id, body, suite_id)
    for k, v in body.model_dump().items():
        setattr(s, k, v)
    db.commit()
    return _out(db, s)


@router.delete("/suites/{suite_id}", status_code=204)
def delete_suite(suite_id: int, db: Session = Depends(get_db)):
    s = get_suite(db, suite_id)
    n = db.query(Schedule).filter(Schedule.suite_id == suite_id).count()
    if n:
        raise HTTPException(400, f"有 {n} 个定时任务引用该套件，请先删除定时任务")
    # SQLite 会复用被删除的最大 id，先解除历史执行的关联（title 仍保留套件名）
    db.query(Run).filter(Run.suite_id == suite_id).update({Run.suite_id: None})
    db.delete(s)
    db.commit()


def run_suite_now(db: Session, s: Suite, environment_id: int | None, *, trigger="suite",
                  schedule_id: int | None = None, title: str | None = None) -> Run:
    env = resolve_env(db, s.project_id, environment_id)
    nodeids, _ = expand(db, s.project_id, s.nodeids, s.marker_expr)
    return enqueue_run(db, s.project_id, env, nodeids, trigger=trigger, title=title or s.name,
                       suite_id=s.id, schedule_id=schedule_id)


@router.post("/suites/{suite_id}/run", response_model=RunOut, status_code=201)
def run_suite(suite_id: int, body: SuiteRunIn, db: Session = Depends(get_db)):
    return run_suite_now(db, get_suite(db, suite_id), body.environment_id)
