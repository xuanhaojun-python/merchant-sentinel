import pytest
from pages.setting_page import SettingPage


@pytest.mark.smoke
@pytest.mark.setting
def test_setting(logged_in_page):
    setting = SettingPage(logged_in_page)
    setting.goto()

    print("\n[Setting] Change Password 按钮可见")
    assert setting.is_change_password_visible()

    print("[Setting] Two-Factor Authentication 区块可见")
    assert setting.is_2fa_section_visible()

    print("[Setting] Withdrawal whitelist 区块可见")
    assert setting.is_whitelist_section_visible()

    print("[Setting] Enable whitelist 按钮可见")
    assert setting.is_enable_whitelist_visible()
