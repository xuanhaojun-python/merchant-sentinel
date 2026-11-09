import os
import shutil
import tempfile
import time
from pathlib import Path

# 必须在导入 sentinel.backend 之前设置，确保使用临时数据库
_DATA = tempfile.mkdtemp(prefix="sentinel-test-")
os.environ["SENTINEL_DATA_DIR"] = _DATA

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

collect_ignore_glob = ["fixtures/*"]

SAMPLE = Path(__file__).parent / "fixtures" / "sample_project"


@pytest.fixture(scope="session")
def client():
    from sentinel.backend.main import app
    with TestClient(app) as c:
        yield c
    shutil.rmtree(_DATA, ignore_errors=True)


@pytest.fixture
def sample_dir(tmp_path):
    dst = tmp_path / "sample_project"
    shutil.copytree(SAMPLE, dst)
    return dst


_counter = iter(range(10_000))


@pytest.fixture
def project(client, sample_dir):
    resp = client.post("/api/projects", json={"name": f"sample-{next(_counter)}", "root_path": str(sample_dir)})
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def env(client, project):
    resp = client.post(f"/api/projects/{project['id']}/environments",
                       json={"name": "TEST", "base_url": "https://example.test"})
    assert resp.status_code == 201, resp.text
    return resp.json()


def wait_run(client, run_id, until=("passed", "failed", "error", "stopped", "interrupted"), timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        run = client.get(f"/api/runs/{run_id}").json()
        if run["status"] in until:
            return run
        time.sleep(0.2)
    raise AssertionError(f"run {run_id} 超时，最后状态 {run['status']}")
