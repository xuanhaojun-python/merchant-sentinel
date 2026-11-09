"""pytest 插件：用 `-p sentinel.backend.services.collect_plugin` 加载，
把收集到的用例和导入错误写入环境变量 MS_COLLECT_FILE 指定的 JSON 文件。"""
import json
import os
from pathlib import Path

_errors: list[dict] = []


def pytest_collectreport(report):
    if report.failed:
        _errors.append({"file": str(report.nodeid or report.fspath), "error": str(report.longrepr)[-2000:]})


def pytest_collection_finish(session):
    out = os.getenv("MS_COLLECT_FILE")
    if not out:
        return
    root = Path(str(session.config.rootpath))
    cases = []
    for item in session.items:
        fn = getattr(item, "function", None)
        doc = (fn.__doc__ or "").strip() if fn else ""
        try:
            file = str(Path(str(item.path)).relative_to(root))
        except ValueError:
            file = str(item.path)
        cases.append({
            "nodeid": item.nodeid,
            "file": file,
            "name": item.name,
            "markers": sorted({m.name for m in item.iter_markers()} - {"parametrize", "usefixtures"}),
            "docstring": doc,
        })
    Path(out).write_text(json.dumps({"cases": cases, "errors": _errors}, ensure_ascii=False), encoding="utf-8")
