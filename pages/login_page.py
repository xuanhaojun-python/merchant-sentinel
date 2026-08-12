from playwright.sync_api import Page
from pages.base_page import BasePage


class LoginPage(BasePage):
    EMAIL_INPUT = "input[type='email'], input[name='email'], #email"
    PASSWORD_INPUT = "input[type='password'], input[name='password'], #password"
    SUBMIT_BUTTON = "button[type='submit'], button:has-text('登录'), button:has-text('Login')"
    ERROR_MESSAGE = ".error-message, [class*='error'], [role='alert']"
    DASHBOARD_INDICATOR = "[class*='dashboard'], [class*='main'], nav, .sidebar"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/login")

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
        self.wait_for_element(self.DASHBOARD_INDICATOR, timeout=60000)
