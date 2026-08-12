from playwright.sync_api import Page, Locator
from config.settings import settings


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.base_url = settings.base_url

    def goto(self, path: str = "") -> None:
        self.page.goto(f"{self.base_url}{path}", timeout=settings.timeout_navigation)

    def wait_for_element(self, selector: str, timeout: int = None) -> Locator:
        t = timeout or settings.timeout_default
        locator = self.page.locator(selector)
        locator.wait_for(state="visible", timeout=t)
        return locator

    def screenshot(self, name: str) -> None:
        self.page.screenshot(path=f"reports/{name}.png", full_page=True)
