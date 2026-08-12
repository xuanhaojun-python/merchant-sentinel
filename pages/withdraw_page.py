from playwright.sync_api import Page
from pages.base_page import BasePage


class WithdrawPage(BasePage):
    AMOUNT_INPUT = "input[name*='amount'], input[placeholder*='金额'], input[placeholder*='amount']"
    ADDRESS_INPUT = "input[name*='address'], input[placeholder*='地址'], input[placeholder*='address']"
    SUBMIT_BUTTON = "button[type='submit'], button:has-text('提现'), button:has-text('Withdraw')"
    CONFIRM_BUTTON = "button:has-text('确认'), button:has-text('Confirm')"
    SUCCESS_MESSAGE = "[class*='success'], [class*='toast-success'], [role='alert']:has-text('成功')"
    ERROR_MESSAGE = "[class*='error'], [class*='toast-error'], [role='alert']:has-text('错误')"
    BALANCE_DISPLAY = "[class*='available'], [class*='balance']"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/withdraw")

    def get_available_balance(self) -> str:
        return self.wait_for_element(self.BALANCE_DISPLAY).inner_text()

    def fill_amount(self, amount: str) -> None:
        self.wait_for_element(self.AMOUNT_INPUT).fill(amount)

    def fill_address(self, address: str) -> None:
        self.wait_for_element(self.ADDRESS_INPUT).fill(address)

    def submit(self) -> None:
        self.page.locator(self.SUBMIT_BUTTON).click()

    def confirm(self) -> None:
        self.page.locator(self.CONFIRM_BUTTON).click()

    def get_success_message(self) -> str:
        locator = self.page.locator(self.SUCCESS_MESSAGE)
        locator.wait_for(state="visible", timeout=10000)
        return locator.inner_text()

    def get_error_message(self) -> str:
        locator = self.page.locator(self.ERROR_MESSAGE)
        locator.wait_for(state="visible", timeout=5000)
        return locator.inner_text()
