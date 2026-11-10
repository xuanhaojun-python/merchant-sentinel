from playwright.sync_api import Locator
from pages.base_page import BasePage


class SettingPage(BasePage):
    PATH = "/setting"

    @property
    def change_password_button(self) -> Locator:
        return self.page.locator("button:has-text('Change Password')").first

    @property
    def two_fa_section(self) -> Locator:
        return self.page.locator("text=Two-Factor Authentication").first

    @property
    def whitelist_section(self) -> Locator:
        return self.page.locator("text=Withdrawal whitelist").first

    @property
    def enable_whitelist_button(self) -> Locator:
        return self.page.locator("button:has-text('Enable whitelist')").first

    @property
    def disable_2fa_entry(self) -> Locator:
        """账号已开启 2FA 时显示「Disable 2FA」入口（非 button 元素）"""
        return self.page.get_by_text("Disable 2FA", exact=True).first
