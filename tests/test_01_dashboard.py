import pytest
from pages.dashboard_page import DashboardPage


@pytest.mark.smoke
@pytest.mark.dashboard
def test_dashboard(logged_in_page):
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()

    print("\n[Dashboard] 欢迎标题可见")
    assert dashboard.is_welcome_visible()

    print("[Dashboard] 余额卡片可见")
    assert dashboard.is_balance_card_visible()

    print("[Dashboard] Deposit 按钮可见")
    assert dashboard.is_deposit_button_visible()

    print("[Dashboard] All Currencies 区块可见")
    assert dashboard.is_currencies_section_visible()

    print("[Dashboard] 点击 Deposit 按钮 → 跳转 Deposit 页")
    dashboard.click_action_deposit()
    assert "/deposit" in logged_in_page.url

    dashboard.goto()

    print("[Dashboard] 点击 Convert 按钮 → 跳转 Convert 页")
    dashboard.click_action_convert()
    assert "/convert" in logged_in_page.url

    dashboard.goto()

    print("[Dashboard] 点击 Withdraw 按钮 → 跳转 Withdraw 页")
    dashboard.click_action_withdraw()
    assert "/withdraw" in logged_in_page.url
