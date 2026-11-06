import pytest
from playwright.sync_api import expect
from config.settings import settings
from pages.login_page import LoginPage

# 注意：README 约定只允许使用 settings.email 账号；
# 错误密码用例每次运行只尝试 1 次，避免触发账号锁定。


@pytest.fixture
def login_page(fresh_page):
    lp = LoginPage(fresh_page)
    lp.goto()
    return lp


@pytest.mark.smoke
@pytest.mark.login
def test_login_success(login_page):
    print("\n[Login] 输入正确账号密码并提交")
    login_page.login(settings.email, settings.password)

    print("[Login] 跳转离开登录页")
    login_page.wait_for_dashboard()
    expect(login_page.page).not_to_have_url(LoginPage.PATH_PATTERN)


@pytest.mark.login
def test_login_empty_fields(login_page):
    print("\n[Login] 不填写任何内容直接提交")
    login_page.click_submit()

    print("[Login] 邮箱提示格式错误")
    expect(login_page.field_error(LoginPage.MSG_INVALID_EMAIL)).to_be_visible()

    print("[Login] 密码提示必填")
    expect(login_page.field_error(LoginPage.MSG_REQUIRED)).to_be_visible()

    print("[Login] 仍停留在登录页")
    expect(login_page.page).to_have_url(LoginPage.PATH_PATTERN)


@pytest.mark.login
def test_login_invalid_email_format(login_page):
    print("\n[Login] 输入非法邮箱格式并提交")
    login_page.login("not-an-email", "abc12345")

    print("[Login] 邮箱提示格式错误")
    expect(login_page.field_error(LoginPage.MSG_INVALID_EMAIL)).to_be_visible()

    print("[Login] 仍停留在登录页")
    expect(login_page.page).to_have_url(LoginPage.PATH_PATTERN)


@pytest.mark.login
def test_login_wrong_password(login_page):
    print("\n[Login] 输入正确邮箱 + 错误密码并提交")
    login_page.login(settings.email, "WrongPwd_000")

    print("[Login] 提示邮箱或密码错误")
    expect(login_page.toast(LoginPage.MSG_WRONG_CREDENTIALS)).to_be_visible()

    print("[Login] 仍停留在登录页")
    expect(login_page.page).to_have_url(LoginPage.PATH_PATTERN)
