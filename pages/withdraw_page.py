import re

from playwright.sync_api import Locator, TimeoutError as PlaywrightTimeoutError
from pages.base_page import BasePage


class WithdrawPage(BasePage):
    # 直接进 fiat 子路由，确保 tab 高亮
    PATH = "/withdraw/fiat"
    FIAT_TAB = "a[href='/withdraw/fiat']"
    CRYPTO_TAB = "a[href='/withdraw/crypto']"
    DIALOG = ".dialog-content"
    AMOUNT_INPUT = "input[placeholder^='Min:']"
    SUBMIT_BUTTON_NAME = "Withdraw Authentication"

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

    # ── 下单表单 ──
    @property
    def amount_input(self) -> Locator:
        return self.page.locator(self.AMOUNT_INPUT).first

    @property
    def submit_button(self) -> Locator:
        """表单完整前为禁用状态；点击后弹出 Withdrawal Confirmation（含 2FA），不会直接下单。"""
        return self.page.get_by_role("button", name=self.SUBMIT_BUTTON_NAME)

    def select_first_beneficiary(self) -> None:
        item = self.page.locator(".el-form-item", has_text="Beneficiary Account").first
        item.locator(".el-select__wrapper").first.click()
        self.page.locator(".el-select-dropdown__item:visible").first.click()

    # ── Withdrawal Confirmation 弹窗 ──
    @property
    def confirm_dialog(self) -> Locator:
        return self.page.get_by_role("dialog").filter(has_text="Withdrawal Confirmation")

    @property
    def two_fa_input(self) -> Locator:
        return self.confirm_dialog.locator("input[placeholder*='Google Authenticator']").first

    @property
    def confirm_button(self) -> Locator:
        return self.confirm_dialog.get_by_role("button", name="Confirm")

    @property
    def cancel_button(self) -> Locator:
        return self.confirm_dialog.get_by_role("button", name="Cancel")

    def field_error(self, scope: Locator | None = None) -> Locator:
        return (scope or self.page).locator(".el-form-item__error:visible").first
