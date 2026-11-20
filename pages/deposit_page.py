from playwright.sync_api import Locator
from pages.base_page import BasePage


class DepositPage(BasePage):
    PATH = "/deposit/crypto"
    CRYPTO_TAB = "a:has-text('Crypto')"
    FIAT_TAB = "a:has-text('Fiat')"
    CURRENCY_LABEL = "text=Select Deposit Currency"
    NETWORK_LABEL = "text=Confirm Network"
    ADDRESS_LABEL = "text=Deposit Address"
    ADDRESS_BLOCK = "[class*=address]"
    CONTENT = ".right-content"

    @property
    def crypto_tab(self) -> Locator:
        return self.page.locator(self.CRYPTO_TAB).first

    @property
    def fiat_tab(self) -> Locator:
        return self.page.locator(self.FIAT_TAB).first

    @property
    def currency_selector(self) -> Locator:
        return self.page.locator(self.CURRENCY_LABEL).first

    @property
    def network_selector(self) -> Locator:
        return self.page.locator(self.NETWORK_LABEL).first

    @property
    def deposit_address(self) -> Locator:
        return self.page.locator(self.ADDRESS_LABEL).first

    def click_fiat_tab(self) -> None:
        self.fiat_tab.click()
        self.page.wait_for_url("**/deposit/fiat**")

    # ── 币种 / 网络 / 地址（2026-11-19 SIT 实测）──
    def _select(self, idx: int) -> Locator:
        return self.page.locator(self.SELECT_BOX).nth(idx).locator(self.SELECT_TRIGGER).first

    def options(self, idx: int) -> list[str]:
        """idx=0 币种，1 网络。"""
        self._select(idx).click()
        items = self.page.locator(self.DROPDOWN_ITEM)
        items.first.wait_for(state="visible")
        opts = [t.strip() for t in items.all_inner_texts()]
        self.page.keyboard.press("Escape")
        items.first.wait_for(state="hidden")
        return opts

    def choose(self, idx: int, value: str) -> None:
        self._select(idx).click()
        self.page.locator(self.DROPDOWN_ITEM).get_by_text(value, exact=True).first.click()
        self.page.wait_for_timeout(1500)

    def selected(self, idx: int) -> str:
        return self._select(idx).inner_text().strip()

    def address(self) -> str:
        """Deposit Address 下方显示的地址。"""
        block = self.page.locator(self.ADDRESS_BLOCK, has_text="Deposit Address").first
        lines = [l.strip() for l in block.inner_text().split("\n") if l.strip() and l.strip() != "Deposit Address"]
        return lines[0] if lines else ""

    def page_text(self) -> str:
        return self.page.locator(self.CONTENT).first.inner_text()
