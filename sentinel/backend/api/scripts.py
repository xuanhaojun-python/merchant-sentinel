from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from sentinel.backend import settings
from sentinel.backend.api.projects import get_project
from sentinel.backend.db import get_db
from sentinel.backend.models import Environment, Run, Script
from sentinel.backend.schemas import RecordIn, RunOut, ScriptExportIn, ScriptIn, ScriptOut, SuiteRunIn, SyncResult
from sentinel.backend.services.recorder import recorder
from sentinel.backend.services.runs import enqueue_run, resolve_env
from sentinel.backend.services.scanner import ScanError, sync_cases

router = APIRouter(prefix="/api", tags=["scripts"])

EXPORT_DIR = "tests/recorded"


def _get(db: Session, script_id: int) -> Script:
    s = db.get(Script, script_id)
    if s is None:
        raise HTTPException(404, "脚本不存在")
    return s


def _out(db: Session, s: Script) -> ScriptOut:
    out = ScriptOut.model_validate(s)
    if s.status == "recording":
        out.content = recorder.live_content(s.id) or s.content
    last = db.get(Run, s.last_run_id) if s.last_run_id else None
    out.last_status = last.status if last else None
    return out


@router.get("/projects/{project_id}/scripts", response_model=list[ScriptOut])
def list_scripts(project_id: int, db: Session = Depends(get_db)):
    get_project(db, project_id)
    return [_out(db, s) for s in db.query(Script).filter(Script.project_id == project_id).order_by(Script.id.desc())]


@router.post("/projects/{project_id}/scripts", response_model=ScriptOut, status_code=201)
def create_script(project_id: int, body: ScriptIn, db: Session = Depends(get_db)):
    get_project(db, project_id)
    s = Script(project_id=project_id, source="manual", status="ready", **body.model_dump())
    db.add(s)
    db.commit()
    return _out(db, s)


@router.get("/scripts/{script_id}", response_model=ScriptOut)
def read_script(script_id: int, db: Session = Depends(get_db)):
    return _out(db, _get(db, script_id))


@router.put("/scripts/{script_id}", response_model=ScriptOut)
def update_script(script_id: int, body: ScriptIn, db: Session = Depends(get_db)):
    s = _get(db, script_id)
    if s.status == "recording":
        raise HTTPException(400, "录制中的脚本不能编辑")
    s.name, s.description, s.content = body.name, body.description, body.content
    if s.content.strip() and s.status == "failed":
        s.status, s.message = "ready", ""
    db.commit()
    return _out(db, s)


@router.delete("/scripts/{script_id}", status_code=204)
def delete_script(script_id: int, db: Session = Depends(get_db)):
    s = _get(db, script_id)
    if s.status == "recording":
        raise HTTPException(400, "录制中的脚本不能删除，请先结束录制")
    db.delete(s)
    db.commit()


# ── 录制 ──
@router.get("/recorder")
def recorder_status():
    return {"recording": recorder.current_id is not None, "script_id": recorder.current_id}


@router.post("/projects/{project_id}/recorder/start", response_model=ScriptOut, status_code=201)
def start_recording(project_id: int, body: RecordIn, db: Session = Depends(get_db)):
    get_project(db, project_id)
    url = body.url.strip()
    if not url and body.environment_id:
        env = db.get(Environment, body.environment_id)
        url = env.base_url if env and env.project_id == project_id else ""
    s = Script(project_id=project_id, name=body.name, description=body.description, source="recorded",
               url=url, status="recording")
    db.add(s)
    db.commit()
    try:
        recorder.start(s.id, url, body.device.strip())
    except HTTPException:
        db.delete(s)
        db.commit()
        raise
    return _out(db, s)


@router.post("/recorder/stop")
def stop_recording():
    if not recorder.stop():
        raise HTTPException(400, "当前没有进行中的录制")
    return {"ok": True}


# ── 执行 / 导出 ──
def _script_file(s: Script) -> Path:
    d = settings.SCRIPTS_DIR / f"script_{s.id}"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"test_script_{s.id}.py"
    f.write_text(s.content, encoding="utf-8")
    return f


@router.post("/scripts/{script_id}/run", response_model=RunOut, status_code=201)
def run_script(script_id: int, body: SuiteRunIn, db: Session = Depends(get_db)):
    s = _get(db, script_id)
    if s.status != "ready" or not s.content.strip():
        raise HTTPException(400, "脚本为空或仍在录制中")
    env = resolve_env(db, s.project_id, body.environment_id)
    run = enqueue_run(db, s.project_id, env, [str(_script_file(s))], trigger="script", title=f"脚本：{s.name}")
    s.last_run_id = run.id
    db.commit()
    return run


@router.post("/scripts/{script_id}/export", response_model=SyncResult)
def export_script(script_id: int, body: ScriptExportIn, overwrite: bool = False, db: Session = Depends(get_db)):
    """导出到工程 tests/recorded/test_<filename>.py 并同步用例。"""
    s = _get(db, script_id)
    if not s.content.strip():
        raise HTTPException(400, "脚本内容为空")
    project = get_project(db, s.project_id)
    rel = f"{EXPORT_DIR}/test_{body.filename.removeprefix('test_')}.py"
    target = Path(project.root_path) / rel
    if target.exists() and not overwrite and s.exported_path != rel:
        raise HTTPException(409, f"{rel} 已存在")
    target.parent.mkdir(parents=True, exist_ok=True)
    init = target.parent / "__init__.py"
    if (target.parent.parent / "__init__.py").exists() and not init.exists():
        init.write_text("", encoding="utf-8")  # tests/ 是包时，子目录也需要是包
    target.write_text(s.content, encoding="utf-8")
    s.exported_path = rel
    db.commit()
    try:
        return sync_cases(db, project)
    except ScanError as exc:
        raise HTTPException(400, f"已导出到 {rel}，但同步用例失败：{exc}")
