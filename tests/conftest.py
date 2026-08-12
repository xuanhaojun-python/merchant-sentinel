import pytest
from playwright.sync_api import sync_playwright
from config.settings import settings
from pages.login_page import LoginPage


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=settings.headless, slow_mo=settings.slow_mo)
        yield b
        b.close()


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="function")
def logged_in_page(page):
    login = LoginPage(page)
    login.goto()
    login.login(settings.email, settings.password)
    login.wait_for_dashboard()
    yield page
