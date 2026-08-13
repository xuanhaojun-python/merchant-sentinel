from playwright.sync_api import Page
from pages.base_page import BasePage


class TransactionPage(BasePage):
    SEARCH_BUTTON = "button:has-text('Search')"
    RESET_BUTTON = "button:has-text('Reset')"
    EXPORT_BUTTON = "button:has-text('Export')"
    TABLE = "table.el-table__header"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/transaction")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def is_page_loaded(self) -> bool:
        return self.page.locator(self.SEARCH_BUTTON).is_visible()

    def is_table_visible(self) -> bool:
        return self.page.locator(self.TABLE).first.is_visible()

    def click_search(self) -> None:
        self.page.locator(self.SEARCH_BUTTON).click()
        self.page.wait_for_load_state("networkidle")

    def click_reset(self) -> None:
        self.page.locator(self.RESET_BUTTON).click()
        self.page.wait_for_timeout(500)

    def click_export(self) -> None:
        self.page.locator(self.EXPORT_BUTTON).click()
        self.page.wait_for_timeout(1000)
