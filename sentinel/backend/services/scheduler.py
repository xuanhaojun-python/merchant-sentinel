"""定时任务：APScheduler 后台调度，数据库是唯一来源，增删改后调用 sync_job 同步。"""
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import HTTPException

from sentinel.backend.db import SessionLocal
from sentinel.backend.models import Schedule

_scheduler = BackgroundScheduler(job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 300})


def parse_cron(expr: str) -> CronTrigger:
    try:
        return CronTrigger.from_crontab(expr.strip())
    except ValueError as exc:
        raise HTTPException(400, f"cron 表达式不合法（需 5 段：分 时 日 月 周）：{exc}")


def next_fire_times(expr: str, n: int = 5) -> list[datetime]:
    trigger, out, prev = parse_cron(expr), [], None
    now = datetime.now().astimezone()
    for _ in range(n):
        nxt = trigger.get_next_fire_time(prev, prev or now)
        if nxt is None:
            break
        out.append(nxt.replace(tzinfo=None))
        prev = nxt
    return out


def _job_id(schedule_id: int) -> str:
    return f"schedule-{schedule_id}"


def fire(schedule_id: int) -> int | None:
    """触发一次定时任务（调度器线程 / 立即执行 共用），返回 run_id。"""
    from sentinel.backend.api.suites import run_suite_now  # 避免循环导入
    with SessionLocal() as db:
        sch = db.get(Schedule, schedule_id)
        if sch is None:
            return None
        try:
            run = run_suite_now(db, sch.suite, sch.environment_id, trigger="schedule", schedule_id=sch.id,
                                title=f"{sch.name}（{sch.suite.name}）")
        except HTTPException as exc:
            print(f"[scheduler] 定时任务 {schedule_id} 触发失败：{exc.detail}")
            return None
        sch.last_run_id, sch.last_run_at = run.id, datetime.now()
        db.commit()
        return run.id


def sync_job(sch: Schedule) -> None:
    job_id = _job_id(sch.id)
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)
    if sch.enabled:
        _scheduler.add_job(fire, parse_cron(sch.cron), args=[sch.id], id=job_id, replace_existing=True)


def remove_job(schedule_id: int) -> None:
    if _scheduler.get_job(_job_id(schedule_id)):
        _scheduler.remove_job(_job_id(schedule_id))


def next_run_at(schedule_id: int) -> datetime | None:
    job = _scheduler.get_job(_job_id(schedule_id))
    return job.next_run_time.replace(tzinfo=None) if job and job.next_run_time else None


def start() -> None:
    if not _scheduler.running:
        _scheduler.start()
    with SessionLocal() as db:
        for sch in db.query(Schedule).filter(Schedule.enabled.is_(True)):
            try:
                sync_job(sch)
            except HTTPException as exc:
                print(f"[scheduler] 跳过定时任务 {sch.id}：{exc.detail}")


def shutdown() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
