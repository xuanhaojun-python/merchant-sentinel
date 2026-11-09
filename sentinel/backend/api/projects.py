import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from sentinel.backend import settings
from sentinel.backend.db import get_db
from sentinel.backend.models import Environment, Project, Run, TestCase
from sentinel.backend.schemas import EnvironmentIn, EnvironmentOut, ProjectIn, ProjectOut

router = APIRouter(prefix="/api", tags=["projects"])

PYTEST_MARKERS = ("pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini", "conftest.py", "tests")


def _validate_root(path: str) -> str:
    p = Path(path).expanduser()
    if not p.is_dir():
        raise HTTPException(400, f"目录不存在：{path}")
    if not any((p / m).exists() for m in PYTEST_MARKERS):
        raise HTTPException(400, f"不是 pytest 工程（未找到 {' / '.join(PYTEST_MARKERS)}）：{path}")
    return str(p.resolve())


def get_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "项目不存在")
    return project


def _out(db: Session, p: Project) -> ProjectOut:
    out = ProjectOut.model_validate(p)
    out.case_count = db.query(func.count(TestCase.id)).filter(TestCase.project_id == p.id, TestCase.status == "active").scalar()
    out.env_count = db.query(func.count(Environment.id)).filter(Environment.project_id == p.id).scalar()
    return out


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return [_out(db, p) for p in db.query(Project).order_by(Project.id)]


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectIn, db: Session = Depends(get_db)):
    if db.query(Project).filter(Project.name == body.name).first():
        raise HTTPException(400, "项目名称已存在")
    p = Project(name=body.name, description=body.description, root_path=_validate_root(body.root_path))
    db.add(p)
    db.commit()
    return _out(db, p)


@router.get("/projects/{project_id}", response_model=ProjectOut)
def read_project(project_id: int, db: Session = Depends(get_db)):
    return _out(db, get_project(db, project_id))


@router.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, body: ProjectIn, db: Session = Depends(get_db)):
    p = get_project(db, project_id)
    dup = db.query(Project).filter(Project.name == body.name, Project.id != project_id).first()
    if dup:
        raise HTTPException(400, "项目名称已存在")
    p.name, p.description, p.root_path = body.name, body.description, _validate_root(body.root_path)
    db.commit()
    return _out(db, p)


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    p = get_project(db, project_id)
    if db.query(Run).filter(Run.project_id == project_id, Run.status.in_(("queued", "running"))).first():
        raise HTTPException(400, "项目有正在执行或排队的任务，请先停止")
    run_ids = [r.id for r in p.runs]
    db.delete(p)
    db.commit()
    for rid in run_ids:
        shutil.rmtree(settings.run_dir(rid), ignore_errors=True)


# ── Environment ──
def _clear_default(db: Session, project_id: int, keep_id: int | None = None) -> None:
    q = db.query(Environment).filter(Environment.project_id == project_id, Environment.is_default.is_(True))
    for e in q:
        if e.id != keep_id:
            e.is_default = False


@router.get("/projects/{project_id}/environments", response_model=list[EnvironmentOut])
def list_envs(project_id: int, db: Session = Depends(get_db)):
    get_project(db, project_id)
    return db.query(Environment).filter(Environment.project_id == project_id).order_by(Environment.id).all()


@router.post("/projects/{project_id}/environments", response_model=EnvironmentOut, status_code=201)
def create_env(project_id: int, body: EnvironmentIn, db: Session = Depends(get_db)):
    get_project(db, project_id)
    first = not db.query(Environment).filter(Environment.project_id == project_id).first()
    env = Environment(project_id=project_id, **body.model_dump())
    env.is_default = body.is_default or first
    if env.is_default:
        _clear_default(db, project_id)
    db.add(env)
    db.commit()
    return env


@router.put("/environments/{env_id}", response_model=EnvironmentOut)
def update_env(env_id: int, body: EnvironmentIn, db: Session = Depends(get_db)):
    env = db.get(Environment, env_id)
    if env is None:
        raise HTTPException(404, "环境不存在")
    for k, v in body.model_dump().items():
        setattr(env, k, v)
    if env.is_default:
        _clear_default(db, env.project_id, keep_id=env.id)
    db.commit()
    return env


@router.delete("/environments/{env_id}", status_code=204)
def delete_env(env_id: int, db: Session = Depends(get_db)):
    env = db.get(Environment, env_id)
    if env is None:
        raise HTTPException(404, "环境不存在")
    db.delete(env)
    db.commit()
