import pytest
from playwright.sync_api import expect
from pages.dashboard_page import DashboardPage


@pytest.mark.smoke
@pytest.mark.dashboard
def test_dashboard(logged_in_page):
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()

    print("\n[Dashboard] 欢迎标题可见")
    expect(dashboard.welcome_heading).to_be_visible()

    print("[Dashboard] 余额卡片可见")
    expect(dashboard.balance_card).to_be_visible()

    print("[Dashboard] Deposit 按钮可见")
    expect(dashboard.deposit_button).to_be_visible()

    print("[Dashboard] All Currencies 区块可见")
    expect(dashboard.currencies_section).to_be_visible()

    print("[Dashboard] 点击 Deposit 按钮 → 跳转 Deposit 页")
    dashboard.click_action_deposit()

    dashboard.goto()
    print("[Dashboard] 点击 Convert 按钮 → 跳转 Convert 页")
    dashboard.click_action_convert()

    dashboard.goto()
    print("[Dashboard] 点击 Withdraw 按钮 → 跳转 Withdraw 页")
    dashboard.click_action_withdraw()
