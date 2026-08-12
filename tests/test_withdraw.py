import pytest
from pages.withdraw_page import WithdrawPage


@pytest.mark.withdraw
def test_withdraw_page_loads(logged_in_page):
    """提现页面正常加载，显示可用余额"""
    withdraw = WithdrawPage(logged_in_page)
    withdraw.goto()
    balance = withdraw.get_available_balance()
    assert balance


@pytest.mark.withdraw
def test_withdraw_zero_amount_shows_error(logged_in_page):
    """提现金额为 0 时显示错误提示"""
    withdraw = WithdrawPage(logged_in_page)
    withdraw.goto()
    withdraw.fill_amount("0")
    withdraw.fill_address("0xTestAddress1234567890abcdef1234567890abcdef")
    withdraw.submit()
    error = withdraw.get_error_message()
    assert error


@pytest.mark.withdraw
def test_withdraw_invalid_address_shows_error(logged_in_page):
    """无效钱包地址显示错误提示"""
    withdraw = WithdrawPage(logged_in_page)
    withdraw.goto()
    withdraw.fill_amount("1")
    withdraw.fill_address("invalid_address")
    withdraw.submit()
    error = withdraw.get_error_message()
    assert error
