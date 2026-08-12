import functools
from pathlib import Path
from datetime import datetime


def ensure_reports_dir() -> Path:
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    return reports


def timestamped_name(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}"


def screenshot_on_failure(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            page = kwargs.get("page") or kwargs.get("logged_in_page")
            if page is None:
                for a in args:
                    if hasattr(a, "screenshot"):
                        page = a
                        break
            if page:
                name = timestamped_name(func.__name__)
                path = ensure_reports_dir() / f"{name}.png"
                page.screenshot(path=str(path), full_page=True)
            raise
    return wrapper
