import pytest
from pages.dashboard_page import DashboardPage


@pytest.mark.dashboard
def test_wallet_page_loads(logged_in_page):
    """Wallet 首页正常加载，显示欢迎标题"""
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()
    assert dashboard.is_welcome_visible()


@pytest.mark.dashboard
def test_wallet_balance_card_visible(logged_in_page):
    """Wallet 首页余额卡片可见"""
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()
    assert dashboard.is_balance_card_visible()


@pytest.mark.dashboard
def test_wallet_action_buttons_visible(logged_in_page):
    """Wallet 首页 Deposit / Withdraw / Convert 按钮可见"""
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()
    assert dashboard.is_deposit_button_visible()


@pytest.mark.dashboard
def test_wallet_currencies_section_visible(logged_in_page):
    """Wallet 首页 All Currencies 区块可见"""
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()
    assert dashboard.is_currencies_section_visible()
