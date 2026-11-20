from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sentinel.backend import settings
from sentinel.backend.api import cases, dashboard, elements, notifications, projects, runs, schedules, scripts, suites
from sentinel.backend.db import init_db
from sentinel.backend.services import notifier, scheduler
from sentinel.backend.services.recorder import recorder
from sentinel.backend.services.runner import runner


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    runner.mark_interrupted()
    recorder.mark_interrupted()
    if notifier.on_run_finished not in runner.listeners:
        runner.listeners.append(notifier.on_run_finished)
    runner.start()
    scheduler.start()
    yield
    scheduler.shutdown()
    recorder.stop()


app = FastAPI(title="Web3Rec 测试平台", lifespan=lifespan)
app.include_router(projects.router)
app.include_router(cases.router)
app.include_router(runs.router)
for _r in (suites, schedules, notifications, elements, scripts, dashboard):
    app.include_router(_r.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "running_run_id": runner.current_id}


# ── 前端静态文件（make build 之后存在）──
if settings.FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=settings.FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith(("api/", "ws/")):
            raise HTTPException(404)
        file = settings.FRONTEND_DIST / full_path
        if full_path and file.is_file():
            return FileResponse(file)
        return FileResponse(settings.FRONTEND_DIST / "index.html")
