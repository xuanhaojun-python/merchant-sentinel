from sentinel.tests.conftest import wait_run


def _setup(client, project):
    client.post(f"/api/projects/{project['id']}/cases/sync")
    return client.post(f"/api/projects/{project['id']}/suites", json={"name": "s", "marker_expr": "smoke"}).json()


def test_schedule_lifecycle(client, project, env):
    suite = _setup(client, project)
    url = f"/api/projects/{project['id']}/schedules"
    body = {"name": "夜间", "suite_id": suite["id"], "environment_id": env["id"], "cron": "0 2 * * *"}

    assert client.post(url, json={**body, "cron": "every day"}).status_code == 400
    sch = client.post(url, json=body).json()
    assert sch["next_run_at"] and sch["next_run_at"][11:16] == "02:00"
    assert sch["suite_name"] == "s" and sch["environment_name"] == "TEST"

    off = client.post(f"/api/schedules/{sch['id']}/toggle").json()
    assert off["enabled"] is False and off["next_run_at"] is None

    run = client.post(f"/api/schedules/{sch['id']}/trigger").json()
    assert run["trigger"] == "schedule" and run["schedule_id"] == sch["id"]
    assert wait_run(client, run["id"])["status"] == "passed"
    listed = client.get(url).json()[0]
    assert listed["last_run_id"] == run["id"] and listed["last_status"] == "passed"

    # 被定时任务引用的套件不能删
    assert client.delete(f"/api/suites/{suite['id']}").status_code == 400
    assert client.delete(f"/api/schedules/{sch['id']}").status_code == 204
    assert client.delete(f"/api/suites/{suite['id']}").status_code == 204


def test_cron_preview(client):
    times = client.get("/api/cron/preview", params={"expr": "*/15 * * * *", "n": 3}).json()
    assert len(times) == 3 and all(t[14:16] in ("00", "15", "30", "45") for t in times)
    assert client.get("/api/cron/preview", params={"expr": "61 * * * *"}).status_code == 400
