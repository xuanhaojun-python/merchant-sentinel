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
