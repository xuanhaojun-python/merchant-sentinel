from playwright.sync_api import Page
from pages.base_page import BasePage


class DashboardPage(BasePage):
    BALANCE_AMOUNT = "[class*='balance'] [class*='amount'], [data-testid='balance']"
    STATS_CONTAINER = "[class*='stats'], [class*='statistic'], [class*='overview']"
    TRANSACTION_CHART = "[class*='chart'], canvas, [class*='graph']"
    RECENT_ORDERS = "[class*='recent'], [class*='order-list'], table"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/dashboard")

    def get_balance_text(self) -> str:
        return self.wait_for_element(self.BALANCE_AMOUNT).inner_text()

    def is_stats_visible(self) -> bool:
        return self.page.locator(self.STATS_CONTAINER).is_visible()

    def is_chart_visible(self) -> bool:
        return self.page.locator(self.TRANSACTION_CHART).is_visible()

    def is_recent_orders_visible(self) -> bool:
        return self.page.locator(self.RECENT_ORDERS).is_visible()
