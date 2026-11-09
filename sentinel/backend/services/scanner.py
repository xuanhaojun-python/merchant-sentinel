"""用例同步：在项目目录下运行 pytest --collect-only，与数据库比对。"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from sentinel.backend import settings
from sentinel.backend.models import Project, TestCase

PLUGIN = "sentinel.backend.services.collect_plugin"


class ScanError(Exception):
    pass


def subprocess_env(extra: dict | None = None) -> dict:
    env = os.environ.copy()
    # 让子进程能 import sentinel 包（插件）
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(settings.REPO_ROOT), env.get("PYTHONPATH")]))
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if extra:
        env.update(extra)
    return env


def collect(root_path: str, timeout: int = 120) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "collect.json"
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "-p", PLUGIN],
            cwd=root_path, env=subprocess_env({"MS_COLLECT_FILE": str(out)}),
            capture_output=True, text=True, timeout=timeout,
        )
        if not out.exists():
            raise ScanError(f"pytest 收集失败（exit={proc.returncode}）：\n{(proc.stdout + proc.stderr)[-3000:]}")
        return json.loads(out.read_text(encoding="utf-8"))


def sync_cases(db: Session, project: Project) -> dict:
    data = collect(project.root_path)
    now = datetime.now()
    existing = {c.nodeid: c for c in project.cases}
    seen, added, updated = set(), 0, 0
    for item in data["cases"]:
        seen.add(item["nodeid"])
        case = existing.get(item["nodeid"])
        if case is None:
            db.add(TestCase(project_id=project.id, synced_at=now, status="active", **item))
            added += 1
        else:
            changed = (case.markers != item["markers"] or case.docstring != item["docstring"]
                       or case.status != "active" or case.file != item["file"])
            case.markers, case.docstring, case.file, case.name = item["markers"], item["docstring"], item["file"], item["name"]
            case.status, case.synced_at = "active", now
            updated += int(changed)
    removed = 0
    error_files = {e["file"] for e in data["errors"]}
    for nodeid, case in existing.items():
        if nodeid not in seen and case.status != "removed":
            # 文件导入失败时不把其中用例标记为删除
            if any(nodeid.startswith(f) for f in error_files):
                continue
            case.status = "removed"
            removed += 1
    db.commit()
    return {"added": added, "updated": updated, "removed": removed, "errors": data["errors"]}
