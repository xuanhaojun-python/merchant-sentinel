def _sync(client, pid):
    resp = client.post(f"/api/projects/{pid}/cases/sync")
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_sync_adds_cases_with_metadata(client, project):
    result = _sync(client, project["id"])
    assert result == {"added": 5, "updated": 0, "removed": 0, "errors": []}

    cases = {c["name"]: c for c in client.get(f"/api/projects/{project['id']}/cases").json()}
    assert set(cases) == {"test_pass", "test_fail", "test_skip", "test_env", "test_slow"}
    assert cases["test_pass"]["nodeid"] == "tests/test_sample.py::test_pass"
    assert cases["test_pass"]["file"] == "tests/test_sample.py"
    assert cases["test_pass"]["markers"] == ["smoke"]
    assert cases["test_pass"]["docstring"] == "总是通过"


def test_resync_marks_removed_and_keeps_remark(client, project, sample_dir):
    pid = project["id"]
    _sync(client, pid)
    case = next(c for c in client.get(f"/api/projects/{pid}/cases").json() if c["name"] == "test_pass")
    client.put(f"/api/cases/{case['id']}", json={"remark": "我的备注", "tags": ["核心"]})

    f = sample_dir / "tests" / "test_sample.py"
    f.write_text(f.read_text(encoding="utf-8").replace("def test_skip", "def _removed_skip"), encoding="utf-8")
    result = _sync(client, pid)
    assert result["removed"] == 1 and result["added"] == 0

    active = {c["name"]: c for c in client.get(f"/api/projects/{pid}/cases").json()}
    assert "test_skip" not in active
    assert active["test_pass"]["remark"] == "我的备注" and active["test_pass"]["tags"] == ["核心"]
    removed = client.get(f"/api/projects/{pid}/cases", params={"status": "removed"}).json()
    assert [c["name"] for c in removed] == ["test_skip"]


def test_sync_reports_import_errors_without_removing(client, project, sample_dir):
    pid = project["id"]
    _sync(client, pid)
    (sample_dir / "tests" / "test_broken.py").write_text("import not_a_real_module\n", encoding="utf-8")
    result = _sync(client, pid)
    assert result["removed"] == 0
    assert len(result["errors"]) == 1 and "test_broken.py" in result["errors"][0]["file"]


def test_filter_cases(client, project):
    pid = project["id"]
    _sync(client, pid)
    smoke = client.get(f"/api/projects/{pid}/cases", params={"marker": "smoke"}).json()
    assert [c["name"] for c in smoke] == ["test_pass"]
    kw = client.get(f"/api/projects/{pid}/cases", params={"keyword": "总是"}).json()
    assert [c["name"] for c in kw] == ["test_pass"]
