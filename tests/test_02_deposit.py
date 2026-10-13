import pytest
from pages.deposit_page import DepositPage


@pytest.mark.smoke
@pytest.mark.deposit
def test_deposit(logged_in_page):
    deposit = DepositPage(logged_in_page)
    deposit.goto()

    print("\n[Deposit] Crypto tab 可见")
    assert deposit.is_crypto_tab_visible()

    print("[Deposit] Fiat tab 可见")
    assert deposit.is_fiat_tab_visible()

    print("[Deposit] 货币选择器可见")
    assert deposit.is_currency_selector_visible()

    print("[Deposit] 网络选择器可见")
    assert deposit.is_network_selector_visible()
