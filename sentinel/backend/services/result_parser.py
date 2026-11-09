"""解析 pytest-json-report 输出为用例结果。"""
import json
from pathlib import Path


def _steps(stdout: str) -> list[str]:
    return [line.strip() for line in (stdout or "").splitlines() if line.strip().startswith("[")]


def _error(test: dict) -> str:
    for stage in ("setup", "call", "teardown"):
        info = test.get(stage) or {}
        if info.get("outcome") == "failed":
            return info.get("longrepr") or (info.get("crash") or {}).get("message", "")
    return ""


def _outcome(test: dict) -> str:
    outcome = test.get("outcome", "error")
    if outcome in ("passed", "failed", "skipped"):
        return outcome
    if outcome == "xfailed":
        return "skipped"
    if outcome == "xpassed":
        return "passed"
    return "error"


def _skip_reason(test: dict) -> str:
    for stage in ("setup", "call"):
        info = test.get(stage) or {}
        if info.get("outcome") == "skipped":
            return info.get("longrepr", "")
    return ""


def parse_report(report_file: Path, run_dir: Path) -> list[dict]:
    data = json.loads(report_file.read_text(encoding="utf-8"))
    results = []
    for test in data.get("tests", []):
        name = test["nodeid"].split("::")[-1]
        shot = run_dir / "screenshots" / f"{name}.png"
        outcome = _outcome(test)
        stdout = "".join((test.get(s) or {}).get("stdout", "") for s in ("setup", "call", "teardown"))
        results.append({
            "nodeid": test["nodeid"],
            "outcome": outcome,
            "duration": round(sum((test.get(s) or {}).get("duration", 0) for s in ("setup", "call", "teardown")), 2),
            "steps": _steps(stdout),
            "error": _error(test) if outcome in ("failed", "error") else _skip_reason(test) if outcome == "skipped" else "",
            "screenshot": f"screenshots/{shot.name}" if shot.exists() else "",
        })
    return results
