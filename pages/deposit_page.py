from playwright.sync_api import Page
from pages.base_page import BasePage


class DepositPage(BasePage):
    CRYPTO_TAB = "a:has-text('Crypto')"
    FIAT_TAB = "a:has-text('Fiat')"
    CURRENCY_SELECTOR = "text=Select Deposit Currency"
    NETWORK_SELECTOR = "text=Confirm Network"
    DEPOSIT_ADDRESS = "text=Deposit Address"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/deposit/crypto")
        self.page.wait_for_load_state("networkidle")

    def is_crypto_tab_visible(self) -> bool:
        return self.page.locator(self.CRYPTO_TAB).first.is_visible()

    def is_fiat_tab_visible(self) -> bool:
        return self.page.locator(self.FIAT_TAB).first.is_visible()

    def is_currency_selector_visible(self) -> bool:
        return self.page.locator(self.CURRENCY_SELECTOR).first.is_visible()

    def is_network_selector_visible(self) -> bool:
        return self.page.locator(self.NETWORK_SELECTOR).first.is_visible()

    def is_deposit_address_visible(self) -> bool:
        return self.page.locator(self.DEPOSIT_ADDRESS).first.is_visible()

    def click_fiat_tab(self) -> None:
        self.page.locator(self.FIAT_TAB).first.click()
        self.page.wait_for_load_state("networkidle")
