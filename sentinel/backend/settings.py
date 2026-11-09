import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent          # sentinel/
REPO_ROOT = PACKAGE_DIR.parent                                 # merchant-sentinel/
DATA_DIR = Path(os.getenv("SENTINEL_DATA_DIR", PACKAGE_DIR / "data")).resolve()
RUNS_DIR = DATA_DIR / "runs"
FRONTEND_DIST = PACKAGE_DIR / "frontend" / "dist"
HOST = os.getenv("SENTINEL_HOST", "127.0.0.1")
PORT = int(os.getenv("SENTINEL_PORT", "8082"))
STOP_GRACE_SECONDS = 5


def ensure_dirs() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def run_dir(run_id: int) -> Path:
    return RUNS_DIR / str(run_id)
