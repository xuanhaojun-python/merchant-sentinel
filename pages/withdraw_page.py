from playwright.sync_api import Page
from pages.base_page import BasePage


class WithdrawPage(BasePage):
    FIAT_TAB = "a[href='/withdraw/fiat']"
    CRYPTO_TAB = "a[href='/withdraw/crypto']"
    DIALOG = ".dialog-content"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        # 直接进 fiat 子路由，确保 tab 高亮
        super().goto("/withdraw/fiat")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1500)
        self._close_dialog_if_present()

    def _close_dialog_if_present(self) -> None:
        dialog = self.page.locator(self.DIALOG).first
        if dialog.is_visible(timeout=1000):
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)

    def is_fiat_tab_active(self) -> bool:
        return "/withdraw/fiat" in self.page.url

    def is_crypto_tab_active(self) -> bool:
        return "/withdraw/crypto" in self.page.url

    def is_fiat_tab_visible(self) -> bool:
        return self.page.locator(self.FIAT_TAB).first.is_visible()

    def is_crypto_tab_visible(self) -> bool:
        return self.page.locator(self.CRYPTO_TAB).first.is_visible()

    def click_crypto_tab(self) -> None:
        self.page.locator(self.CRYPTO_TAB).first.click()
        self.page.wait_for_url("**/withdraw/crypto")
        self._close_dialog_if_present()

    def click_fiat_tab(self) -> None:
        self.page.locator(self.FIAT_TAB).first.click()
        self.page.wait_for_url("**/withdraw/fiat")
        self._close_dialog_if_present()
