import pytest
from playwright.sync_api import expect
from pages.withdraw_page import WithdrawPage


@pytest.mark.smoke
@pytest.mark.withdraw
def test_withdraw(logged_in_page):
    withdraw = WithdrawPage(logged_in_page)
    withdraw.goto()

    print("\n[Withdraw] Fiat tab 可见")
    expect(withdraw.fiat_tab).to_be_visible()

    print("[Withdraw] Crypto tab 可见")
    expect(withdraw.crypto_tab).to_be_visible()

    print("[Withdraw] 进入页面默认 Fiat tab 高亮")
    expect(logged_in_page).to_have_url(WithdrawPage.FIAT_URL)

    print("[Withdraw] 点击 Crypto tab 高亮")
    withdraw.click_crypto_tab()
    expect(logged_in_page).to_have_url(WithdrawPage.CRYPTO_URL)

    print("[Withdraw] 点击 Fiat tab 高亮")
    withdraw.click_fiat_tab()
    expect(logged_in_page).to_have_url(WithdrawPage.FIAT_URL)
