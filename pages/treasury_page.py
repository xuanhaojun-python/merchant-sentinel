from playwright.sync_api import Locator
from pages.base_page import BasePage


class TreasuryPage(BasePage):
    PATH = "/treasury/index"
    TABLE_COLUMNS = ("Product Name", "Reference APR", "Term", "Minimum Amount")

    @property
    def recommended_products(self) -> Locator:
        return self.page.locator("text=Recommended Products").first

    @property
    def table_header(self) -> Locator:
        return self.page.locator("table.el-table__header").first

    @property
    def my_positions_button(self) -> Locator:
        return self.page.locator("text=My Positions").first

    @property
    def subscribe_button(self) -> Locator:
        return self.page.locator("button:has-text('Subscribe')").first

    def column(self, name: str) -> Locator:
        return self.page.locator(f"th:has-text('{name}')").first
