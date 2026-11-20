from playwright.sync_api import Locator
from pages.base_page import BasePage


class TreasuryPage(BasePage):
    PATH = "/treasury/index"
    RECOMMENDED_LABEL = "text=Recommended Products"
    MY_POSITIONS = "text=My Positions"
    SUBSCRIBE_BUTTON = "button:has-text('Subscribe')"
    TABLE_COLUMNS = ("Product Name", "Reference APR", "Term", "Minimum Amount")

    @property
    def recommended_products(self) -> Locator:
        return self.page.locator(self.RECOMMENDED_LABEL).first

    @property
    def table_header(self) -> Locator:
        return self.page.locator(self.TABLE_HEADER).first

    @property
    def my_positions_button(self) -> Locator:
        return self.page.locator(self.MY_POSITIONS).first

    @property
    def subscribe_button(self) -> Locator:
        return self.page.locator(self.SUBSCRIBE_BUTTON).first

    def column(self, name: str) -> Locator:
        return self.page.locator(f"th:has-text('{name}')").first

    HOLDING_PATH = "/treasury/holding"
    HOLDING_COLUMNS = ("Product Name", "Reference APR", "Term", "Amount", "Cumulative Total Earnings")

    def product_rows(self) -> list[list[str]]:
        rows = self.page.locator(self.TABLE_BODY_ROW_VISIBLE)
        rows.first.wait_for(state="visible", timeout=30000)
        return [[c.strip() for c in r.locator("td").all_inner_texts()] for r in rows.all()]

    def open_first_detail(self) -> None:
        self.page.locator(self.TABLE_BODY_ROW).first.get_by_text("Detail", exact=True).click()
        self.page.wait_for_url("**/treasury/detail?productId=*")
