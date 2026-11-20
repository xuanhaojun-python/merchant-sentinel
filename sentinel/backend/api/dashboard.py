"""数据看板：按项目统计最近 N 天的执行情况。"""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from sentinel.backend.api.projects import get_project
from sentinel.backend.db import get_db
from sentinel.backend.models import FINISHED_STATUSES, CaseResult, Run, Schedule, Script, Suite, TestCase

router = APIRouter(prefix="/api", tags=["dashboard"])

PRIORITIES = ("p0", "p1", "p2")
# 不属于“业务模块”的标记
NON_MODULE = set(PRIORITIES) | {"fund", "e2e", "creates_data", "smoke", "security", "parametrize", "skip",
                                 "skipif", "xfail", "usefixtures", "filterwarnings"}


def priority_of(markers: list[str]) -> str:
    found = [p for p in PRIORITIES if p in (markers or [])]
    return found[0] if len(found) == 1 else "none"


def _rate(passed: int, total: int) -> float | None:
    return round(passed / total * 100, 1) if total else None


@router.get("/projects/{project_id}/dashboard")
def dashboard(project_id: int, days: int = Query(14, ge=1, le=180), db: Session = Depends(get_db)):
    get_project(db, project_id)
    since_day = date.today() - timedelta(days=days - 1)
    since = datetime.combine(since_day, datetime.min.time())

    cases = db.query(TestCase).filter(TestCase.project_id == project_id, TestCase.status == "active").all()
    case_by_id = {c.id: c for c in cases}
    priority = Counter(priority_of(c.markers) for c in cases)
    modules = Counter(m for c in cases for m in set(c.markers or []) if m not in NON_MODULE)

    runs = (db.query(Run).filter(Run.project_id == project_id, Run.created_at >= since,
                                 Run.status.in_(FINISHED_STATUSES)).order_by(Run.id).all())
    run_ids = [r.id for r in runs]
    results = db.query(CaseResult).filter(CaseResult.run_id.in_(run_ids)).all() if run_ids else []
    run_day = {r.id: r.created_at.date() for r in runs}

    # 每日趋势
    trend = {since_day + timedelta(days=i): {"runs": 0, "passed": 0, "failed": 0, "skipped": 0} for i in range(days)}
    for r in runs:
        trend[r.created_at.date()]["runs"] += 1
    for res in results:
        key = "passed" if res.outcome == "passed" else "skipped" if res.outcome == "skipped" else "failed"
        trend[run_day[res.run_id]][key] += 1
    trend_out = [{"date": d.isoformat(), **v, "pass_rate": _rate(v["passed"], v["passed"] + v["failed"])}
                 for d, v in sorted(trend.items())]

    # 用例维度
    per_case = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0, "durations": [], "last_failed_run": None})
    for res in results:
        st = per_case[res.nodeid]
        st["total"] += 1
        if res.outcome == "passed":
            st["passed"] += 1
        elif res.outcome in ("failed", "error"):
            st["failed"] += 1
            st["last_failed_run"] = max(st["last_failed_run"] or 0, res.run_id)
        if res.outcome != "skipped":
            st["durations"].append(res.duration)

    def row(nodeid, st):
        return {"nodeid": nodeid, "name": nodeid.split("::")[-1], "total": st["total"], "passed": st["passed"],
                "failed": st["failed"], "fail_rate": _rate(st["failed"], st["total"]),
                "avg_duration": round(sum(st["durations"]) / len(st["durations"]), 2) if st["durations"] else 0,
                "max_duration": round(max(st["durations"]), 2) if st["durations"] else 0,
                "last_failed_run": st["last_failed_run"]}

    rows = [row(n, st) for n, st in per_case.items()]
    top_failed = sorted((r for r in rows if r["failed"]), key=lambda r: (-r["failed"], -(r["fail_rate"] or 0)))[:10]
    slowest = sorted((r for r in rows if r["avg_duration"]), key=lambda r: -r["avg_duration"])[:10]
    flaky = sorted((r for r in rows if r["passed"] and r["failed"]), key=lambda r: -r["failed"])[:10]

    executed = sum(1 for res in results if res.outcome != "skipped")
    passed = sum(1 for res in results if res.outcome == "passed")
    covered = {res.test_case_id for res in results if res.test_case_id in case_by_id and res.outcome != "skipped"}
    last = db.query(Run).filter(Run.project_id == project_id).order_by(Run.id.desc()).first()

    return {
        "days": days,
        "kpi": {
            "case_count": len(cases),
            "suite_count": db.query(Suite).filter(Suite.project_id == project_id).count(),
            "schedule_enabled": db.query(Schedule).filter(Schedule.project_id == project_id, Schedule.enabled.is_(True)).count(),
            "script_count": db.query(Script).filter(Script.project_id == project_id).count(),
            "run_count": len(runs),
            "result_count": len(results),
            "pass_rate": _rate(passed, executed),
            "avg_run_duration": round(sum(r.duration for r in runs) / len(runs), 1) if runs else 0,
            "executed_case_count": len(covered),
            "exec_coverage": _rate(len(covered), len(cases)),
            "last_run": {"id": last.id, "status": last.status, "created_at": last.created_at} if last else None,
        },
        "trend": trend_out,
        "status_dist": dict(Counter(r.status for r in runs)),
        "trigger_dist": dict(Counter(r.trigger for r in runs)),
        "priority_dist": {p: priority.get(p, 0) for p in (*PRIORITIES, "none")},
        "module_dist": dict(modules.most_common()),
        "top_failed": top_failed,
        "slowest": slowest,
        "flaky": flaky,
    }
