import pytest
from playwright.sync_api import sync_playwright
from config.settings import settings
from pages.login_page import LoginPage


@pytest.fixture(scope="session")
def browser_context():
    """启动一次浏览器，登录一次，保存 storage state，整个 session 复用"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.headless, slow_mo=settings.slow_mo)
        context = browser.new_context()
        page = context.new_page()

        # 登录一次
        login = LoginPage(page)
        login.goto()
        login.login(settings.email, settings.password)
        login.wait_for_dashboard()

        # 保存登录 state
        storage = context.storage_state()
        page.close()
        context.close()

        yield browser, storage
        browser.close()


@pytest.fixture(scope="function")
def page(browser_context):
    """每个测试用新 page，但复用已登录的 cookies/storage"""
    browser, storage = browser_context
    context = browser.new_context(storage_state=storage)
    pg = context.new_page()
    yield pg
    context.close()


@pytest.fixture(scope="function")
def logged_in_page(page):
    """已登录状态的 page，直接跳到 wallet"""
    page.goto(f"{settings.base_url}/wallet/index")
    page.wait_for_load_state("networkidle")
    yield page
