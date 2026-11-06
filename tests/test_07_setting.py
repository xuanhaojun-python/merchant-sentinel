import pytest
from playwright.sync_api import expect
from pages.setting_page import SettingPage


@pytest.mark.smoke
@pytest.mark.setting
def test_setting(logged_in_page):
    setting = SettingPage(logged_in_page)
    setting.goto()

    print("\n[Setting] Change Password 按钮可见")
    expect(setting.change_password_button).to_be_visible()

    print("[Setting] Two-Factor Authentication 区块可见")
    expect(setting.two_fa_section).to_be_visible()

    print("[Setting] Withdrawal whitelist 区块可见")
    expect(setting.whitelist_section).to_be_visible()

    print("[Setting] Enable whitelist 按钮可见")
    expect(setting.enable_whitelist_button).to_be_visible()
