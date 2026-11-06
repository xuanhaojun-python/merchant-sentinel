import re

from playwright.sync_api import Locator, TimeoutError as PlaywrightTimeoutError
from pages.base_page import BasePage


class WithdrawPage(BasePage):
    # 直接进 fiat 子路由，确保 tab 高亮
    PATH = "/withdraw/fiat"
    FIAT_TAB = "a[href='/withdraw/fiat']"
    CRYPTO_TAB = "a[href='/withdraw/crypto']"
    DIALOG = ".dialog-content"

    FIAT_URL = re.compile(r"/withdraw/fiat")
    CRYPTO_URL = re.compile(r"/withdraw/crypto")

    def goto(self) -> None:
        super().goto()
        self.fiat_tab.wait_for(state="visible")
        self._close_dialog_if_present(timeout=2000)

    def _close_dialog_if_present(self, timeout: int = 1000) -> None:
        dialog = self.page.locator(self.DIALOG).first
        try:
            dialog.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            return
        self.page.keyboard.press("Escape")
        dialog.wait_for(state="hidden", timeout=3000)

    @property
    def fiat_tab(self) -> Locator:
        return self.page.locator(self.FIAT_TAB).first

    @property
    def crypto_tab(self) -> Locator:
        return self.page.locator(self.CRYPTO_TAB).first

    def click_crypto_tab(self) -> None:
        self.crypto_tab.click()
        self.page.wait_for_url("**/withdraw/crypto")
        self._close_dialog_if_present()

    def click_fiat_tab(self) -> None:
        self.fiat_tab.click()
        self.page.wait_for_url("**/withdraw/fiat")
        self._close_dialog_if_present()
