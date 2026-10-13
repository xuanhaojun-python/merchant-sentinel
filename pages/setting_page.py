from playwright.sync_api import Page
from pages.base_page import BasePage


class SettingPage(BasePage):
    SECURITY_SECTION = "h2:has-text('Security')"
    CHANGE_PASSWORD_BUTTON = "button:has-text('Change Password')"
    TWO_FA_SECTION = "text=Two-Factor Authentication"
    WHITELIST_SECTION = "text=Withdrawal whitelist"
    ENABLE_WHITELIST_BUTTON = "button:has-text('Enable whitelist')"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/setting")
        self.page.wait_for_load_state("networkidle")

    def is_page_loaded(self) -> bool:
        return self.page.locator(self.CHANGE_PASSWORD_BUTTON).is_visible()

    def is_change_password_visible(self) -> bool:
        return self.page.locator(self.CHANGE_PASSWORD_BUTTON).is_visible()

    def is_2fa_section_visible(self) -> bool:
        return self.page.locator(self.TWO_FA_SECTION).is_visible()

    def is_whitelist_section_visible(self) -> bool:
        return self.page.locator(self.WHITELIST_SECTION).is_visible()

    def is_enable_whitelist_visible(self) -> bool:
        return self.page.locator(self.ENABLE_WHITELIST_BUTTON).is_visible()
