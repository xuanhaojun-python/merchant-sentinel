import json

import httpx
import pytest

from clients.proto_client import ProtoAuthError, ProtoClient

PROTO = "https://proto.test"
SSO = "https://sso.test"


class FakeProto:
    """模拟 SSO + proto 的 OAuth 登录链路与事件中心。"""

    def __init__(self):
        self.logins = 0
        self.valid_token = None
        self.events = []
        self.expire_next_query = False
        self.sso_ok = True
        self.query_bodies = []

    def handler(self, req: httpx.Request) -> httpx.Response:
        url = str(req.url)
        if url.startswith(f"{PROTO}/redirect/proto/oauth2/authorization/sso"):
            return httpx.Response(302, headers={
                "location": f"{SSO}/oauth/authorize?response_type=code&client_id=c&state=s1",
                "set-cookie": "redirectUrl=x; Path=/"})
        if url == f"{SSO}/api/user/login":
            body = json.loads(req.content)
            assert body["type"] == "account"
            if not self.sso_ok:
                return httpx.Response(200, json={"code": 42200, "errMsg": "bad password", "data": None})
            return httpx.Response(200, json={"code": 0, "errMsg": "ok", "data": {"access_token": "SSO-TOKEN"}})
        if url.startswith(f"{SSO}/api/oauth/authorize"):
            assert req.headers["authorization"] == "Bearer SSO-TOKEN"
            assert "state=s1" in url
            return httpx.Response(200, json={"code": 0, "data": {
                "redirect_uri": f"{PROTO}/redirect/proto/login/oauth2/code/sso?code=abc&state=s1"}})
        if url.startswith(f"{PROTO}/redirect/proto/login/oauth2/code/sso"):
            self.logins += 1
            self.valid_token = f"PT{self.logins}"
            return httpx.Response(302, headers={"location": f"{PROTO}/",
                                                "set-cookie": f"proto-token={self.valid_token}; Path=/"})
        # 以下为 proto 业务接口
        assert req.headers.get("x-pd-uri") == "api"
        if f"proto-token={self.valid_token}" not in req.headers.get("cookie", ""):
            return httpx.Response(401)
        if url.startswith(f"{PROTO}/proto/ops/user"):
            return httpx.Response(200, json={"code": "0000", "data": {"userId": "PUSR1"}})
        if url == f"{PROTO}/proto/ec/queryHistory":
            assert req.headers["x-lp-user-id"] == "PUSR1"
            if self.expire_next_query:
                self.expire_next_query = False
                self.valid_token = "rotated"
                return httpx.Response(401)
            body = json.loads(req.content)
            self.query_bodies.append(body)
            recs = [e for e in self.events
                    if e["topic"] == body["topic"] and body["startTime"] <= int(e["createTime"]) <= body["endTime"]]
            return httpx.Response(200, json={"code": "0000", "data": {"records": recs, "total": len(recs)}})
        return httpx.Response(404)

    def add_email(self, to, code, ts_ms):
        self.events.append({"topic": "chnl_email", "createTime": str(ts_ms), "detail": {
            "payload": {"dataModel": {"to": to, "code": code, "exp": 2}, "templateName": "verify.code.sp2.v1"}}})


class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


@pytest.fixture
def fake():
    return FakeProto()


PASSWORD = "S3cr3t-Pa55"


def make_client(fake, clock=None):
    clock = clock or Clock(1_000_000.0)
    return ProtoClient(PROTO, SSO, "u", PASSWORD, transport=httpx.MockTransport(fake.handler),
                       clock=clock, sleep=clock.sleep)


def test_login_flow_and_query(fake):
    fake.add_email("a@test.com", "111111", 1_000_000_000)
    client = make_client(fake)
    events = client.query_events("chnl_email", 999_999_000, 1_000_001_000)
    assert fake.logins == 1
    assert len(events) == 1


def test_sso_login_failure_hides_password(fake):
    fake.sso_ok = False
    client = make_client(fake)
    with pytest.raises(ProtoAuthError) as e:
        client.login()
    assert "bad password" in str(e.value)
    assert PASSWORD not in str(e.value)


def test_relogin_once_on_401(fake):
    client = make_client(fake)
    client.login()
    fake.expire_next_query = True
    client.query_events("chnl_email", 0, 1)
    assert fake.logins == 2


def test_wait_for_email_code_matches_recipient_and_ignores_old(fake):
    clock = Clock(1_000_000.0)
    since = int(clock.t * 1000)
    fake.add_email("me@test.com", "000000", since - 60_000)      # 旧验证码
    fake.add_email("other@test.com", "999999", since + 1_000)    # 别人的
    fake.add_email("ME@test.com", "123456", since + 2_000)        # 目标（大小写不敏感）
    client = make_client(fake, clock)
    assert client.wait_for_email_code("me@test.com", since) == "123456"


def test_wait_for_email_code_picks_latest(fake):
    clock = Clock(1_000_000.0)
    since = int(clock.t * 1000)
    fake.add_email("me@test.com", "111111", since + 1_000)
    fake.add_email("me@test.com", "222222", since + 3_000)
    assert make_client(fake, clock).wait_for_email_code("me@test.com", since) == "222222"


def test_wait_for_email_code_polls_until_arrival(fake):
    clock = Clock(1_000_000.0)
    since = int(clock.t * 1000)
    client = make_client(fake, clock)
    orig = fake.handler
    calls = {"n": 0}

    def handler(req):
        if str(req.url).endswith("/proto/ec/queryHistory"):
            calls["n"] += 1
            if calls["n"] == 3:
                fake.add_email("me@test.com", "654321", since + 6_000)
        return orig(req)
    client._http._transport = httpx.MockTransport(handler)
    assert client.wait_for_email_code("me@test.com", since, interval=3) == "654321"
    assert calls["n"] == 3


def test_wait_for_email_code_timeout(fake):
    clock = Clock(1_000_000.0)
    client = make_client(fake, clock)
    with pytest.raises(TimeoutError, match="me@test.com"):
        client.wait_for_email_code("me@test.com", int(clock.t * 1000), timeout=10, interval=3)
