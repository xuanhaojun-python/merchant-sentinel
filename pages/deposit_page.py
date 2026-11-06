from playwright.sync_api import Locator
from pages.base_page import BasePage


class DepositPage(BasePage):
    PATH = "/deposit/crypto"

    @property
    def crypto_tab(self) -> Locator:
        return self.page.locator("a:has-text('Crypto')").first

    @property
    def fiat_tab(self) -> Locator:
        return self.page.locator("a:has-text('Fiat')").first

    @property
    def currency_selector(self) -> Locator:
        return self.page.locator("text=Select Deposit Currency").first

    @property
    def network_selector(self) -> Locator:
        return self.page.locator("text=Confirm Network").first

    @property
    def deposit_address(self) -> Locator:
        return self.page.locator("text=Deposit Address").first

    def click_fiat_tab(self) -> None:
        self.fiat_tab.click()
        self.page.wait_for_url("**/deposit/fiat**")
