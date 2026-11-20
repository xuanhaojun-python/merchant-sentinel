import sys
import time

from sentinel.backend.services.recorder import record_file, recorder
from sentinel.tests.conftest import wait_run

SCRIPT = "def test_recorded():\n    print('[Script] ok')\n    assert True\n"


def _create(client, project, content=SCRIPT, name="demo"):
    resp = client.post(f"/api/projects/{project['id']}/scripts", json={"name": name, "content": content})
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_script_run_and_export(client, project, env, sample_dir):
    s = _create(client, project)
    run = client.post(f"/api/scripts/{s['id']}/run", json={"environment_id": env["id"]}).json()
    assert run["trigger"] == "script" and run["title"] == "脚本：demo"
    run = wait_run(client, run["id"])
    assert run["status"] == "passed" and run["results"][0]["steps"] == ["[Script] ok"]
    assert client.get(f"/api/scripts/{s['id']}").json()["last_status"] == "passed"

    r = client.post(f"/api/scripts/{s['id']}/export", json={"filename": "demo_flow"})
    assert r.status_code == 200, r.text and r.json()["added"] == 1
    assert (sample_dir / "tests" / "recorded" / "test_demo_flow.py").read_text() == SCRIPT
    cases = client.get(f"/api/projects/{project['id']}/cases", params={"keyword": "test_recorded"}).json()
    assert [c["nodeid"] for c in cases] == ["tests/recorded/test_demo_flow.py::test_recorded"]

    other = _create(client, project, name="other")
    assert client.post(f"/api/scripts/{other['id']}/export", json={"filename": "demo_flow"}).status_code == 409
    assert client.post(f"/api/scripts/{other['id']}/export?overwrite=true", json={"filename": "demo_flow"}).status_code == 200
    assert client.post(f"/api/scripts/{other['id']}/export", json={"filename": "../evil"}).status_code == 422


def test_empty_script_cannot_run(client, project):
    s = _create(client, project, content="")
    assert client.post(f"/api/scripts/{s['id']}/run", json={}).status_code == 400


def test_recording_flow(client, project, monkeypatch):
    """用假的 codegen（写文件后等待被停止）验证录制状态流转。"""
    def fake_cmd(script_id, url, device=""):
        code = (f"import pathlib,time; pathlib.Path({str(record_file(script_id))!r}).write_text({SCRIPT!r}); "
                "time.sleep(30)")
        return [sys.executable, "-c", code]
    monkeypatch.setattr(recorder, "build_cmd", fake_cmd)

    s = client.post(f"/api/projects/{project['id']}/recorder/start", json={"name": "rec", "url": "https://x.test"}).json()
    assert s["status"] == "recording" and s["source"] == "recorded"
    assert client.get("/api/recorder").json() == {"recording": True, "script_id": s["id"]}
    assert client.post(f"/api/projects/{project['id']}/recorder/start", json={"name": "rec2"}).status_code == 400
    assert client.delete(f"/api/scripts/{s['id']}").status_code == 400

    deadline = time.time() + 10
    while time.time() < deadline and "test_recorded" not in client.get(f"/api/scripts/{s['id']}").json()["content"]:
        time.sleep(0.1)
    assert client.post("/api/recorder/stop").status_code == 200
    while time.time() < deadline and client.get(f"/api/scripts/{s['id']}").json()["status"] == "recording":
        time.sleep(0.1)
    done = client.get(f"/api/scripts/{s['id']}").json()
    assert done["status"] == "ready" and done["content"] == SCRIPT
    assert client.get("/api/recorder").json()["recording"] is False
    assert client.post("/api/recorder/stop").status_code == 400
