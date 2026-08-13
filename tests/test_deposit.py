import pytest
from pages.deposit_page import DepositPage


@pytest.mark.deposit
def test_deposit_page_loads(logged_in_page):
    """Deposit 页面正常加载"""
    deposit = DepositPage(logged_in_page)
    deposit.goto()
    assert deposit.is_crypto_tab_visible()


@pytest.mark.deposit
def test_deposit_fiat_tab_visible(logged_in_page):
    """Deposit 页面 Fiat tab 可见"""
    deposit = DepositPage(logged_in_page)
    deposit.goto()
    assert deposit.is_fiat_tab_visible()


@pytest.mark.deposit
def test_deposit_currency_selector_visible(logged_in_page):
    """Deposit 页面货币选择器可见"""
    deposit = DepositPage(logged_in_page)
    deposit.goto()
    assert deposit.is_currency_selector_visible()


@pytest.mark.deposit
def test_deposit_network_selector_visible(logged_in_page):
    """Deposit 页面网络选择器可见"""
    deposit = DepositPage(logged_in_page)
    deposit.goto()
    assert deposit.is_network_selector_visible()
