from playwright.sync_api import Page
from pages.base_page import BasePage


class OrdersPage(BasePage):
    ORDER_TABLE = "table.el-table__header"
    ORDER_ROW = "table.el-table__body tbody tr"
    SEARCH_BUTTON = "button:has-text('Search')"
    RESET_BUTTON = "button:has-text('Reset')"
    ORDER_DETAIL = "[class*='order-detail'], [class*='detail-panel']"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/transaction")
        self.page.wait_for_load_state("networkidle")

    def wait_for_orders_loaded(self) -> None:
        self.wait_for_element(self.ORDER_TABLE)

    def get_order_count(self) -> int:
        return self.page.locator(self.ORDER_ROW).count()

    def search(self, keyword: str) -> None:
        self.page.locator(self.SEARCH_BUTTON).click()
        self.page.wait_for_load_state("networkidle")

    def click_first_order(self) -> None:
        self.page.locator(self.ORDER_ROW).first.click()

    def is_detail_visible(self) -> bool:
        return self.page.locator(self.ORDER_DETAIL).first.is_visible()
