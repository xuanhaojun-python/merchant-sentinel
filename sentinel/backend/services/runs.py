"""创建执行记录并提交给执行器（手动 / 套件 / 定时任务 / 脚本共用）。"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from sentinel.backend.models import Environment, Run
from sentinel.backend.services.runner import runner


def resolve_env(db: Session, project_id: int, environment_id: int | None) -> Environment | None:
    if environment_id is None:
        return None
    env = db.get(Environment, environment_id)
    if env is None or env.project_id != project_id:
        raise HTTPException(400, "环境不存在或不属于该项目")
    return env


def enqueue_run(db: Session, project_id: int, env: Environment | None, nodeids: list[str], *,
                trigger: str = "manual", title: str = "", suite_id: int | None = None,
                schedule_id: int | None = None) -> Run:
    if not nodeids:
        raise HTTPException(400, "没有可执行的用例")
    run = Run(project_id=project_id, environment_id=env.id if env else None,
              environment_name=env.name if env else "", selected_nodeids=list(nodeids), status="queued",
              trigger=trigger, title=title, suite_id=suite_id, schedule_id=schedule_id)
    db.add(run)
    db.commit()
    runner.submit(run.id)
    return run
