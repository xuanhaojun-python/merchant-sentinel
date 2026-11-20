import time

import httpx
import pytest

from sentinel.backend.services import notifier
from sentinel.tests.conftest import wait_run


class FakePost:
    def __init__(self, resp=None):
        self.calls, self.resp = [], resp or {"code": 0}

    def __call__(self, url, json, timeout):
        self.calls.append((url, json))
        return httpx.Response(200, json=self.resp, request=httpx.Request("POST", url))


@pytest.fixture
def fake_post(monkeypatch):
    fake = FakePost()
    monkeypatch.setattr(notifier.httpx, "post", fake)
    return fake


_n = iter(range(1000))


def _channel(client, **kw):
    body = {"name": f"ch-{next(_n)}", "type": "feishu", "url": "https://open.feishu.example/hook/x", **kw}
    resp = client.post("/api/channels", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_channel_validation(client):
    assert client.post("/api/channels", json={"name": "x", "type": "sms", "url": "https://a"}).status_code == 422
    assert client.post("/api/channels", json={"name": "x", "type": "wecom", "url": "ftp://a"}).status_code == 422


def test_test_message_success_and_failure(client, fake_post, monkeypatch):
    ch = _channel(client, secret="s3cret")
    n = client.post(f"/api/channels/{ch['id']}/test").json()
    assert n["status"] == "success"
    url, body = fake_post.calls[-1]
    assert body["msg_type"] == "post" and "sign" in body and "timestamp" in body

    monkeypatch.setattr(notifier.httpx, "post", FakePost({"code": 19021, "msg": "sign match fail"}))
    assert client.post(f"/api/channels/{ch['id']}/test").json()["status"] == "failed"
    logs = client.get("/api/notifications", params={"channel_id": ch["id"]}).json()
    assert logs["total"] == 2


@pytest.mark.parametrize("ctype,key", [("wecom", "markdown"), ("dingtalk", "markdown"), ("webhook", "lines")])
def test_payload_shapes(ctype, key):
    ch = notifier.NotifyChannel(id=1, name="c", type=ctype, url="https://x.example/hook", secret="k" if ctype == "dingtalk" else "")
    url, body = notifier.build_payload(ch, "标题", ["行1"], "http://localhost/reports/1")
    assert key in body
    if ctype == "dingtalk":
        assert "timestamp=" in url and "sign=" in url


def test_should_notify():
    assert notifier.should_notify("always", "passed")
    assert notifier.should_notify("failed", "error") and not notifier.should_notify("failed", "passed")
    assert not notifier.should_notify("never", "failed")


def test_schedule_run_sends_notification(client, project, env, fake_post):
    client.post(f"/api/projects/{project['id']}/cases/sync")
    ch = _channel(client, type="wecom")
    suite = client.post(f"/api/projects/{project['id']}/suites",
                        json={"name": "fail", "nodeids": ["tests/test_sample.py::test_fail"]}).json()
    sch = client.post(f"/api/projects/{project['id']}/schedules", json={
        "name": "n", "suite_id": suite["id"], "environment_id": env["id"], "cron": "0 3 * * *",
        "channel_ids": [ch["id"]], "notify_on": "failed"}).json()
    run = wait_run(client, client.post(f"/api/schedules/{sch['id']}/trigger").json()["id"])
    assert run["status"] == "failed"

    deadline = time.time() + 10
    while time.time() < deadline:
        items = client.get("/api/notifications", params={"channel_id": ch["id"]}).json()["items"]
        if items:
            break
        time.sleep(0.2)
    assert items and items[0]["run_id"] == run["id"] and items[0]["status"] == "success"
    assert "test_fail" in items[0]["content"]

    # 手动补发
    again = client.post(f"/api/runs/{run['id']}/notify", json={"channel_ids": [ch["id"]]}).json()
    assert len(again) == 1 and again[0]["status"] == "success"
    assert client.post(f"/api/notifications/{items[0]['id']}/resend").json()["status"] == "success"


def test_delete_channel_detaches_from_schedule(client, project):
    client.post(f"/api/projects/{project['id']}/cases/sync")
    ch = _channel(client)
    suite = client.post(f"/api/projects/{project['id']}/suites", json={"name": "d", "marker_expr": "smoke"}).json()
    sch = client.post(f"/api/projects/{project['id']}/schedules", json={
        "name": "d", "suite_id": suite["id"], "cron": "0 4 * * *", "channel_ids": [ch["id"]]}).json()
    assert client.delete(f"/api/channels/{ch['id']}").status_code == 204
    assert client.get(f"/api/projects/{project['id']}/schedules").json()[0]["channel_ids"] == []
    client.delete(f"/api/schedules/{sch['id']}")
