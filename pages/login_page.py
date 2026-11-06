import re

from playwright.sync_api import Locator
from pages.base_page import BasePage


class LoginPage(BasePage):
    PATH = "/login"
    PATH_PATTERN = re.compile(r"/login")
    SWITCH_TO_PASSWORD = "a:has-text('Login with password')"
    EMAIL_INPUT = "input[autocomplete='username']"
    # 页面有两个 type=password input，第一个 hidden，第二个是真实输入框
    PASSWORD_INPUT = "input[autocomplete='off'][type='password']"
    SUBMIT_BUTTON = "button[type='submit']"
    ACCEPT_COOKIE = "text=Accept All"
    FIELD_ERROR = ".el-form-item__error"

    MSG_INVALID_EMAIL = "Please enter a valid email address"
    MSG_REQUIRED = "This field is required. Please fill it in."
    MSG_WRONG_CREDENTIALS = "Incorrect email or password"

    def goto(self) -> None:
        super().goto()
        # .mask 是全屏固定遮罩(z-index:1000)，禁用其 pointer-events 才能交互
        self.page.evaluate("() => { const m = document.querySelector('.mask'); if (m) m.style.pointerEvents = 'none'; }")
        cookie_btn = self.page.locator(self.ACCEPT_COOKIE)
        if cookie_btn.is_visible():
            cookie_btn.click()
        # 切换到密码登录模式
        self.wait_for_element(self.SWITCH_TO_PASSWORD, timeout=10000).click()
        self.wait_for_element(self.PASSWORD_INPUT, timeout=5000)

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

    def wait_for_dashboard(self) -> None:
        self.page.wait_for_url(lambda url: "/login" not in url, timeout=60000)

    # ── 断言用 Locator ──
    def field_error(self, text: str) -> Locator:
        return self.page.locator(self.FIELD_ERROR, has_text=text).first

    def toast(self, text: str) -> Locator:
        return self.page.get_by_text(text).first
