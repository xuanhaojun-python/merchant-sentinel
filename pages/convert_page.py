from playwright.sync_api import Locator
from pages.base_page import BasePage


class ConvertPage(BasePage):
    PATH = "/convert"
    SELL_AMOUNT_INPUT = "input[placeholder^='Min:']"

    @property
    def submit_button(self) -> Locator:
        return self.page.locator("button:has-text('Submit')").first

    @property
    def sell_section(self) -> Locator:
        return self.page.locator("text=Sell").first

    @property
    def buy_section(self) -> Locator:
        return self.page.locator("text=Buy").first

    @property
    def available_balance(self) -> Locator:
        return self.page.locator("text=Available Balance").first

    @property
    def notice_banner(self) -> Locator:
        return self.page.locator("text=Please note that this final convert").first

    def fill_sell_amount(self, amount: str) -> None:
        self.wait_for_element(self.SELL_AMOUNT_INPUT).fill(amount)
