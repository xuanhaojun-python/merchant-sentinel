from sentinel.tests.conftest import wait_run

N = "tests/test_sample.py::"


def _suite(client, project, **kw):
    body = {"name": "冒烟", "nodeids": [], "marker_expr": "", **kw}
    return client.post(f"/api/projects/{project['id']}/suites", json=body)


def test_suite_expand_and_run(client, project, env):
    client.post(f"/api/projects/{project['id']}/cases/sync")
    resp = _suite(client, project, nodeids=[N + "test_skip", N + "test_gone"], marker_expr="smoke")
    assert resp.status_code == 201, resp.text
    suite = resp.json()
    assert suite["case_count"] == 2                     # test_skip + smoke 匹配到的 test_pass
    assert suite["missing"] == [N + "test_gone"]

    prev = client.post(f"/api/projects/{project['id']}/suites/preview", json={"marker_expr": "not slow and not smoke"}).json()
    assert set(prev["nodeids"]) == {N + n for n in ("test_fail", "test_skip", "test_env")}

    run = client.post(f"/api/suites/{suite['id']}/run", json={"environment_id": env["id"]}).json()
    assert run["trigger"] == "suite" and run["suite_id"] == suite["id"] and run["title"] == "冒烟"
    run = wait_run(client, run["id"])
    assert run["status"] == "passed" and (run["passed"], run["skipped"]) == (1, 1)
    assert client.get(f"/api/suites/{suite['id']}").json()["last_run"]["id"] == run["id"]
    assert client.get("/api/runs", params={"suite_id": suite["id"]}).json()["total"] == 1


def test_suite_validation(client, project):
    assert _suite(client, project).status_code == 400                      # 什么都没选
    assert _suite(client, project, marker_expr="p0 and (").status_code == 400
    assert _suite(client, project, marker_expr="smoke").status_code == 201
    assert _suite(client, project, marker_expr="smoke").status_code == 400  # 重名


def test_suite_run_without_cases(client, project):
    suite = _suite(client, project, name="空", marker_expr="nothing_matches").json()
    assert client.post(f"/api/suites/{suite['id']}/run", json={}).status_code == 400
