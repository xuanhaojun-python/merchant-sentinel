"""P0 金额：Withdraw → Crypto 表单校验，以及各页面可用余额一致。只读，绝不点击 Next step。"""
import pytest
from playwright.sync_api import expect

from pages.convert_page import ConvertPage
from pages.withdraw_page import CryptoWithdrawPage, WithdrawPage
from utils.money import assert_amount


@pytest.fixture
def crypto(logged_in_page):
    c = CryptoWithdrawPage(logged_in_page)
    c.goto()
    return c


@pytest.mark.p0
@pytest.mark.withdraw
def test_currency_options_show_balances(crypto):
    opts = crypto.currency_options()
    print(f"\n[Crypto] 可提币种及余额：{opts}")
    assert set(opts) == {"USDT", "USDC"}
    assert all(v >= 0 for v in opts.values())


@pytest.mark.p0
@pytest.mark.withdraw
def test_amount_requires_currency_first(crypto):
    print("\n[Crypto] 未选币种直接输入金额 → 提示先选择钱包")
    crypto.amount_input.type("1", delay=30)
    expect(crypto.field_error()).to_have_text(CryptoWithdrawPage.MSG_SELECT_WALLET_FIRST)
    expect(crypto.next_button).to_be_disabled()


@pytest.mark.p0
@pytest.mark.withdraw
def test_max_withdrawal_limit(crypto):
    crypto.select_currency("USDT")
    print("\n[Crypto] 输入 99999999 → 提示单笔最大 10,000 USDT")
    crypto.amount_input.type("99999999", delay=20)
    expect(crypto.field_error()).to_have_text(CryptoWithdrawPage.MSG_MAX_AMOUNT)
    expect(crypto.next_button).to_be_disabled()


@pytest.mark.p0
@pytest.mark.withdraw
def test_next_step_disabled_without_address(crypto):
    crypto.select_currency("USDT")
    print("\n[Crypto] 选了币种、填了金额但未选地址 → Next step 禁用，手续费显示 -")
    crypto.amount_input.type("1", delay=30)
    expect(crypto.next_button).to_be_disabled()
    expect(crypto.fee_text).to_contain_text("-")
    print("[Crypto] 白名单提示与地址管理入口可见")
    expect(crypto.whitelist_notice).to_be_visible()
    expect(crypto.address_management_link).to_be_visible()


@pytest.mark.p0
@pytest.mark.withdraw
def test_usdt_balance_consistent_across_pages(logged_in_page):
    """Crypto 提现下拉、Crypto 表单、Fiat 提现、Convert 四处显示的 USDT 可用余额一致。"""
    crypto = CryptoWithdrawPage(logged_in_page)
    crypto.goto()
    in_options = crypto.currency_options()["USDT"]
    crypto.select_currency("USDT")
    in_form = crypto.available_balance()

    fiat = WithdrawPage(logged_in_page)
    fiat.goto()
    fiat.amount_input.wait_for(state="visible")
    in_fiat = fiat.available_balance()

    convert = ConvertPage(logged_in_page)
    convert.goto()
    in_convert, ccy = convert.available()
    print(f"\n[余额一致] 下拉 {in_options} / Crypto 表单 {in_form} / Fiat {in_fiat} / Convert {in_convert} {ccy}")
    assert ccy == "USDT"
    for v in (in_form, in_fiat, in_convert):
        assert_amount(v, in_options, 6)
