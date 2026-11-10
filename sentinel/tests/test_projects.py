def test_create_project_validates_root_path(client, tmp_path):
    resp = client.post("/api/projects", json={"name": "bad", "root_path": str(tmp_path / "nope")})
    assert resp.status_code == 400
    assert "目录不存在" in resp.json()["detail"]

    empty = tmp_path / "empty"
    empty.mkdir()
    resp = client.post("/api/projects", json={"name": "bad2", "root_path": str(empty)})
    assert resp.status_code == 400
    assert "不是 pytest 工程" in resp.json()["detail"]


def test_project_crud(client, project):
    pid = project["id"]
    assert any(p["id"] == pid for p in client.get("/api/projects").json())

    dup = client.post("/api/projects", json={"name": project["name"], "root_path": project["root_path"]})
    assert dup.status_code == 400

    resp = client.put(f"/api/projects/{pid}", json={"name": project["name"] + "-x", "description": "d",
                                                     "root_path": project["root_path"]})
    assert resp.status_code == 200 and resp.json()["description"] == "d"

    assert client.delete(f"/api/projects/{pid}").status_code == 204
    assert client.get(f"/api/projects/{pid}").status_code == 404


def test_environment_default_is_unique(client, project):
    pid = project["id"]
    first = client.post(f"/api/projects/{pid}/environments", json={"name": "SIT", "base_url": "https://a"}).json()
    assert first["is_default"] is True  # 第一个环境自动设为默认

    second = client.post(f"/api/projects/{pid}/environments",
                         json={"name": "UAT", "base_url": "https://b", "is_default": True}).json()
    envs = {e["name"]: e for e in client.get(f"/api/projects/{pid}/environments").json()}
    assert envs["UAT"]["is_default"] and not envs["SIT"]["is_default"]

    assert client.delete(f"/api/environments/{second['id']}").status_code == 204
    assert len(client.get(f"/api/projects/{pid}/environments").json()) == 1


def test_environment_allow_fund_defaults_false(client, project):
    resp = client.post(f"/api/projects/{project['id']}/environments", json={"name": "E", "base_url": "https://x.test"})
    assert resp.status_code == 201 and resp.json()["allow_fund"] is False


def test_add_missing_columns_upgrades_old_db(tmp_path, monkeypatch):
    from sqlalchemy import create_engine
    from sentinel.backend import db

    old = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with old.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE environment (id INTEGER PRIMARY KEY, name VARCHAR(50))")
        conn.exec_driver_sql("INSERT INTO environment (id, name) VALUES (1, 'SIT')")
    monkeypatch.setattr(db, "engine", old)
    db._add_missing_columns()
    db._add_missing_columns()  # 幂等
    with old.connect() as conn:
        assert conn.exec_driver_sql("SELECT allow_fund FROM environment WHERE id = 1").scalar() == 0
