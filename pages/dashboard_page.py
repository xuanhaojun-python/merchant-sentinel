from playwright.sync_api import Locator
from pages.base_page import BasePage


class DashboardPage(BasePage):
    PATH = "/wallet/index"
    ACTION_DEPOSIT = ".btn-wrap button:has-text('Deposit')"
    ACTION_CONVERT = ".btn-wrap button:has-text('Convert')"
    ACTION_WITHDRAW = ".btn-wrap button:has-text('Withdraw')"

    def goto(self) -> None:
        super().goto()
        self.dismiss_dialog_if_present()

    @property
    def welcome_heading(self) -> Locator:
        return self.page.locator("h1").first

    @property
    def balance_card(self) -> Locator:
        return self.page.locator("[class*=balance]").first

    @property
    def deposit_button(self) -> Locator:
        return self.page.locator("button:has-text('Deposit')").first

    @property
    def currencies_section(self) -> Locator:
        return self.page.locator("text=All Currencies").first

    def click_action_deposit(self) -> None:
        self.page.locator(self.ACTION_DEPOSIT).click()
        self.page.wait_for_url("**/deposit/**", timeout=10000)

    def click_action_convert(self) -> None:
        self.page.locator(self.ACTION_CONVERT).click()
        self.page.wait_for_url("**/convert**", timeout=10000)

    def click_action_withdraw(self) -> None:
        self.page.locator(self.ACTION_WITHDRAW).click()
        self.page.wait_for_url("**/withdraw/**", timeout=10000)
