"""P0 登录态与菜单可访问：未登录拦截、菜单导航、退出登录、token 失效。"""
import re

import pytest
from playwright.sync_api import expect

from config.settings import settings
from pages.layout import PROTECTED_ROUTES, SIDEBAR_MENUS, TOKEN_COOKIE, AppLayout
from pages.login_page import LoginPage

LOGIN_URL = LoginPage.PATH_PATTERN


@pytest.mark.p0
@pytest.mark.security
@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_protected_route_redirects_to_login(fresh_page, route):
    print(f"\n[Session] 未登录直接访问 {route}")
    fresh_page.goto(f"{settings.base_url}{route}", timeout=settings.timeout_navigation)

    print("[Session] 被拦截到登录页")
    expect(fresh_page).to_have_url(LOGIN_URL)


@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.parametrize("menu", list(SIDEBAR_MENUS))
def test_sidebar_menu_accessible(logged_in_page, menu):
    layout = AppLayout(logged_in_page)
    # 先回到 Wallet 作为统一起点（Wallet 自身用例则从 Setting 出发），保证每次都是一次真实的菜单跳转
    start = "/setting" if menu == "Wallet" else "/wallet/index"
    layout.goto(start)
    layout.dismiss_dialog_if_present()

    print(f"\n[Menu] 点击左侧菜单 {menu}")
    layout.click_menu(menu)

    print(f"[Menu] 跳转到 {SIDEBAR_MENUS[menu].pattern}，且未被踢回登录页")
    expect(logged_in_page).to_have_url(SIDEBAR_MENUS[menu])
    expect(logged_in_page).not_to_have_url(LOGIN_URL)

    print("[Menu] 菜单项处于选中状态")
    expect(layout.sidebar_item(menu).locator("xpath=ancestor-or-self::*[contains(@class,'active')][1]")).to_have_count(1)


@pytest.mark.p0
@pytest.mark.security
@pytest.mark.login
def test_logout_invalidates_session(own_session_page):
    page = own_session_page
    layout = AppLayout(page)
    assert layout.has_token(), "登录后应存在 token cookie"

    print("\n[Logout] 右上角账户菜单 → Logout")
    layout.logout()

    print("[Logout] 回到登录页，token 被清除")
    expect(page).to_have_url(LOGIN_URL)
    assert not layout.has_token(), f"退出后 {TOKEN_COOKIE} 仍存在"

    print("[Logout] 再次访问 Wallet 被拦截")
    page.goto(f"{settings.base_url}/wallet/index")
    expect(page).to_have_url(LOGIN_URL)

    print("[Logout] 浏览器后退也无法回到登录后页面")
    page.go_back()
    expect(page).to_have_url(LOGIN_URL)


@pytest.mark.p0
@pytest.mark.security
def test_cleared_token_redirects_to_login(own_session_page):
    page = own_session_page
    print("\n[Session] 清除 token cookie 模拟会话失效")
    page.context.clear_cookies(name=TOKEN_COOKIE)

    print("[Session] 访问 Transaction 被拦截到登录页")
    page.goto(f"{settings.base_url}/transaction")
    expect(page).to_have_url(LOGIN_URL)


@pytest.mark.p0
@pytest.mark.security
def test_tampered_token_redirects_to_login(own_session_page):
    page = own_session_page
    cookie = next(c for c in page.context.cookies() if c["name"] == TOKEN_COOKIE)

    print("\n[Session] 把 token 篡改为无效值")
    page.context.clear_cookies(name=TOKEN_COOKIE)
    page.context.add_cookies([{**cookie, "value": "invalid-" + cookie["value"][::-1][:24]}])

    print("[Session] 访问 Wallet 被拦截到登录页")
    page.goto(f"{settings.base_url}/wallet/index")
    expect(page).to_have_url(LOGIN_URL, timeout=settings.timeout_default)


@pytest.mark.p0
@pytest.mark.login
def test_login_unregistered_email(fresh_page):
    lp = LoginPage(fresh_page)
    lp.goto()
    print("\n[Login] 使用未注册邮箱登录")
    lp.login("not-registered-" + re.sub(r"\W", "", settings.email)[:12] + "@test.com", "Whatever#123")

    print("[Login] 提示账号或密码错误，停留在登录页")
    expect(lp.toast(LoginPage.MSG_WRONG_CREDENTIALS)).to_be_visible()
    expect(fresh_page).to_have_url(LOGIN_URL)
