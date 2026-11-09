"""执行器：单 worker 队列，子进程运行 pytest，日志写入 run_dir/output.log。"""
import os
import queue
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime

from sentinel.backend import settings
from sentinel.backend.db import SessionLocal
from sentinel.backend.models import CaseResult, Environment, Run, TestCase
from sentinel.backend.services.result_parser import parse_report
from sentinel.backend.services.scanner import subprocess_env


class Runner:
    def __init__(self) -> None:
        self._queue: "queue.Queue[int]" = queue.Queue()
        self._lock = threading.Lock()
        self._current_id: int | None = None
        self._proc: subprocess.Popen | None = None
        self._stop_requested: set[int] = set()
        self._thread: threading.Thread | None = None

    # ── 生命周期 ──
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, name="sentinel-runner", daemon=True)
        self._thread.start()

    @staticmethod
    def mark_interrupted() -> int:
        """后端启动时，把遗留的 queued/running 记录标记为 interrupted。"""
        with SessionLocal() as db:
            runs = db.query(Run).filter(Run.status.in_(("queued", "running"))).all()
            for r in runs:
                r.status, r.message = "interrupted", "后端重启，执行被中断"
                r.finished_at = r.finished_at or datetime.now()
            db.commit()
            return len(runs)

    # ── 对外接口 ──
    def submit(self, run_id: int) -> None:
        self._queue.put(run_id)

    def stop(self, run_id: int) -> bool:
        with self._lock:
            if run_id == self._current_id and self._proc:
                self._stop_requested.add(run_id)
                self._terminate(self._proc)
                return True
        with SessionLocal() as db:  # 仍在排队：直接标记
            run = db.get(Run, run_id)
            if run and run.status == "queued":
                self._stop_requested.add(run_id)
                run.status, run.finished_at, run.message = "stopped", datetime.now(), "排队中被停止"
                db.commit()
                return True
        return False

    @property
    def current_id(self) -> int | None:
        return self._current_id

    # ── 内部 ──
    @staticmethod
    def _terminate(proc: subprocess.Popen) -> None:
        def kill():
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
            try:
                proc.wait(timeout=settings.STOP_GRACE_SECONDS)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        threading.Thread(target=kill, daemon=True).start()

    def _loop(self) -> None:
        while True:
            run_id = self._queue.get()
            try:
                if run_id in self._stop_requested:
                    continue
                self._execute(run_id)
            except Exception as exc:  # 保底：执行器线程不能挂
                with SessionLocal() as db:
                    run = db.get(Run, run_id)
                    if run:
                        run.status, run.message, run.finished_at = "error", f"执行器异常：{exc}", datetime.now()
                        db.commit()
            finally:
                with self._lock:
                    self._current_id, self._proc = None, None
                self._stop_requested.discard(run_id)

    def _execute(self, run_id: int) -> None:
        rdir = settings.run_dir(run_id)
        if rdir.exists():
            shutil.rmtree(rdir)
        (rdir / "screenshots").mkdir(parents=True)
        log_path, report_path = rdir / "output.log", rdir / "report.json"

        with SessionLocal() as db:
            run = db.get(Run, run_id)
            if run is None or run.status != "queued":
                return
            env = db.get(Environment, run.environment_id) if run.environment_id else None
            extra = {"MS_RUN_DIR": str(rdir)}
            if env:
                extra.update({"MS_BASE_URL": env.base_url, "MS_HEADLESS": "true" if env.headless else "false"})
                if env.email:
                    extra["MS_EMAIL"] = env.email
                if env.password:
                    extra["MS_PASSWORD"] = env.password
            cwd, nodeids = run.project.root_path, list(run.selected_nodeids)
            run.status, run.started_at = "running", datetime.now()
            db.commit()

        cmd = [sys.executable, "-m", "pytest", *nodeids, "-p", "no:cacheprovider",
               "--json-report", f"--json-report-file={report_path}", "--json-report-omit", "keywords", "log"]
        start = time.monotonic()
        with open(log_path, "w", encoding="utf-8") as log:
            log.write(f"$ {' '.join(cmd)}\n\n")
            log.flush()
            with self._lock:
                proc = subprocess.Popen(cmd, cwd=cwd, env=subprocess_env(extra), stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                                        bufsize=1, start_new_session=True)
                self._current_id, self._proc = run_id, proc
            for line in proc.stdout:
                log.write(line)
                log.flush()
            exit_code = proc.wait()
        self._finish(run_id, exit_code, time.monotonic() - start, report_path)

    def _finish(self, run_id: int, exit_code: int, duration: float, report_path) -> None:
        with SessionLocal() as db:
            run = db.get(Run, run_id)
            run.exit_code, run.duration, run.finished_at = exit_code, round(duration, 2), datetime.now()
            results = []
            if report_path.exists():
                try:
                    results = parse_report(report_path, settings.run_dir(run_id))
                except Exception as exc:
                    run.message = f"解析结果失败：{exc}"
            case_ids = {c.nodeid: c.id for c in db.query(TestCase).filter(TestCase.project_id == run.project_id)}
            for r in results:
                db.add(CaseResult(run_id=run_id, test_case_id=case_ids.get(r["nodeid"]), **r))
            run.total = len(results)
            run.passed = sum(r["outcome"] == "passed" for r in results)
            run.failed = sum(r["outcome"] in ("failed", "error") for r in results)
            run.skipped = sum(r["outcome"] == "skipped" for r in results)

            if run_id in self._stop_requested:
                run.status, run.message = "stopped", run.message or "用户手动停止"
            elif exit_code == 5:
                run.status, run.message = "error", "未收集到任何用例"
            elif not report_path.exists() or exit_code not in (0, 1):
                # 2=中断/收集错误 3=内部错误 4=参数错误 <0=被信号杀死
                run.status = "error"
                run.message = run.message or f"pytest 异常退出（exit={exit_code}），请查看日志"
            else:
                run.status = "passed" if exit_code == 0 and run.failed == 0 else "failed"
            db.commit()


runner = Runner()
