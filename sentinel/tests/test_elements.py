def test_element_sync(client, project, sample_dir):
    url = f"/api/projects/{project['id']}/elements"
    r = client.post(url + "/sync").json()
    assert (r["added"], r["removed"], r["errors"]) == (5, 0, [])

    els = {e["name"]: e for e in client.get(url).json()}
    assert set(els) == {"PATH", "SUBMIT", "TITLE_TEXT", "ROW_XPATH", "URL_PATTERN"}
    assert {k: v["kind"] for k, v in els.items()} == {
        "PATH": "path", "SUBMIT": "css", "TITLE_TEXT": "text", "ROW_XPATH": "xpath", "URL_PATTERN": "regex"}
    assert els["SUBMIT"]["refs"] == 2 and els["SUBMIT"]["page"] == "DemoPage" and els["SUBMIT"]["line"] == 6
    assert els["TITLE_TEXT"]["refs"] == 1  # 子类 ChildPage 中的 self.TITLE_TEXT 计入父类常量的引用
    assert els["ROW_XPATH"]["refs"] == 0

    client.put(f"/api/elements/{els['SUBMIT']['id']}", json={"remark": "提交按钮"})
    page = sample_dir / "pages" / "demo_page.py"
    page.write_text(page.read_text().replace('    ROW_XPATH = "//table//tr"\n', "").replace("button[type=submit]", "#go"))
    r = client.post(url + "/sync").json()
    assert (r["added"], r["updated"], r["removed"]) == (0, 1, 1)
    submit = client.get(url, params={"keyword": "#go"}).json()[0]
    assert submit["remark"] == "提交按钮"  # 平台备注保留
    assert [e["name"] for e in client.get(url, params={"status": "removed"}).json()] == ["ROW_XPATH"]


def test_element_sync_syntax_error(client, project, sample_dir):
    (sample_dir / "pages" / "broken.py").write_text("class X(:\n")
    r = client.post(f"/api/projects/{project['id']}/elements/sync").json()
    assert r["added"] == 5 and r["errors"][0]["file"] == "pages/broken.py"
