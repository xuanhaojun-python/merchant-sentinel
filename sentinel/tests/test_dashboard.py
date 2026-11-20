from sentinel.tests.conftest import wait_run

N = "tests/test_sample.py::"


def test_dashboard(client, project, env):
    client.post(f"/api/projects/{project['id']}/cases/sync")
    for names in (["test_pass", "test_fail"], ["test_pass", "test_skip"]):
        r = client.post("/api/runs", json={"project_id": project["id"], "environment_id": env["id"],
                                           "nodeids": [N + n for n in names]}).json()
        wait_run(client, r["id"])

    d = client.get(f"/api/projects/{project['id']}/dashboard", params={"days": 7}).json()
    assert len(d["trend"]) == 7
    today = d["trend"][-1]
    assert (today["runs"], today["passed"], today["failed"], today["skipped"]) == (2, 2, 1, 1)
    k = d["kpi"]
    assert k["case_count"] == 5 and k["run_count"] == 2 and k["pass_rate"] == 66.7
    assert k["executed_case_count"] == 2
    assert d["status_dist"] == {"failed": 1, "passed": 1}
    assert d["priority_dist"]["none"] == 5
    assert d["module_dist"] == {"slow": 1}
    assert d["top_failed"][0]["name"] == "test_fail"
    assert client.get(f"/api/projects/{project['id']}/dashboard", params={"days": 0}).status_code == 422
