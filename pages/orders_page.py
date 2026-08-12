from playwright.sync_api import Page
from pages.base_page import BasePage


class OrdersPage(BasePage):
    ORDER_TABLE = "table, [class*='order-list'], [class*='orders']"
    ORDER_ROW = "table tbody tr, [class*='order-item'], [class*='order-row']"
    SEARCH_INPUT = "input[placeholder*='搜索'], input[placeholder*='search'], input[type='search']"
    STATUS_FILTER = "select[name*='status'], [class*='status-filter'], [class*='filter']"
    ORDER_DETAIL = "[class*='order-detail'], [class*='detail-panel']"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/orders")

    def wait_for_orders_loaded(self) -> None:
        self.wait_for_element(self.ORDER_TABLE)

    def get_order_count(self) -> int:
        self.wait_for_orders_loaded()
        return self.page.locator(self.ORDER_ROW).count()

    def search(self, keyword: str) -> None:
        self.wait_for_element(self.SEARCH_INPUT).fill(keyword)
        self.page.keyboard.press("Enter")
        self.page.wait_for_load_state("networkidle")

    def filter_by_status(self, status: str) -> None:
        self.page.locator(self.STATUS_FILTER).select_option(label=status)
        self.page.wait_for_load_state("networkidle")

    def click_first_order(self) -> None:
        self.page.locator(self.ORDER_ROW).first.click()

    def is_detail_visible(self) -> bool:
        return self.page.locator(self.ORDER_DETAIL).is_visible()
