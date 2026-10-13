from playwright.sync_api import Page
from pages.base_page import BasePage


class DashboardPage(BasePage):
    WELCOME_HEADING = "h1"
    BALANCE_CARD = "[class*=balance]"
    DEPOSIT_BUTTON = "button:has-text('Deposit')"
    CURRENCIES_SECTION = "text=All Currencies"
    ACTION_DEPOSIT = ".btn-wrap button:has-text('Deposit')"
    ACTION_CONVERT = ".btn-wrap button:has-text('Convert')"
    ACTION_WITHDRAW = ".btn-wrap button:has-text('Withdraw')"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/wallet/index")
        self.page.wait_for_load_state("networkidle")

    def is_welcome_visible(self) -> bool:
        return self.page.locator(self.WELCOME_HEADING).first.is_visible()

    def is_balance_card_visible(self) -> bool:
        return self.page.locator(self.BALANCE_CARD).first.is_visible()

    def is_deposit_button_visible(self) -> bool:
        return self.page.locator(self.DEPOSIT_BUTTON).first.is_visible()

    def is_currencies_section_visible(self) -> bool:
        return self.page.locator(self.CURRENCIES_SECTION).first.is_visible()

    def click_action_deposit(self) -> None:
        self.page.locator(self.ACTION_DEPOSIT).click()
        self.page.wait_for_url("**/deposit/**", timeout=10000)

    def click_action_convert(self) -> None:
        self.page.locator(self.ACTION_CONVERT).click()
        self.page.wait_for_url("**/convert**", timeout=10000)

    def click_action_withdraw(self) -> None:
        self.page.locator(self.ACTION_WITHDRAW).click()
        self.page.wait_for_url("**/withdraw/**", timeout=10000)
