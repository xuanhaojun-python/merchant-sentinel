"""运营后台 proto 的 HTTP 客户端（辅助用途：取邮箱验证码、后续的审批放行）。

登录链路（OAuth2 授权码，2026-11-10 SIT 实测）：
  1. GET  {proto}/redirect/proto/oauth2/authorization/sso?redirectUrl=…   → 302 到 SSO，带 state，并写入 proto 侧 cookie
  2. POST {sso}/api/user/login {username, password, type: "account"}     → access_token
  3. GET  {sso}/api/oauth/authorize?<第 1 步 location 的 query>
          Authorization: Bearer <access_token>                           → data.redirect_uri（带 code）
  4. GET  data.redirect_uri（proto 回调）                                 → 写入 cookie proto-token
之后的 proto 接口靠 cookie proto-token 认证，并且必须带 header `x-pd-uri: api`（否则 nginx 返回 405），
带 `x-lp-user-id` 时才会返回数据。

注意：事件中心只保留最近约 1 小时的事件，取码必须在触发发码后尽快进行。
"""
import json
import time
from typing import Any, Callable
from urllib.parse import urlsplit

import httpx

EMAIL_TOPIC = "chnl_email"
_OK = "0000"


class ProtoError(RuntimeError):
    """proto 接口业务错误。"""


class ProtoAuthError(ProtoError):
    """SSO / proto 登录失败。"""


class ProtoClient:
    def __init__(self, base_url: str, sso_url: str, username: str, password: str,
                 transport: httpx.BaseTransport | None = None, timeout: float = 30,
                 clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.base_url = base_url.rstrip("/")
        self.sso_url = sso_url.rstrip("/")
        self._username = username
        self._password = password
        self._clock = clock
        self._sleep = sleep
        self._http = httpx.Client(timeout=timeout, transport=transport)
        self._user_id: str | None = None

    # ── 登录 ─────────────────────────────────────────────────────
    def login(self) -> None:
        self._http.cookies.clear()
        start = self._http.get(f"{self.base_url}/redirect/proto/oauth2/authorization/sso",
                               params={"redirectUrl": f"{self.base_url}/"})
        location = start.headers.get("location")
        if start.status_code not in (301, 302, 303) or not location:
            raise ProtoAuthError(f"proto 未跳转到 SSO（HTTP {start.status_code}）")

        resp = self._http.post(f"{self.sso_url}/api/user/login",
                               json={"username": self._username, "password": self._password, "type": "account"})
        body = _json(resp)
        if body.get("code") != 0 or not (body.get("data") or {}).get("access_token"):
            raise ProtoAuthError(f"SSO 登录失败：{body.get('errMsg') or resp.status_code}")
        sso_token = body["data"]["access_token"]

        resp = self._http.get(f"{self.sso_url}/api/oauth/authorize?{urlsplit(location).query}",
                              headers={"Authorization": f"Bearer {sso_token}"})
        body = _json(resp)
        redirect_uri = (body.get("data") or {}).get("redirect_uri")
        if body.get("code") != 0 or not redirect_uri:
            raise ProtoAuthError(f"SSO 授权失败：{body.get('errMsg') or resp.status_code}")

        self._http.get(redirect_uri)
        if not self._http.cookies.get("proto-token"):
            raise ProtoAuthError("proto 回调后未拿到 proto-token")

        user = self._call("GET", "/proto/ops/user", retry_auth=False)
        self._user_id = user.get("userId")
        if not self._user_id:
            raise ProtoAuthError("proto 未返回当前用户 userId")

    # ── 通用请求 ──────────────────────────────────────────────────
    def _call(self, method: str, path: str, json_body: dict | None = None, retry_auth: bool = True) -> Any:
        if retry_auth and self._user_id is None:
            self.login()
        headers = {"x-pd-uri": "api"}
        if self._user_id:
            headers["x-lp-user-id"] = self._user_id
        resp = self._http.request(method, f"{self.base_url}{path}", json=json_body, headers=headers)
        if resp.status_code == 401 and retry_auth:
            self.login()
            return self._call(method, path, json_body, retry_auth=False)
        if resp.status_code == 401:
            raise ProtoAuthError(f"proto 未授权：{method} {path}")
        body = _json(resp)
        if body.get("code") != _OK:
            raise ProtoError(f"proto 接口失败 {method} {path}：{body.get('code')} {body.get('msg')}")
        return body.get("data")

    # ── 事件中心 ──────────────────────────────────────────────────
    def query_events(self, topic: str, start_ms: int, end_ms: int, page: int = 1, limit: int = 50) -> list[dict]:
        data = self._call("POST", "/proto/ec/queryHistory", {
            "pageNum": page, "limit": limit, "producer": "", "topic": topic,
            "eventType": "", "eventId": "", "startTime": start_ms, "endTime": end_ms,
        })
        return list((data or {}).get("records") or [])

    def wait_for_email_code(self, to: str, since_ms: int, timeout: float = 120, interval: float = 3) -> str:
        """轮询 chnl_email 事件，返回发给 `to` 的、在 since_ms 之后产生的最新验证码。"""
        target = to.strip().lower()
        begin = self._clock()
        while True:
            now_ms = int(self._clock() * 1000)
            events = self.query_events(EMAIL_TOPIC, since_ms - 5000, now_ms + 5000)
            matches = []
            for ev in events:
                model = _data_model(ev)
                created = int(ev.get("createTime") or 0)
                if (model and str(model.get("to", "")).strip().lower() == target
                        and model.get("code") and created >= since_ms):
                    matches.append((created, str(model["code"])))
            if matches:
                return max(matches)[1]
            waited = self._clock() - begin
            if waited >= timeout:
                raise TimeoutError(f"{waited:.0f}s 内未在 proto 事件中心找到发给 {to} 的验证码")
            self._sleep(interval)

    def close(self) -> None:
        self._http.close()


def _json(resp: httpx.Response) -> dict:
    try:
        body = resp.json()
    except ValueError as e:
        raise ProtoError(f"非 JSON 响应：HTTP {resp.status_code} {resp.request.url}") from e
    return body if isinstance(body, dict) else {}


def _data_model(event: dict) -> dict | None:
    detail = event.get("detail")
    if isinstance(detail, str):
        try:
            detail = json.loads(detail)
        except ValueError:
            return None
    payload = (detail or {}).get("payload") if isinstance(detail, dict) else None
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            return None
    model = (payload or {}).get("dataModel") if isinstance(payload, dict) else None
    return model if isinstance(model, dict) else None
