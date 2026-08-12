import pytest
from pages.login_page import LoginPage
from config.settings import settings


@pytest.mark.login
def test_login_success(page):
    """正确账号密码可以成功登录并跳转 Dashboard"""
    login = LoginPage(page)
    login.goto()
    login.login(settings.email, settings.password)
    login.wait_for_dashboard()
    assert "/login" not in page.url


@pytest.mark.login
def test_login_wrong_password(page):
    """错误密码显示错误提示"""
    login = LoginPage(page)
    login.goto()
    login.login(settings.email, "wrong_password_123")
    error = login.get_error_message()
    assert error


@pytest.mark.login
def test_login_empty_email(page):
    """空邮箱无法提交"""
    login = LoginPage(page)
    login.goto()
    login.fill_password("somepassword")
    login.click_submit()
    assert "/login" in page.url or page.locator(login.EMAIL_INPUT).is_visible()
