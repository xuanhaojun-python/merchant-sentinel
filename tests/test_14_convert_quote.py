"""P0 金额 / 汇率：Convert 报价计算与校验。只读，绝不点击 Submit。

买入金额规则（2026-11-19 SIT 实测）：Buy = Sell × 报价，向下截断到 2 位（10 × 0.987911 = 9.879 → 9.87）。
"""
from decimal import Decimal

import pytest
from playwright.sync_api import expect

from pages.convert_page import ConvertPage
from utils.money import assert_amount, round_down


@pytest.fixture
def convert(logged_in_page):
    c = ConvertPage(logged_in_page)
    c.goto()
    c.sell_input.wait_for(state="visible")
    return c


def _buy_and_quote(convert: ConvertPage, amount: str):
    """输入金额后读取 (报价, 买入金额)；报价恰好在读取间隙刷新时重试。"""
    for _ in range(3):
        convert.enter_sell(amount)
        expect(convert.buy_input).not_to_have_value("")
        before = convert.quote()[0]
        buy = convert.buy_amount()
        if convert.quote()[0] == before:
            return before, buy
    raise AssertionError("报价持续刷新，无法稳定读取")


@pytest.mark.p0
@pytest.mark.convert
def test_currency_options(convert):
    sell, buy = convert.options(0), convert.options(1)
    print(f"\n[Convert] 卖出币种 {sell}，买入币种 {buy}")
    assert set(sell) == {"USDT", "USDC"}
    assert set(buy) == {"USD", "EUR", "GBP"}
    balance, ccy = convert.available()
    assert_amount(sell[ccy], balance, 6)


@pytest.mark.p0
@pytest.mark.convert
def test_min_and_max_amount(convert):
    print("\n[Convert] 输入 0.5 → 提示最小 1 USDT")
    convert.enter_sell("0.5")
    expect(convert.field_error()).to_have_text(ConvertPage.MSG_MIN_AMOUNT)
    print("[Convert] 输入 999999999 → 提示最大 2,000,000 USDT")
    convert.enter_sell("999999999")
    expect(convert.field_error()).to_have_text(ConvertPage.MSG_MAX_AMOUNT)
    print("[Convert] 输入 abc → 输入框保持为空，不出报价金额")
    convert.enter_sell("abc")
    expect(convert.sell_input).to_have_value("")
    expect(convert.buy_input).to_have_value("")


@pytest.mark.p0
@pytest.mark.convert
@pytest.mark.parametrize("amount", ["1", "10", "123.456789"])
def test_buy_amount_equals_sell_times_quote(convert, amount):
    rate, buy = _buy_and_quote(convert, amount)
    expected = round_down(Decimal(amount) * rate, 2)
    print(f"\n[Convert] {amount} × {rate} = {Decimal(amount) * rate} → 截断 {expected}，页面 {buy}")
    assert_amount(buy, expected, 2)


@pytest.mark.p0
@pytest.mark.convert
def test_max_uses_available_balance(convert):
    balance, _ = convert.available()
    print(f"\n[Convert] 点击 Max → 卖出金额 = 可用余额 {balance}")
    convert.max_button.click()
    expect(convert.sell_input).to_have_value(f"{balance:,.6f}")
    expect(convert.buy_input).not_to_have_value("")
    rate = convert.quote()[0]
    assert_amount(convert.buy_amount(), round_down(balance * rate, 2), 2)


@pytest.mark.p0
@pytest.mark.convert
def test_quote_countdown(convert):
    first = convert.countdown_seconds()
    convert.page.wait_for_timeout(1500)
    second = convert.countdown_seconds()
    print(f"\n[Convert] 报价倒计时 {first}s → {second}s")
    assert 0 <= first <= 30 and second != first
