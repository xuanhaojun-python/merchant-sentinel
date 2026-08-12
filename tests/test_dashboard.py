import pytest
from pages.dashboard_page import DashboardPage


@pytest.mark.dashboard
def test_dashboard_balance_visible(logged_in_page):
    """登录后 Dashboard 显示余额"""
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()
    balance = dashboard.get_balance_text()
    assert balance


@pytest.mark.dashboard
def test_dashboard_stats_visible(logged_in_page):
    """Dashboard 统计数据区域可见"""
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()
    assert dashboard.is_stats_visible()


@pytest.mark.dashboard
def test_dashboard_loads_without_error(logged_in_page):
    """Dashboard 页面无 JS 错误"""
    errors = []
    logged_in_page.on("pageerror", lambda e: errors.append(str(e)))
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()
    dashboard.wait_for_element(dashboard.STATS_CONTAINER)
    assert errors == [], f"页面 JS 错误: {errors}"
