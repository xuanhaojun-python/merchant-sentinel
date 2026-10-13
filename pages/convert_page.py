from playwright.sync_api import Page
from pages.base_page import BasePage


class ConvertPage(BasePage):
    SELL_LABEL = "text=Sell"
    BUY_LABEL = "text=Buy"
    SELL_AMOUNT_INPUT = "input[placeholder^='Min:']"
    SUBMIT_BUTTON = "button:has-text('Submit')"
    AVAILABLE_BALANCE = "text=Available Balance"
    NOTICE_BANNER = "text=Please note that this final convert"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/convert")
        self.page.wait_for_load_state("networkidle")

    def is_page_loaded(self) -> bool:
        return self.page.locator(self.SUBMIT_BUTTON).is_visible()

    def is_sell_section_visible(self) -> bool:
        return self.page.locator(self.SELL_LABEL).first.is_visible()

    def is_buy_section_visible(self) -> bool:
        return self.page.locator(self.BUY_LABEL).first.is_visible()

    def is_available_balance_visible(self) -> bool:
        return self.page.locator(self.AVAILABLE_BALANCE).is_visible()

    def is_notice_visible(self) -> bool:
        return self.page.locator(self.NOTICE_BANNER).is_visible()

    def fill_sell_amount(self, amount: str) -> None:
        self.wait_for_element(self.SELL_AMOUNT_INPUT).fill(amount)
