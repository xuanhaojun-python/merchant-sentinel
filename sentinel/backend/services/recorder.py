"""脚本录制：在本机启动 `playwright codegen`（有界面），关闭录制窗口后把生成的 pytest 脚本存入 Script。

同一时间只允许一个录制会话。
"""
import os
import signal
import subprocess
import sys
import threading
from datetime import datetime

from fastapi import HTTPException

from sentinel.backend import settings
from sentinel.backend.db import SessionLocal
from sentinel.backend.models import Script
from sentinel.backend.services.scanner import subprocess_env


def record_file(script_id: int):
    return settings.SCRIPTS_DIR / f"record_{script_id}.py"


class Recorder:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._proc: subprocess.Popen | None = None
        self._script_id: int | None = None
        self._stopped = False

    @property
    def current_id(self) -> int | None:
        return self._script_id

    def build_cmd(self, script_id: int, url: str, device: str = "") -> list[str]:
        cmd = [sys.executable, "-m", "playwright", "codegen", "--target", "python-pytest",
               "-o", str(record_file(script_id))]
        if device:
            cmd += ["--device", device]
        if url:
            cmd.append(url)
        return cmd

    def start(self, script_id: int, url: str, device: str = "") -> None:
        with self._lock:
            if self._proc and self._proc.poll() is None:
                raise HTTPException(400, f"已有录制进行中（脚本 #{self._script_id}），请先结束")
            record_file(script_id).unlink(missing_ok=True)
            try:
                proc = subprocess.Popen(self.build_cmd(script_id, url, device), cwd=str(settings.REPO_ROOT),
                                        env=subprocess_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, encoding="utf-8", errors="replace", start_new_session=True)
            except OSError as exc:
                raise HTTPException(500, f"启动 playwright codegen 失败：{exc}")
            self._proc, self._script_id, self._stopped = proc, script_id, False
        threading.Thread(target=self._wait, args=(proc, script_id), daemon=True, name=f"recorder-{script_id}").start()

    def stop(self) -> bool:
        with self._lock:
            proc = self._proc
            if not proc or proc.poll() is not None:
                return False
            self._stopped = True
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        return True

    def live_content(self, script_id: int) -> str:
        f = record_file(script_id)
        return f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""

    def _wait(self, proc: subprocess.Popen, script_id: int) -> None:
        output = proc.stdout.read() if proc.stdout else ""
        code = proc.wait()
        content = self.live_content(script_id)
        with SessionLocal() as db:
            s = db.get(Script, script_id)
            if s is not None:
                s.content = content
                if content.strip():
                    s.status, s.message = "ready", ""
                else:
                    s.status = "failed"
                    s.message = ("未录制到任何操作" if code == 0 or self._stopped
                                 else f"codegen 异常退出（exit={code}）：{output[-1500:]}")
                s.updated_at = datetime.now()
                db.commit()
        record_file(script_id).unlink(missing_ok=True)
        with self._lock:
            if self._script_id == script_id:
                self._proc, self._script_id = None, None

    @staticmethod
    def mark_interrupted() -> None:
        with SessionLocal() as db:
            for s in db.query(Script).filter(Script.status == "recording"):
                content = record_file(s.id).read_text(encoding="utf-8") if record_file(s.id).exists() else ""
                s.content = content or s.content
                s.status = "ready" if s.content.strip() else "failed"
                s.message = "" if s.content.strip() else "后端重启，录制被中断"
            db.commit()


recorder = Recorder()
