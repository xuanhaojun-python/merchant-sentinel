from playwright.sync_api import Page
from pages.base_page import BasePage


class LoginPage(BasePage):
    SWITCH_TO_PASSWORD = "a:has-text('Login with password')"
    SWITCH_TO_CODE = "a:has-text('Login with verification code')"
    EMAIL_INPUT = "input[autocomplete='username']"
    # 页面有两个 type=password input，第一个 hidden，第二个是真实输入框
    PASSWORD_INPUT = "input[autocomplete='off'][type='password']"
    SUBMIT_BUTTON = "button[type='submit']"
    ACCEPT_COOKIE = "text=Accept All"
    ERROR_MESSAGE = ".el-message, .el-form-item__error"
    DASHBOARD_INDICATOR = ".main, header"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/login")
        self.page.wait_for_load_state("networkidle")
        # .mask 是全屏固定遮罩(z-index:1000)，禁用其 pointer-events 才能交互
        self.page.evaluate("() => { const m = document.querySelector('.mask'); if (m) m.style.pointerEvents = 'none'; }")
        # 处理 cookie banner
        cookie_btn = self.page.locator(self.ACCEPT_COOKIE)
        if cookie_btn.is_visible():
            cookie_btn.click()
            self.page.wait_for_timeout(300)
        # 切换到密码登录模式
        switch = self.page.locator(self.SWITCH_TO_PASSWORD)
        switch.wait_for(state="visible", timeout=10000)
        switch.click()
        self.page.wait_for_timeout(500)

    def fill_email(self, email: str) -> None:
        self.wait_for_element(self.EMAIL_INPUT).fill(email)

    def fill_password(self, password: str) -> None:
        self.wait_for_element(self.PASSWORD_INPUT).fill(password)

    def click_submit(self) -> None:
        self.page.locator(self.SUBMIT_BUTTON).click()

    def login(self, email: str, password: str) -> None:
        self.fill_email(email)
        self.fill_password(password)
        self.click_submit()

    def get_error_message(self) -> str:
        locator = self.page.locator(self.ERROR_MESSAGE)
        locator.wait_for(state="visible", timeout=5000)
        return locator.inner_text()

    def wait_for_dashboard(self) -> None:
        # 等待跳转离开登录页
        self.page.wait_for_url(lambda url: "/login" not in url, timeout=60000)
