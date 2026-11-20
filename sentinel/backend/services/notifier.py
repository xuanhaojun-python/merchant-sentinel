"""通知：执行结束后按定时任务配置推送到飞书 / 企业微信 / 钉钉 / 通用 webhook，并记录发送结果。"""
import base64
import hashlib
import hmac
import threading
import time
import urllib.parse

import httpx

from sentinel.backend import settings
from sentinel.backend.db import SessionLocal
from sentinel.backend.models import Notification, NotifyChannel, Project, Run, Schedule

STATUS_TEXT = {"passed": "✅ 通过", "failed": "❌ 失败", "error": "⚠️ 错误", "stopped": "⏹ 已停止",
               "interrupted": "⏸ 已中断"}
TRIGGER_TEXT = {"manual": "手动", "suite": "套件", "schedule": "定时", "script": "脚本"}
TIMEOUT = 10


def build_message(run: Run, project_name: str) -> tuple[str, list[str], str]:
    """返回 (标题, 正文行, 报告链接)。"""
    title = f"[Web3Rec] {project_name} · {run.title or f'执行 #{run.id}'} {STATUS_TEXT.get(run.status, run.status)}"
    rate = f"{run.passed / run.total * 100:.0f}%" if run.total else "-"
    lines = [
        f"执行 ID：#{run.id}（{TRIGGER_TEXT.get(run.trigger, run.trigger)}）",
        f"环境：{run.environment_name or '工程默认配置'}",
        f"结果：通过 {run.passed} / 失败 {run.failed} / 跳过 {run.skipped} / 共 {run.total}（通过率 {rate}）",
        f"耗时：{run.duration:.1f}s",
    ]
    failed = [r.nodeid.split("::")[-1] for r in run.results if r.outcome in ("failed", "error")]
    if failed:
        shown = failed[:10]
        lines.append("失败用例：" + "、".join(shown) + (f" 等 {len(failed)} 条" if len(failed) > len(shown) else ""))
    if run.message:
        lines.append(f"说明：{run.message}")
    return title, lines, f"{settings.PUBLIC_URL}/reports/{run.id}"


def _sign_feishu(secret: str) -> dict:
    ts = str(int(time.time()))
    sign = base64.b64encode(hmac.new(f"{ts}\n{secret}".encode(), b"", hashlib.sha256).digest()).decode()
    return {"timestamp": ts, "sign": sign}


def _sign_dingtalk(url: str, secret: str) -> str:
    ts = str(int(time.time() * 1000))
    sign = base64.b64encode(hmac.new(secret.encode(), f"{ts}\n{secret}".encode(), hashlib.sha256).digest()).decode()
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}timestamp={ts}&sign={urllib.parse.quote_plus(sign)}"


def build_payload(channel: NotifyChannel, title: str, lines: list[str], link: str, extra: dict | None = None) -> tuple[str, dict]:
    """返回 (请求 URL, JSON 体)。"""
    url = channel.url
    if channel.type == "feishu":
        body = {"msg_type": "post", "content": {"post": {"zh_cn": {
            "title": title,
            "content": [[{"tag": "text", "text": ln}] for ln in lines] + [[{"tag": "a", "text": "查看报告", "href": link}]],
        }}}}
        if channel.secret:
            body.update(_sign_feishu(channel.secret))
    elif channel.type == "wecom":
        body = {"msgtype": "markdown", "markdown": {
            "content": f"**{title}**\n" + "\n".join(f"> {ln}" for ln in lines) + f"\n[查看报告]({link})"}}
    elif channel.type == "dingtalk":
        body = {"msgtype": "markdown", "markdown": {
            "title": title, "text": f"#### {title}\n" + "\n".join(f"- {ln}" for ln in lines) + f"\n\n[查看报告]({link})"}}
        if channel.secret:
            url = _sign_dingtalk(url, channel.secret)
    else:
        body = {"title": title, "lines": lines, "link": link, **(extra or {})}
    return url, body


def _ok(resp: httpx.Response) -> bool:
    if not resp.is_success:
        return False
    try:
        data = resp.json()
    except ValueError:
        return True
    if not isinstance(data, dict):
        return True
    for key in ("code", "errcode", "StatusCode"):
        if key in data and data[key] not in (0, "0"):
            return False
    return True


def send(channel: NotifyChannel, title: str, lines: list[str], link: str, *, run_id=None, project_id=None,
         extra: dict | None = None) -> Notification:
    """同步发送一条通知并落库，返回记录。"""
    url, body = build_payload(channel, title, lines, link, extra)
    try:
        resp = httpx.post(url, json=body, timeout=TIMEOUT)
        status, response = ("success" if _ok(resp) else "failed"), f"HTTP {resp.status_code} {resp.text[:1000]}"
    except httpx.HTTPError as exc:
        status, response = "failed", f"{type(exc).__name__}: {exc}"
    with SessionLocal() as db:
        n = Notification(channel_id=channel.id, channel_name=channel.name, channel_type=channel.type, run_id=run_id,
                         project_id=project_id, title=title, content="\n".join(lines + [link]), status=status,
                         response=response)
        db.add(n)
        db.commit()
        return n


def notify_run(run_id: int, channel_ids: list[int]) -> list[Notification]:
    with SessionLocal() as db:
        run = db.get(Run, run_id)
        if run is None:
            return []
        project = db.get(Project, run.project_id)
        title, lines, link = build_message(run, project.name if project else "")
        extra = {"run_id": run.id, "status": run.status, "total": run.total, "passed": run.passed,
                 "failed": run.failed, "skipped": run.skipped, "duration": run.duration}
        channels = db.query(NotifyChannel).filter(NotifyChannel.id.in_(channel_ids), NotifyChannel.enabled.is_(True)).all()
    return [send(c, title, lines, link, run_id=run_id, project_id=run.project_id, extra=extra) for c in channels]


def should_notify(notify_on: str, status: str) -> bool:
    if notify_on == "always":
        return True
    if notify_on == "failed":
        return status != "passed"
    return False


def on_run_finished(run_id: int) -> None:
    """执行器回调：定时任务触发的执行按配置发通知（在独立线程中发送，不阻塞执行器）。"""
    with SessionLocal() as db:
        run = db.get(Run, run_id)
        if run is None or not run.schedule_id:
            return
        sch = db.get(Schedule, run.schedule_id)
        if sch is None or not sch.channel_ids or not should_notify(sch.notify_on, run.status):
            return
        ids = list(sch.channel_ids)
    threading.Thread(target=notify_run, args=(run_id, ids), daemon=True, name=f"notify-{run_id}").start()
