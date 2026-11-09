import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from sentinel.backend import settings
from sentinel.backend.api.projects import get_project
from sentinel.backend.db import SessionLocal, get_db
from sentinel.backend.models import FINISHED_STATUSES, Environment, Run
from sentinel.backend.schemas import Page, RunCreate, RunDetail, RunOut
from sentinel.backend.services.runner import runner

router = APIRouter(tags=["runs"])


def _get_run(db: Session, run_id: int) -> Run:
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(404, "执行记录不存在")
    return run


@router.post("/api/runs", response_model=RunOut, status_code=201)
def create_run(body: RunCreate, db: Session = Depends(get_db)):
    get_project(db, body.project_id)
    env = None
    if body.environment_id is not None:
        env = db.get(Environment, body.environment_id)
        if env is None or env.project_id != body.project_id:
            raise HTTPException(400, "环境不存在或不属于该项目")
    run = Run(project_id=body.project_id, environment_id=env.id if env else None,
              environment_name=env.name if env else "", selected_nodeids=body.nodeids, status="queued")
    db.add(run)
    db.commit()
    runner.submit(run.id)
    return run


@router.get("/api/runs", response_model=Page)
def list_runs(project_id: int | None = None, status: str | None = None, finished: bool | None = None,
              page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    q = db.query(Run)
    if project_id:
        q = q.filter(Run.project_id == project_id)
    if status:
        q = q.filter(Run.status == status)
    if finished is not None:
        q = q.filter(Run.status.in_(FINISHED_STATUSES) if finished else Run.status.notin_(FINISHED_STATUSES))
    total = q.count()
    items = q.order_by(Run.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [RunOut.model_validate(r) for r in items], "total": total}


@router.get("/api/runs/{run_id}", response_model=RunDetail)
def read_run(run_id: int, db: Session = Depends(get_db)):
    return _get_run(db, run_id)


@router.post("/api/runs/{run_id}/stop", response_model=RunOut)
def stop_run(run_id: int, db: Session = Depends(get_db)):
    run = _get_run(db, run_id)
    if run.status not in ("queued", "running"):
        raise HTTPException(400, "该执行已结束")
    runner.stop(run_id)
    db.refresh(run)
    return run


@router.delete("/api/runs/{run_id}", status_code=204)
def delete_run(run_id: int, db: Session = Depends(get_db)):
    import shutil
    run = _get_run(db, run_id)
    if run.status in ("queued", "running"):
        raise HTTPException(400, "执行中的记录不能删除，请先停止")
    db.delete(run)
    db.commit()
    shutil.rmtree(settings.run_dir(run_id), ignore_errors=True)


@router.get("/api/runs/{run_id}/log", response_class=PlainTextResponse)
def read_log(run_id: int, db: Session = Depends(get_db)):
    _get_run(db, run_id)
    log = settings.run_dir(run_id) / "output.log"
    return log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""


@router.get("/api/runs/{run_id}/screenshots/{name}")
def read_screenshot(run_id: int, name: str):
    base = (settings.run_dir(run_id) / "screenshots").resolve()
    path = (base / name).resolve()
    if path.parent != base or not path.is_file():  # 防止路径穿越
        raise HTTPException(404, "截图不存在")
    return FileResponse(path, media_type="image/png")


@router.websocket("/ws/runs/{run_id}/log")
async def ws_log(ws: WebSocket, run_id: int):
    """推送日志增量：连上先补发已有内容，之后轮询文件，执行结束后发送 {"type":"end"} 并关闭。"""
    await ws.accept()
    log: Path = settings.run_dir(run_id) / "output.log"
    pos = 0
    try:
        while True:
            if log.exists():
                with open(log, encoding="utf-8", errors="replace") as f:
                    f.seek(pos)
                    chunk = f.read()
                    pos = f.tell()
                if chunk:
                    await ws.send_json({"type": "log", "data": chunk})
            with SessionLocal() as db:
                run = db.get(Run, run_id)
                status = run.status if run else "error"
            if status in FINISHED_STATUSES:
                if log.exists():  # 结束前再读一次尾部
                    with open(log, encoding="utf-8", errors="replace") as f:
                        f.seek(pos)
                        tail = f.read()
                    if tail:
                        await ws.send_json({"type": "log", "data": tail})
                await ws.send_json({"type": "end", "status": status})
                await ws.close()
                return
            await ws.send_json({"type": "status", "status": status})
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return
