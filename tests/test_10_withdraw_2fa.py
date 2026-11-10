"""P0 安全：账号开启 2FA 时，提现必须输入 2FA 验证码。

安全约束：本用例绝不输入验证码。点击 Confirm 之前先断言 2FA 输入框存在，
如果账号的 2FA 被关闭（输入框不存在），用例直接失败而不会点 Confirm，避免真实下单。
"""
import pytest
from playwright.sync_api import expect

from pages.login_page import LoginPage
from pages.setting_page import SettingPage
from pages.withdraw_page import WithdrawPage

AMOUNT = "0.1"  # 最小提现额；本用例不会真实提交


@pytest.mark.p0
@pytest.mark.security
@pytest.mark.withdraw
def test_withdraw_requires_2fa(logged_in_page):
    page = logged_in_page

    print("\n[2FA] Setting 页确认账号已开启 2FA（显示 Disable 2FA）")
    setting = SettingPage(page)
    setting.goto()
    expect(setting.disable_2fa_entry).to_be_visible()

    withdraw = WithdrawPage(page)
    withdraw.goto()

    print("[2FA] 表单未填写时提交按钮禁用")
    expect(withdraw.submit_button).to_be_disabled()

    print(f"[2FA] 输入金额 {AMOUNT} 并选择第一个收款账户")
    withdraw.amount_input.fill(AMOUNT)
    withdraw.select_first_beneficiary()
    expect(withdraw.submit_button).to_be_enabled()

    print("[2FA] 点击 Withdraw Authentication 弹出确认弹窗")
    withdraw.submit_button.click()
    expect(withdraw.confirm_dialog).to_be_visible()

    print("[2FA] 弹窗包含 6 位 2FA 验证码输入框")
    expect(withdraw.two_fa_input).to_be_visible()  # 安全闸：不存在则在此失败，不会点 Confirm
    expect(withdraw.two_fa_input).to_have_attribute("maxlength", "6")
    expect(withdraw.two_fa_input).to_have_value("")

    try:
        print("[2FA] 不输入验证码直接 Confirm → 提示必填，弹窗不关闭")
        withdraw.confirm_button.click()
        expect(withdraw.field_error(withdraw.confirm_dialog)).to_have_text(LoginPage.MSG_REQUIRED)
        expect(withdraw.confirm_dialog).to_be_visible()
    finally:
        print("[2FA] Cancel 关闭弹窗")
        if withdraw.confirm_dialog.is_visible():
            withdraw.cancel_button.click()
    expect(withdraw.confirm_dialog).to_be_hidden()
