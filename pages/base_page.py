from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
from config.settings import settings


class BasePage:
    PATH = ""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.base_url = settings.base_url

    def goto(self, path: str | None = None) -> None:
        target = self.PATH if path is None else path
        self.page.goto(f"{self.base_url}{target}", timeout=settings.timeout_navigation)
        self.page.wait_for_load_state("domcontentloaded")

    def wait_for_element(self, selector: str, timeout: int | None = None) -> Locator:
        locator = self.page.locator(selector).first
        locator.wait_for(state="visible", timeout=timeout or settings.timeout_default)
        return locator

    def dismiss_dialog_if_present(self, timeout: int = 3000) -> None:
        """关闭 Compliance Declaration 弹窗：勾选复选框后点击 Agree and confirm。弹窗未出现则直接返回。"""
        # 页面上有多个 role=dialog 的弹窗（Tips / Withdraw / Receipt ...），按 aria-label 精确定位
        dialog = self.page.get_by_role("dialog", name="Compliance Declaration")
        try:
            dialog.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            return
        checkbox = dialog.locator('input[type="checkbox"]')
        if checkbox.count() > 0:
            checkbox.first.check(force=True)
        dialog.locator('button:has-text("Agree and confirm")').click()
        dialog.wait_for(state="hidden", timeout=5000)
