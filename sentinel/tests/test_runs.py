from sentinel.tests.conftest import wait_run

N = "tests/test_sample.py::"


def _run(client, project, env, names):
    resp = client.post("/api/runs", json={"project_id": project["id"], "environment_id": env["id"] if env else None,
                                          "nodeids": [N + n for n in names]})
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_mixed_run_results(client, project, env):
    client.post(f"/api/projects/{project['id']}/cases/sync")
    run = wait_run(client, _run(client, project, env, ["test_pass", "test_fail", "test_skip", "test_env"])["id"])

    assert run["status"] == "failed" and run["exit_code"] == 1
    assert (run["total"], run["passed"], run["failed"], run["skipped"]) == (4, 2, 1, 1)
    assert run["environment_name"] == "TEST"
    res = {r["nodeid"].split("::")[1]: r for r in run["results"]}
    assert res["test_pass"]["steps"] == ["[Sample] 第一步", "[Sample] 第二步"]
    assert res["test_pass"]["test_case_id"] is not None
    assert "故意失败" in res["test_fail"]["error"]
    assert res["test_fail"]["screenshot"] == "screenshots/test_fail.png"
    assert "故意跳过" in res["test_skip"]["error"]
    assert res["test_env"]["outcome"] == "passed"  # 环境变量已注入

    shot = client.get(f"/api/runs/{run['id']}/screenshots/test_fail.png")
    assert shot.status_code == 200 and shot.headers["content-type"] == "image/png"
    assert client.get(f"/api/runs/{run['id']}/screenshots/..%2Foutput.log").status_code == 404

    log = client.get(f"/api/runs/{run['id']}/log").text
    assert "4 items" in log or "collected 4" in log


def test_all_passed_run(client, project, env):
    run = wait_run(client, _run(client, project, env, ["test_pass"])["id"])
    assert run["status"] == "passed" and run["passed"] == 1


def test_unknown_nodeid_is_error(client, project, env):
    run = wait_run(client, _run(client, project, env, ["test_does_not_exist"])["id"])
    assert run["status"] == "error"
    assert run["message"]


def test_stop_running_and_queued(client, project, env):
    slow = _run(client, project, env, ["test_slow"])
    queued = _run(client, project, env, ["test_pass"])
    wait_run(client, slow["id"], until=("running",))

    assert client.post(f"/api/runs/{queued['id']}/stop").json()["status"] == "stopped"
    client.post(f"/api/runs/{slow['id']}/stop")
    run = wait_run(client, slow["id"], timeout=15)
    assert run["status"] == "stopped"
    assert wait_run(client, queued["id"])["status"] == "stopped"
    assert client.post(f"/api/runs/{slow['id']}/stop").status_code == 400


def test_websocket_streams_log_until_end(client, project, env):
    run = _run(client, project, env, ["test_pass"])
    chunks, end = [], None
    with client.websocket_connect(f"/ws/runs/{run['id']}/log") as ws:
        while True:
            msg = ws.receive_json()
            if msg["type"] == "log":
                chunks.append(msg["data"])
            elif msg["type"] == "end":
                end = msg
                break
    assert end["status"] == "passed"
    assert "test_sample.py" in "".join(chunks)


def test_list_runs_pagination_and_filter(client, project, env):
    for _ in range(3):
        wait_run(client, _run(client, project, env, ["test_pass"])["id"])
    page = client.get("/api/runs", params={"project_id": project["id"], "page_size": 2}).json()
    assert page["total"] == 3 and len(page["items"]) == 2
    assert page["items"][0]["id"] > page["items"][1]["id"]
    finished = client.get("/api/runs", params={"project_id": project["id"], "finished": True}).json()
    assert finished["total"] == 3


def test_mark_interrupted(client, project):
    from sentinel.backend.db import SessionLocal
    from sentinel.backend.models import Run
    from sentinel.backend.services.runner import Runner
    with SessionLocal() as db:
        r = Run(project_id=project["id"], status="running", selected_nodeids=[N + "test_pass"])
        db.add(r)
        db.commit()
        rid = r.id
    assert Runner.mark_interrupted() >= 1
    assert client.get(f"/api/runs/{rid}").json()["status"] == "interrupted"


def test_delete_run(client, project, env):
    run = wait_run(client, _run(client, project, env, ["test_pass"])["id"])
    assert client.delete(f"/api/runs/{run['id']}").status_code == 204
    assert client.get(f"/api/runs/{run['id']}").status_code == 404
