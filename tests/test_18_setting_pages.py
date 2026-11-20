"""P2 信息维护类页面：修改密码表单校验、收款账户管理、自动提现策略。只读，不提交任何修改。"""
import pytest
from playwright.sync_api import expect

from pages.login_page import LoginPage
from pages.setting_page import AutoWithdrawPage, BeneficiaryPage, ChangePasswordPage, SettingPage
from pages.withdraw_page import WithdrawPage


@pytest.mark.p2
@pytest.mark.setting
def test_change_password_required_fields(logged_in_page):
    setting = SettingPage(logged_in_page)
    setting.goto()
    print("\n[Setting] 点击 Change Password → 进入修改密码页")
    setting.change_password_button.click()
    logged_in_page.wait_for_url(f"**{ChangePasswordPage.PATH}")
    cp = ChangePasswordPage(logged_in_page)
    expect(cp.password_inputs).to_have_count(3)
    for label in ("Old Password", "New Password", "Confirm New Password"):
        expect(cp.label(label)).to_be_visible()
    print("[Setting] 不填写直接 Submit → 三个字段均提示必填（表单校验拦截，不会发起修改）")
    cp.submit_button.click()
    expect(logged_in_page.locator(".el-form-item__error:visible")).to_have_count(3)
    assert set(cp.errors()) == {LoginPage.MSG_REQUIRED}, cp.errors()
    print("[Setting] Cancel 返回 Setting 页")
    cp.cancel_button.click()
    logged_in_page.wait_for_url(f"**{SettingPage.PATH}")


@pytest.mark.p2
@pytest.mark.setting
def test_beneficiary_management_list(logged_in_page):
    w = WithdrawPage(logged_in_page)
    w.goto()
    print("\n[Beneficiary] 从 Fiat 提现页进入 Beneficiary Management")
    logged_in_page.get_by_text("Beneficiary Management").first.click()
    logged_in_page.wait_for_url(f"**{BeneficiaryPage.PATH}")
    for col in BeneficiaryPage.COLUMNS:
        expect(logged_in_page.locator("th", has_text=col).first).to_be_visible()
    for btn in ("+ Add", "+ Add in Bulk"):
        expect(logged_in_page.get_by_text(btn, exact=True).first).to_be_visible()
    rows = logged_in_page.locator(".el-table__body tbody tr")
    expect(rows.first).to_be_visible()
    statuses = {r.locator("td").nth(4).inner_text().strip() for r in rows.all()}
    print(f"[Beneficiary] 本页 {rows.count()} 个收款账户，状态 {statuses}")
    assert statuses <= {"Succeeded", "Processing", "Failed", "Rejected", "Action Required"}, statuses


@pytest.mark.p2
@pytest.mark.withdraw
def test_auto_withdraw_strategies(logged_in_page):
    w = WithdrawPage(logged_in_page)
    w.goto()
    print("\n[AutoWithdraw] 点击 Auto Withdrawal 的 Details → 进入策略列表")
    logged_in_page.locator("text=Auto Withdrawal").locator("..").get_by_text("Details", exact=True).first.click()
    logged_in_page.wait_for_url(f"**{AutoWithdrawPage.PATH}")
    for col in AutoWithdrawPage.COLUMNS:
        expect(logged_in_page.locator("th", has_text=col).first).to_be_visible()
    for btn in ("+ Add Crypto Strategy", "+ Add Fiat Strategy"):
        expect(logged_in_page.get_by_text(btn, exact=True).first).to_be_visible()
