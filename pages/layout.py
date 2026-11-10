import re

from playwright.sync_api import Locator
from pages.base_page import BasePage

TOKEN_COOKIE = "lepton-token"

# 左侧菜单 → (落地 URL 正则)。2026-11-10 SIT 实测
SIDEBAR_MENUS = {
    "Wallet": re.compile(r"/wallet/index"),
    "Deposit": re.compile(r"/deposit/"),
    "Treasury": re.compile(r"/treasury/"),
    "Withdraw": re.compile(r"/withdraw/fiat"),
    "Convert": re.compile(r"/convert"),
    "Transaction": re.compile(r"/transaction"),
    "Setting": re.compile(r"/setting"),
}

# 未登录时应被拦截到 /login 的路由
PROTECTED_ROUTES = [
    "/wallet/index", "/deposit/crypto", "/deposit/fiat", "/treasury/index",
    "/withdraw/fiat", "/withdraw/crypto", "/convert", "/transaction", "/setting",
]


class AppLayout(BasePage):
    """登录后的公共布局：左侧菜单 + 右上角账户菜单。"""

    SIDEBAR = "nav, aside, [class*=sidebar], [class*=menu]"

    def sidebar_item(self, name: str) -> Locator:
        return self.page.locator(self.SIDEBAR).get_by_text(name, exact=True).first

    def click_menu(self, name: str) -> None:
        self.sidebar_item(name).click()
        self.page.wait_for_url(SIDEBAR_MENUS[name])
        self.dismiss_dialog_if_present()

    @property
    def account_menu(self) -> Locator:
        return self.page.locator(".el-dropdown-menu:visible", has_text="Logout")

    def logout(self) -> None:
        # 账户下拉的触发元素：通过菜单的 aria-labelledby 反查，页面上有两个 .account-wrap
        trigger_id = self.page.locator(".el-dropdown-menu", has_text="Logout").first.get_attribute("aria-labelledby")
        self.page.locator(f"[id='{trigger_id}']").hover()
        self.account_menu.get_by_text("Logout", exact=True).click()

    def has_token(self) -> bool:
        return any(c["name"] == TOKEN_COOKIE for c in self.page.context.cookies())
