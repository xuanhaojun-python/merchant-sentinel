from playwright.sync_api import Locator
from pages.base_page import BasePage


class SettingPage(BasePage):
    PATH = "/setting"
    CHANGE_PASSWORD_BUTTON = "button:has-text('Change Password')"
    TWO_FA_SECTION = "text=Two-Factor Authentication"
    WHITELIST_SECTION = "text=Withdrawal whitelist"
    ENABLE_WHITELIST_BUTTON = "button:has-text('Enable whitelist')"

    @property
    def change_password_button(self) -> Locator:
        return self.page.locator(self.CHANGE_PASSWORD_BUTTON).first

    @property
    def two_fa_section(self) -> Locator:
        return self.page.locator(self.TWO_FA_SECTION).first

    @property
    def whitelist_section(self) -> Locator:
        return self.page.locator(self.WHITELIST_SECTION).first

    @property
    def enable_whitelist_button(self) -> Locator:
        return self.page.locator(self.ENABLE_WHITELIST_BUTTON).first

    @property
    def disable_2fa_entry(self) -> Locator:
        """账号已开启 2FA 时显示「Disable 2FA」入口（非 button 元素）"""
        return self.page.get_by_text("Disable 2FA", exact=True).first


class ChangePasswordPage(BasePage):
    PATH = "/change-password"
    PASSWORD_INPUTS = "input[type=password]:visible"

    @property
    def password_inputs(self) -> Locator:
        return self.page.locator(self.PASSWORD_INPUTS)

    def label(self, text: str) -> Locator:
        return self.page.get_by_text(text, exact=True).first

    @property
    def submit_button(self) -> Locator:
        return self.page.get_by_role("button", name="Submit")

    @property
    def cancel_button(self) -> Locator:
        return self.page.get_by_role("button", name="Cancel")

    def errors(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.FIELD_ERROR_VISIBLE).all_inner_texts()]


class BeneficiaryPage(BasePage):
    PATH = "/beneficiary"
    COLUMNS = ("Account Name", "Account Number/IBAN", "Currency", "Nick Name", "Status", "Action")


class AutoWithdrawPage(BasePage):
    PATH = "/auto-withdraw"
    COLUMNS = ("Strategy Name", "Scenario", "Strategy Parameters", "Withdrawal Amount", "Creation Time", "Status", "Action")
