import pytest
from pages.withdraw_page import WithdrawPage


@pytest.mark.smoke
@pytest.mark.withdraw
def test_withdraw(logged_in_page):
    withdraw = WithdrawPage(logged_in_page)
    withdraw.goto()

    print("\n[Withdraw] Fiat tab 可见")
    assert withdraw.is_fiat_tab_visible()

    print("[Withdraw] Crypto tab 可见")
    assert withdraw.is_crypto_tab_visible()

    print("[Withdraw] 进入页面默认 Fiat tab 高亮")
    assert withdraw.is_fiat_tab_active()

    print("[Withdraw] 点击 Crypto tab 高亮")
    withdraw.click_crypto_tab()
    assert withdraw.is_crypto_tab_active()

    print("[Withdraw] 点击 Fiat tab 高亮")
    withdraw.click_fiat_tab()
    assert withdraw.is_fiat_tab_active()
