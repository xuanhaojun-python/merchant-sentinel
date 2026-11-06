from playwright.sync_api import Locator, TimeoutError as PlaywrightTimeoutError
from pages.base_page import BasePage


class TransactionPage(BasePage):
    PATH = "/transaction"
    TABLE_ROW = "table.el-table__body tbody tr"

    @property
    def search_button(self) -> Locator:
        return self.page.locator("button:has-text('Search')").first

    @property
    def reset_button(self) -> Locator:
        return self.page.locator("button:has-text('Reset')").first

    @property
    def export_button(self) -> Locator:
        return self.page.locator("button:has-text('Export')").first

    @property
    def table(self) -> Locator:
        return self.page.locator("table.el-table__header").first

    def row_count(self, timeout: int = 10000) -> int:
        """等待数据行渲染后返回行数；超时仍无数据行且显示"无数据"提示则返回 0。

        注意：Search 后表格重新加载期间会短暂出现空状态，因此优先等待数据行，而不是二者取先。
        """
        rows = self.page.locator(self.TABLE_ROW)
        try:
            rows.first.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            self.page.locator(".el-table__empty-text").first.wait_for(state="visible")
            return 0
        return rows.count()

    def click_search(self) -> None:
        self.search_button.click()

    def click_reset(self) -> None:
        self.reset_button.click()
