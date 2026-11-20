from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from sentinel.backend.api.projects import get_project
from sentinel.backend.api.suites import get_suite
from sentinel.backend.db import get_db
from sentinel.backend.models import Environment, NotifyChannel, Run, Schedule
from sentinel.backend.schemas import RunOut, ScheduleIn, ScheduleOut
from sentinel.backend.services import scheduler

router = APIRouter(prefix="/api", tags=["schedules"])


def _get(db: Session, schedule_id: int) -> Schedule:
    sch = db.get(Schedule, schedule_id)
    if sch is None:
        raise HTTPException(404, "定时任务不存在")
    return sch


def _out(db: Session, sch: Schedule) -> ScheduleOut:
    out = ScheduleOut.model_validate(sch)
    out.suite_name = sch.suite.name if sch.suite else ""
    env = db.get(Environment, sch.environment_id) if sch.environment_id else None
    out.environment_name = env.name if env else ""
    out.next_run_at = scheduler.next_run_at(sch.id)
    last = db.get(Run, sch.last_run_id) if sch.last_run_id else None
    out.last_status = last.status if last else None
    return out


def _validate(db: Session, project_id: int, body: ScheduleIn) -> None:
    scheduler.parse_cron(body.cron)
    if get_suite(db, body.suite_id).project_id != project_id:
        raise HTTPException(400, "套件不属于该项目")
    if body.environment_id is not None:
        env = db.get(Environment, body.environment_id)
        if env is None or env.project_id != project_id:
            raise HTTPException(400, "环境不存在或不属于该项目")
    if body.channel_ids:
        found = db.query(NotifyChannel.id).filter(NotifyChannel.id.in_(body.channel_ids)).count()
        if found != len(set(body.channel_ids)):
            raise HTTPException(400, "通知渠道不存在")


@router.get("/projects/{project_id}/schedules", response_model=list[ScheduleOut])
def list_schedules(project_id: int, db: Session = Depends(get_db)):
    get_project(db, project_id)
    return [_out(db, s) for s in db.query(Schedule).filter(Schedule.project_id == project_id).order_by(Schedule.id)]


@router.post("/projects/{project_id}/schedules", response_model=ScheduleOut, status_code=201)
def create_schedule(project_id: int, body: ScheduleIn, db: Session = Depends(get_db)):
    get_project(db, project_id)
    _validate(db, project_id, body)
    sch = Schedule(project_id=project_id, **body.model_dump())
    db.add(sch)
    db.commit()
    scheduler.sync_job(sch)
    return _out(db, sch)


@router.put("/schedules/{schedule_id}", response_model=ScheduleOut)
def update_schedule(schedule_id: int, body: ScheduleIn, db: Session = Depends(get_db)):
    sch = _get(db, schedule_id)
    _validate(db, sch.project_id, body)
    for k, v in body.model_dump().items():
        setattr(sch, k, v)
    db.commit()
    scheduler.sync_job(sch)
    return _out(db, sch)


@router.post("/schedules/{schedule_id}/toggle", response_model=ScheduleOut)
def toggle_schedule(schedule_id: int, db: Session = Depends(get_db)):
    sch = _get(db, schedule_id)
    sch.enabled = not sch.enabled
    db.commit()
    scheduler.sync_job(sch)
    return _out(db, sch)


@router.delete("/schedules/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    sch = _get(db, schedule_id)
    scheduler.remove_job(sch.id)
    db.query(Run).filter(Run.schedule_id == schedule_id).update({Run.schedule_id: None})
    db.delete(sch)
    db.commit()


@router.post("/schedules/{schedule_id}/trigger", response_model=RunOut, status_code=201)
def trigger_now(schedule_id: int, db: Session = Depends(get_db)):
    _get(db, schedule_id)
    run_id = scheduler.fire(schedule_id)
    if run_id is None:
        raise HTTPException(400, "触发失败：套件没有可执行的用例")
    return db.get(Run, run_id)


@router.get("/cron/preview", response_model=list)
def cron_preview(expr: str, n: int = 5):
    return scheduler.next_fire_times(expr, min(max(n, 1), 20))
