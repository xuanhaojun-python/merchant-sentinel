import pytest
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from config.settings import settings


def fresh_login(email, password):
    """用独立 browser 做登录测试，不影响 session 状态"""
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    return p, browser, context, page


@pytest.mark.login
def test_login_success():
    """正确账号密码可以成功登录并跳转离开登录页"""
    p, browser, context, page = fresh_login(settings.email, settings.password)
    try:
        login = LoginPage(page)
        login.goto()
        login.login(settings.email, settings.password)
        login.wait_for_dashboard()
        assert "/login" not in page.url
    finally:
        context.close()
        browser.close()
        p.stop()


@pytest.mark.login
def test_login_wrong_password():
    """错误密码显示错误提示"""
    p, browser, context, page = fresh_login(settings.email, "wrong_password_123")
    try:
        login = LoginPage(page)
        login.goto()
        login.login(settings.email, "wrong_password_123")
        error = login.get_error_message()
        assert error
    finally:
        context.close()
        browser.close()
        p.stop()


@pytest.mark.login
def test_login_empty_email():
    """空邮箱点击提交，停在登录页"""
    p, browser, context, page = fresh_login("", "somepassword")
    try:
        login = LoginPage(page)
        login.goto()
        login.fill_password("somepassword")
        login.click_submit()
        page.wait_for_timeout(1000)
        assert "/login" in page.url
    finally:
        context.close()
        browser.close()
        p.stop()
