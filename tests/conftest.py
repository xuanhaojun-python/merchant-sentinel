import base64
import html as html_lib
import os
import pytest
from playwright.sync_api import sync_playwright, expect
from config.settings import settings
from pages.login_page import LoginPage
from datetime import datetime


# ── 自定义报告数据收集 ────────────────────────────────────────────
class _Report:
    results = []
    start_time = None


def _take_screenshot(item) -> str | None:
    """失败时对当前 page 截图，返回 base64 字符串（用于内嵌报告），失败则返回 None。"""
    page = item.funcargs.get("logged_in_page") or item.funcargs.get("fresh_page")
    if page is None:
        return None
    try:
        # 由测试平台执行时，截图写入本次执行的产物目录
        shot_dir = os.path.join(os.getenv("MS_RUN_DIR", "reports"), "screenshots")
        os.makedirs(shot_dir, exist_ok=True)
        path = os.path.join(shot_dir, f"{item.name}.png")
        page.screenshot(path=path, full_page=True)
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        stdout = ""
        for name, content in rep.sections:
            if "stdout" in name.lower():
                stdout = content.strip()
                break
        steps = [line for line in stdout.splitlines() if line.strip().startswith("[")]
        screenshot_b64 = _take_screenshot(item) if rep.failed else None
        _Report.results.append({
            "name": item.name,
            "outcome": rep.outcome,
            "duration": round(rep.duration, 2),
            "steps": steps,
            "error": str(rep.longrepr) if rep.failed else None,
            "screenshot": screenshot_b64,
        })


def pytest_sessionstart(session):
    settings.require_credentials()
    # expect 断言默认超时 5s，SIT 环境偏慢，统一使用配置的超时
    expect.set_options(timeout=settings.timeout_default)
    _Report.start_time = datetime.now()
    _Report.results = []


def pytest_sessionfinish(session, exitstatus):
    results = _Report.results
    passed = sum(1 for r in results if r["outcome"] == "passed")
    failed = sum(1 for r in results if r["outcome"] == "failed")
    skipped = sum(1 for r in results if r["outcome"] == "skipped")
    total_sec = sum(r["duration"] for r in results)
    run_time = _Report.start_time.strftime("%Y-%m-%d %H:%M:%S") if _Report.start_time else ""

    rows = ""
    for r in results:
        color = {"passed": "#2e7d32", "skipped": "#f9a825"}.get(r["outcome"], "#c62828")
        badge = r["outcome"].upper()
        steps_html = "".join(
            f'<div class="step">✅ {html_lib.escape(s)}</div>' for s in r["steps"]
        )
        if r["error"]:
            steps_html += f'<div class="error"><pre>{html_lib.escape(r["error"])}</pre></div>'
        if r.get("screenshot"):
            steps_html += f'<div class="screenshot"><img src="data:image/png;base64,{r["screenshot"]}" alt="failure screenshot"></div>'
        rows += f"""
        <tr>
          <td><span class="badge" style="background:{color}">{badge}</span></td>
          <td class="name">{r['name']}</td>
          <td>{r['duration']}s</td>
          <td class="steps-cell">{steps_html}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>测试报告</title>
<style>
  body {{ font-family: -apple-system, Arial, sans-serif; margin: 0; background: #f5f5f5; color: #333; }}
  .header {{ background: #1a237e; color: #fff; padding: 24px 32px; }}
  .header h1 {{ margin: 0 0 8px; font-size: 22px; }}
  .header p {{ margin: 0; font-size: 13px; opacity: .8; }}
  .summary {{ display: flex; gap: 16px; padding: 20px 32px; }}
  .card {{ background: #fff; border-radius: 8px; padding: 16px 24px; min-width: 120px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  .card .num {{ font-size: 28px; font-weight: bold; }}
  .card .label {{ font-size: 12px; color: #888; margin-top: 4px; }}
  .passed .num {{ color: #2e7d32; }}
  .failed .num {{ color: #c62828; }}
  table {{ width: calc(100% - 64px); margin: 0 32px 32px; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  th {{ background: #e8eaf6; padding: 12px 16px; text-align: left; font-size: 13px; color: #555; }}
  td {{ padding: 12px 16px; vertical-align: top; border-top: 1px solid #f0f0f0; font-size: 13px; }}
  .name {{ font-weight: 500; }}
  .badge {{ color: #fff; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
  .step {{ padding: 3px 0; color: #37474f; font-size: 13px; }}
  .error {{ margin-top: 8px; }}
  .error pre {{ background: #fce4ec; color: #b71c1c; padding: 10px; border-radius: 4px; font-size: 12px; white-space: pre-wrap; word-break: break-all; }}
  .screenshot {{ margin-top: 10px; }}
  .screenshot img {{ max-width: 100%; border: 1px solid #e0e0e0; border-radius: 4px; cursor: pointer; }}
</style>
</head>
<body>
<div class="header">
  <h1>🧪 Leptage 商户后台 UI 自动化测试报告</h1>
  <p>执行时间：{run_time} &nbsp;|&nbsp; 共 {len(results)} 条用例 &nbsp;|&nbsp; 总耗时 {total_sec:.1f}s</p>
</div>
<div class="summary">
  <div class="card passed"><div class="num">{passed}</div><div class="label">通过</div></div>
  <div class="card failed"><div class="num">{failed}</div><div class="label">失败</div></div>
  <div class="card"><div class="num">{skipped}</div><div class="label">跳过</div></div>
  <div class="card"><div class="num">{len(results)}</div><div class="label">总计</div></div>
</div>
<table>
  <thead><tr><th>结果</th><th>用例名称</th><th>耗时</th><th>检查步骤 / 失败截图</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
</body>
</html>"""

    os.makedirs("reports", exist_ok=True)
    with open("reports/custom_report.html", "w", encoding="utf-8") as f:
        f.write(html)


# ── Playwright fixtures ───────────────────────────────────────────
@pytest.fixture(scope="session")
def _browser():
    """整个 session 只启动一个浏览器"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.headless, slow_mo=settings.slow_mo)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def page(_browser):
    """整个 session 只有一个 page，登录一次，所有用例复用"""
    context = _browser.new_context()
    pg = context.new_page()

    login = LoginPage(pg)
    login.goto()
    login.login(settings.email, settings.password)
    login.wait_for_dashboard()

    yield pg
    context.close()


@pytest.fixture(scope="session")
def logged_in_page(page):
    """已登录的 page，session 内所有用例共享"""
    return page


@pytest.fixture(scope="function")
def fresh_page(_browser):
    """无登录态，专用于登录流程测试"""
    context = _browser.new_context()
    pg = context.new_page()
    yield pg
    context.close()
