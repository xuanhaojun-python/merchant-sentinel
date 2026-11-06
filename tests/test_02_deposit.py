import pytest
from playwright.sync_api import expect
from pages.deposit_page import DepositPage


@pytest.mark.smoke
@pytest.mark.deposit
def test_deposit(logged_in_page):
    deposit = DepositPage(logged_in_page)
    deposit.goto()

    print("\n[Deposit] Crypto tab 可见")
    expect(deposit.crypto_tab).to_be_visible()

    print("[Deposit] Fiat tab 可见")
    expect(deposit.fiat_tab).to_be_visible()

    print("[Deposit] 货币选择器可见")
    expect(deposit.currency_selector).to_be_visible()

    print("[Deposit] 网络选择器可见")
    expect(deposit.network_selector).to_be_visible()
