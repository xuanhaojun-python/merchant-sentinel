import pytest
from playwright.sync_api import sync_playwright
from config.settings import settings
from pages.login_page import LoginPage
from datetime import datetime


# ── 自定义报告数据收集 ────────────────────────────────────────────
class _Report:
    results = []
    start_time = None


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
        _Report.results.append({
            "name": item.name,
            "outcome": rep.outcome,
            "duration": round(rep.duration, 2),
            "steps": steps,
            "error": str(rep.longrepr) if rep.failed else None,
        })


def pytest_sessionstart(session):
    _Report.start_time = datetime.now()
    _Report.results = []


def pytest_sessionfinish(session, exitstatus):
    results = _Report.results
    passed = sum(1 for r in results if r["outcome"] == "passed")
    failed = sum(1 for r in results if r["outcome"] == "failed")
    total_sec = sum(r["duration"] for r in results)
    run_time = _Report.start_time.strftime("%Y-%m-%d %H:%M:%S") if _Report.start_time else ""

    rows = ""
    for r in results:
        color = "#2e7d32" if r["outcome"] == "passed" else "#c62828"
        badge = "PASSED" if r["outcome"] == "passed" else "FAILED"
        steps_html = "".join(
            f'<div class="step">✅ {s}</div>' for s in r["steps"]
        )
        if r["error"]:
            steps_html += f'<div class="error"><pre>{r["error"]}</pre></div>'
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
  <div class="card"><div class="num">{len(results)}</div><div class="label">总计</div></div>
</div>
<table>
  <thead><tr><th>结果</th><th>用例名称</th><th>耗时</th><th>检查步骤</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
</body>
</html>"""

    import os
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
