"""P0 金额 / 手续费：Withdraw → Fiat 表单的校验与计算。

只读：只输入金额、选择收款账户，绝不点击 Withdraw Authentication。
到账金额规则（2026-11-19 SIT 实测）：免费额度内 Recipient Gets = 金额 × 套餐汇率（1 USDT = 1.0 USD）− Total Fee，
Total Fee = Processing fee + Leptage fee。
"""
import re
from decimal import Decimal

import pytest
from playwright.sync_api import expect

from pages.login_page import LoginPage
from pages.withdraw_page import WithdrawPage
from utils.money import assert_amount, round_half_up


@pytest.fixture
def fiat(logged_in_page):
    w = WithdrawPage(logged_in_page)
    w.goto()
    w.amount_input.wait_for(state="visible")
    return w


@pytest.mark.p0
@pytest.mark.withdraw
def test_min_amount_validation(fiat):
    print("\n[Fiat] 金额输入框提示最小值 0.100000")
    expect(fiat.amount_input).to_have_attribute("placeholder", "Min: 0.100000")
    print("[Fiat] 输入 0.05 → 提示最小提现金额")
    fiat.enter_amount("0.05")
    expect(fiat.field_error()).to_have_text(WithdrawPage.MSG_MIN_AMOUNT)
    print("[Fiat] 输入 0.1 → 提示消失")
    fiat.enter_amount("0.1")
    expect(fiat.page.locator(".select-origin-ccy .el-form-item__error:visible")).to_have_count(0)


@pytest.mark.p0
@pytest.mark.withdraw
def test_non_numeric_amount_rejected(fiat):
    print("\n[Fiat] 输入 abc → 输入框保持为空并提示必填")
    fiat.amount_input.fill("abc")
    fiat.amount_input.blur()
    expect(fiat.amount_input).to_have_value("")
    expect(fiat.field_error()).to_have_text(LoginPage.MSG_REQUIRED)


@pytest.mark.p0
@pytest.mark.withdraw
def test_over_balance_validation(fiat):
    balance = fiat.available_balance()
    over = balance + Decimal(1)
    print(f"\n[Fiat] 可用余额 {balance} USDT，输入 {over} → 提示可用余额")
    fiat.enter_amount(str(over))
    expect(fiat.field_error()).to_have_text(f"Your available balance is {balance:,.6f} USDT")


@pytest.mark.p0
@pytest.mark.withdraw
def test_over_free_limit_hint(fiat):
    remaining, total = fiat.remaining_free()
    print(f"\n[Fiat] 套餐免费额度 剩余 {remaining} / 总额 {total} USD")
    assert 0 <= remaining <= total
    print(f"[Fiat] 输入超过剩余额度的金额 {remaining + 1} → 提示超出部分按标准费率")
    fiat.enter_amount(str(remaining + 1))
    expect(fiat.withdraw_tips).to_have_text(WithdrawPage.MSG_OVER_FREE_LIMIT)


@pytest.mark.p0
@pytest.mark.withdraw
def test_max_fills_available_balance(fiat):
    balance = fiat.available_balance()
    print(f"\n[Fiat] 点击 Max → 金额填入可用余额 {balance}")
    fiat.max_button.click()
    expect(fiat.amount_input).to_have_value(f"{balance:,.6f}")


@pytest.mark.p0
@pytest.mark.withdraw
def test_fee_shown_only_after_beneficiary(fiat):
    print("\n[Fiat] 未选收款账户时 Total Fee 显示 -")
    fiat.enter_amount("1")
    assert fiat.total_fee() is None
    print("[Fiat] 选择收款账户后显示 Total Fee、Payout Option、Fee Bearer")
    fiat.select_first_beneficiary()
    expect(fiat.fee_step.locator(".title-style span").first).to_have_text(re.compile(r"Total Fee: [\d.,]+ USD"))
    expect(fiat.page.get_by_text("Payout Option", exact=True)).to_be_visible()
    expect(fiat.page.get_by_text("Fee Bearer:", exact=False).first).to_be_visible()


@pytest.mark.p0
@pytest.mark.withdraw
def test_total_fee_equals_breakdown(fiat):
    fiat.select_first_beneficiary()
    fiat.enter_amount("1")
    expect(fiat.fee_step.locator(".title-style span").first).to_have_text(re.compile(r"Total Fee: [\d.,]+ USD"))
    total = fiat.total_fee()
    parts = fiat.fee_breakdown()
    print(f"\n[Fiat] Total Fee {total} USD，明细 {parts}")
    assert {"Processing", "Leptage"} <= set(parts), parts
    assert_amount(total, sum(parts.values(), Decimal(0)), 2)


@pytest.mark.p0
@pytest.mark.withdraw
@pytest.mark.parametrize("amount", ["0.1", "1", "12.34", "1000"])
def test_recipient_gets_calculation(fiat, amount):
    fiat.select_first_beneficiary()
    remaining, _ = fiat.remaining_free()
    if Decimal(amount) > remaining:
        pytest.skip(f"免费额度剩余 {remaining} USD，不足以验证 {amount}")
    fiat.enter_amount(amount)
    expect(fiat.recipient_input).not_to_have_value("")
    rate, fee, got = fiat.pack_rate(), fiat.total_fee(), fiat.recipient_gets()
    expected = round_half_up(Decimal(amount) * rate - fee, 2)
    print(f"\n[Fiat] {amount} USDT × {rate} − {fee} = {expected}，页面 Recipient Gets {got}")
    assert_amount(got, expected, 2)


@pytest.mark.p0
@pytest.mark.withdraw
def test_market_rate_refreshes(fiat):
    """参考汇率旁有倒计时，倒计时会递减。"""
    first = fiat.rate_countdown()
    print(f"\n[Fiat] 参考汇率 {fiat.market_rate()} USD，倒计时 {first}s")
    assert first is not None and 0 < first <= 30
    fiat.page.wait_for_timeout(2500)
    second = fiat.rate_countdown()
    print(f"[Fiat] 2.5s 后倒计时 {second}s")
    assert second is not None and second != first


@pytest.mark.p2
@pytest.mark.withdraw
def test_payment_note_max_length(fiat):
    print("\n[Fiat] Payment Note 最多 64 个字符")
    fiat.payment_note.fill("x" * 70)
    expect(fiat.payment_note).to_have_value("x" * 64)
    expect(fiat.payment_note_counter).to_have_text("64/64")
    fiat.payment_note.fill("")
    expect(fiat.payment_note_counter).to_have_text("0/64")
