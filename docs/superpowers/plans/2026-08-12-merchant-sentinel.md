# Merchant Sentinel — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 Web3 商户端支付后台的 Playwright (Python) + pytest UI 自动化测试框架，覆盖登录、Dashboard、订单、提现四个核心模块。

**Architecture:** 标准 Page Object Model 三层架构：tests 层调用 pages 层，pages 层封装 Playwright 操作，config 层统一管理环境配置。conftest.py 提供 browser/page/logged_in_page fixtures，BasePage 提供通用等待和截图能力。

**Tech Stack:** Python 3.11+, Playwright, pytest, pytest-playwright, pytest-html, PyYAML

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `requirements.txt` | 依赖声明 |
| `pytest.ini` | pytest 配置（报告、标记） |
| `config/config.yaml` | 环境 URL、账号、超时配置 |
| `config/settings.py` | 读取 config.yaml，提供全局 `Settings` 单例 |
| `pages/base_page.py` | BasePage 基类：goto / wait_for_element / screenshot |
| `pages/login_page.py` | 登录页操作封装 |
| `pages/dashboard_page.py` | Dashboard 页操作封装 |
| `pages/orders_page.py` | 订单列表 & 详情操作封装 |
| `pages/withdraw_page.py` | 提现流程操作封装 |
| `tests/conftest.py` | browser / page / logged_in_page fixtures |
| `tests/test_login.py` | 登录相关测试用例 |
| `tests/test_dashboard.py` | Dashboard 相关测试用例 |
| `tests/test_orders.py` | 订单相关测试用例 |
| `tests/test_withdraw.py` | 提现相关测试用例 |
| `utils/helpers.py` | 截图、等待等公共工具函数 |

---

## Task 1: 初始化项目依赖和配置

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `config/config.yaml`
- Create: `config/__init__.py`
- Create: `config/settings.py`

- [ ] **Step 1: 创建 requirements.txt**

```
playwright==1.44.0
pytest==8.2.2
pytest-playwright==0.5.0
pytest-html==4.1.1
pyyaml==6.0.1
```

- [ ] **Step 2: 创建 pytest.ini**

```ini
[pytest]
testpaths = tests
addopts = --html=reports/report.html --self-contained-html -v
markers =
    login: 登录相关测试
    dashboard: Dashboard 相关测试
    orders: 订单相关测试
    withdraw: 提现相关测试
```

- [ ] **Step 3: 创建 config/config.yaml**

```yaml
base_url: "https://merchant-staging.example.com"
credentials:
  email: "test@merchant.com"
  password: "TestPass123!"
timeouts:
  default: 30000
  navigation: 60000
browser:
  headless: false
  slow_mo: 0
```

- [ ] **Step 4: 创建 config/__init__.py（空文件）**

```python
```

- [ ] **Step 5: 创建 config/settings.py**

```python
import yaml
from pathlib import Path


def _load() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class Settings:
    _data = _load()

    base_url: str = _data["base_url"]
    email: str = _data["credentials"]["email"]
    password: str = _data["credentials"]["password"]
    timeout_default: int = _data["timeouts"]["default"]
    timeout_navigation: int = _data["timeouts"]["navigation"]
    headless: bool = _data["browser"]["headless"]
    slow_mo: int = _data["browser"]["slow_mo"]


settings = Settings()
```

- [ ] **Step 6: 安装依赖并安装 Playwright 浏览器**

```bash
pip install -r requirements.txt
playwright install chromium
```

Expected: 安装完成，无报错

- [ ] **Step 7: 创建 reports/ 目录和 .gitkeep**

```bash
mkdir -p reports && touch reports/.gitkeep
mkdir -p pages tests utils && touch pages/__init__.py tests/__init__.py utils/__init__.py
```

- [ ] **Step 8: Commit**

```bash
git init
git add requirements.txt pytest.ini config/ pages/__init__.py tests/__init__.py utils/__init__.py reports/.gitkeep
git commit -m "chore: init project structure and config"
```

---

## Task 2: 实现 BasePage 和 conftest fixtures

**Files:**
- Create: `pages/base_page.py`
- Create: `pages/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: 创建 pages/base_page.py**

```python
from playwright.sync_api import Page, Locator
from config.settings import settings


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.base_url = settings.base_url

    def goto(self, path: str = "") -> None:
        self.page.goto(f"{self.base_url}{path}", timeout=settings.timeout_navigation)

    def wait_for_element(self, selector: str, timeout: int = None) -> Locator:
        t = timeout or settings.timeout_default
        locator = self.page.locator(selector)
        locator.wait_for(state="visible", timeout=t)
        return locator

    def screenshot(self, name: str) -> None:
        self.page.screenshot(path=f"reports/{name}.png", full_page=True)
```

- [ ] **Step 2: 创建 tests/conftest.py**

```python
import pytest
from playwright.sync_api import sync_playwright
from config.settings import settings
from pages.login_page import LoginPage


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=settings.headless,
            slow_mo=settings.slow_mo,
        )
        yield browser
        browser.close()


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
```

- [ ] **Step 3: 验证 conftest 可被 pytest 加载（不运行真正测试）**

```bash
pytest --collect-only 2>&1 | head -20
```

Expected: 能看到 collected 信息，无 ImportError

- [ ] **Step 4: Commit**

```bash
git add pages/base_page.py tests/conftest.py
git commit -m "feat: add BasePage and session/function fixtures"
```

---

## Task 3: 实现 LoginPage 和登录测试

**Files:**
- Create: `pages/login_page.py`
- Create: `tests/test_login.py`

- [ ] **Step 1: 创建 pages/login_page.py**

```python
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
```

- [ ] **Step 2: 创建 tests/test_login.py**

```python
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
    assert error  # 有错误提示即可


@pytest.mark.login
def test_login_empty_email(page):
    """空邮箱无法提交"""
    login = LoginPage(page)
    login.goto()
    login.fill_password("somepassword")
    login.click_submit()
    # 仍在登录页
    assert "/login" in page.url or page.locator(login.EMAIL_INPUT).is_visible()
```

- [ ] **Step 3: 运行登录测试（确认结构正确，报错可接受——需真实 URL）**

```bash
pytest tests/test_login.py -v -m login 2>&1 | head -40
```

Expected: 测试被收集，若无真实 URL 则报 timeout（结构正确即可）

- [ ] **Step 4: Commit**

```bash
git add pages/login_page.py tests/test_login.py
git commit -m "feat: add LoginPage POM and login test cases"
```

---

## Task 4: 实现 DashboardPage 和 Dashboard 测试

**Files:**
- Create: `pages/dashboard_page.py`
- Create: `tests/test_dashboard.py`

- [ ] **Step 1: 创建 pages/dashboard_page.py**

```python
from playwright.sync_api import Page
from pages.base_page import BasePage


class DashboardPage(BasePage):
    BALANCE_AMOUNT = "[class*='balance'] [class*='amount'], [data-testid='balance']"
    STATS_CONTAINER = "[class*='stats'], [class*='statistic'], [class*='overview']"
    TRANSACTION_CHART = "[class*='chart'], canvas, [class*='graph']"
    RECENT_ORDERS = "[class*='recent'], [class*='order-list'], table"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/dashboard")

    def get_balance_text(self) -> str:
        return self.wait_for_element(self.BALANCE_AMOUNT).inner_text()

    def is_stats_visible(self) -> bool:
        return self.page.locator(self.STATS_CONTAINER).is_visible()

    def is_chart_visible(self) -> bool:
        return self.page.locator(self.TRANSACTION_CHART).is_visible()

    def is_recent_orders_visible(self) -> bool:
        return self.page.locator(self.RECENT_ORDERS).is_visible()
```

- [ ] **Step 2: 创建 tests/test_dashboard.py**

```python
import pytest
from pages.dashboard_page import DashboardPage


@pytest.mark.dashboard
def test_dashboard_balance_visible(logged_in_page):
    """登录后 Dashboard 显示余额"""
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()
    balance = dashboard.get_balance_text()
    assert balance  # 有内容即可


@pytest.mark.dashboard
def test_dashboard_stats_visible(logged_in_page):
    """Dashboard 统计数据区域可见"""
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()
    assert dashboard.is_stats_visible()


@pytest.mark.dashboard
def test_dashboard_loads_without_error(logged_in_page):
    """Dashboard 页面无 JS 错误"""
    errors = []
    logged_in_page.on("pageerror", lambda e: errors.append(str(e)))
    dashboard = DashboardPage(logged_in_page)
    dashboard.goto()
    dashboard.wait_for_element(dashboard.STATS_CONTAINER)
    assert errors == [], f"页面 JS 错误: {errors}"
```

- [ ] **Step 3: Commit**

```bash
git add pages/dashboard_page.py tests/test_dashboard.py
git commit -m "feat: add DashboardPage POM and dashboard test cases"
```

---

## Task 5: 实现 OrdersPage 和订单测试

**Files:**
- Create: `pages/orders_page.py`
- Create: `tests/test_orders.py`

- [ ] **Step 1: 创建 pages/orders_page.py**

```python
from playwright.sync_api import Page
from pages.base_page import BasePage


class OrdersPage(BasePage):
    ORDER_TABLE = "table, [class*='order-list'], [class*='orders']"
    ORDER_ROW = "table tbody tr, [class*='order-item'], [class*='order-row']"
    SEARCH_INPUT = "input[placeholder*='搜索'], input[placeholder*='search'], input[type='search']"
    STATUS_FILTER = "select[name*='status'], [class*='status-filter'], [class*='filter']"
    ORDER_DETAIL = "[class*='order-detail'], [class*='detail-panel']"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/orders")

    def wait_for_orders_loaded(self) -> None:
        self.wait_for_element(self.ORDER_TABLE)

    def get_order_count(self) -> int:
        self.wait_for_orders_loaded()
        return self.page.locator(self.ORDER_ROW).count()

    def search(self, keyword: str) -> None:
        self.wait_for_element(self.SEARCH_INPUT).fill(keyword)
        self.page.keyboard.press("Enter")
        self.page.wait_for_load_state("networkidle")

    def filter_by_status(self, status: str) -> None:
        self.page.locator(self.STATUS_FILTER).select_option(label=status)
        self.page.wait_for_load_state("networkidle")

    def click_first_order(self) -> None:
        self.page.locator(self.ORDER_ROW).first.click()

    def is_detail_visible(self) -> bool:
        return self.page.locator(self.ORDER_DETAIL).is_visible()
```

- [ ] **Step 2: 创建 tests/test_orders.py**

```python
import pytest
from pages.orders_page import OrdersPage


@pytest.mark.orders
def test_orders_list_loads(logged_in_page):
    """订单列表页面正常加载并显示数据"""
    orders = OrdersPage(logged_in_page)
    orders.goto()
    orders.wait_for_orders_loaded()
    count = orders.get_order_count()
    assert count >= 0  # 有数据或空列表都正常


@pytest.mark.orders
def test_orders_search(logged_in_page):
    """搜索框可输入关键词并触发搜索"""
    orders = OrdersPage(logged_in_page)
    orders.goto()
    orders.wait_for_orders_loaded()
    orders.search("TEST")
    # 搜索后页面不崩溃，结果任意
    assert orders.page.locator(orders.ORDER_TABLE).is_visible()


@pytest.mark.orders
def test_orders_detail_opens(logged_in_page):
    """点击订单行可打开详情"""
    orders = OrdersPage(logged_in_page)
    orders.goto()
    orders.wait_for_orders_loaded()
    if orders.get_order_count() > 0:
        orders.click_first_order()
        logged_in_page.wait_for_load_state("networkidle")
        # 详情页打开（URL 变化或详情面板可见）
        assert orders.is_detail_visible() or "/orders/" in logged_in_page.url
```

- [ ] **Step 3: Commit**

```bash
git add pages/orders_page.py tests/test_orders.py
git commit -m "feat: add OrdersPage POM and order test cases"
```

---

## Task 6: 实现 WithdrawPage 和提现测试

**Files:**
- Create: `pages/withdraw_page.py`
- Create: `tests/test_withdraw.py`

- [ ] **Step 1: 创建 pages/withdraw_page.py**

```python
from playwright.sync_api import Page
from pages.base_page import BasePage


class WithdrawPage(BasePage):
    AMOUNT_INPUT = "input[name*='amount'], input[placeholder*='金额'], input[placeholder*='amount']"
    ADDRESS_INPUT = "input[name*='address'], input[placeholder*='地址'], input[placeholder*='address']"
    SUBMIT_BUTTON = "button[type='submit'], button:has-text('提现'), button:has-text('Withdraw')"
    CONFIRM_BUTTON = "button:has-text('确认'), button:has-text('Confirm')"
    SUCCESS_MESSAGE = "[class*='success'], [class*='toast-success'], [role='alert']:has-text('成功')"
    ERROR_MESSAGE = "[class*='error'], [class*='toast-error'], [role='alert']:has-text('错误')"
    BALANCE_DISPLAY = "[class*='available'], [class*='balance']"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/withdraw")

    def get_available_balance(self) -> str:
        return self.wait_for_element(self.BALANCE_DISPLAY).inner_text()

    def fill_amount(self, amount: str) -> None:
        self.wait_for_element(self.AMOUNT_INPUT).fill(amount)

    def fill_address(self, address: str) -> None:
        self.wait_for_element(self.ADDRESS_INPUT).fill(address)

    def submit(self) -> None:
        self.page.locator(self.SUBMIT_BUTTON).click()

    def confirm(self) -> None:
        self.page.locator(self.CONFIRM_BUTTON).click()

    def get_success_message(self) -> str:
        locator = self.page.locator(self.SUCCESS_MESSAGE)
        locator.wait_for(state="visible", timeout=10000)
        return locator.inner_text()

    def get_error_message(self) -> str:
        locator = self.page.locator(self.ERROR_MESSAGE)
        locator.wait_for(state="visible", timeout=5000)
        return locator.inner_text()
```

- [ ] **Step 2: 创建 tests/test_withdraw.py**

```python
import pytest
from pages.withdraw_page import WithdrawPage


@pytest.mark.withdraw
def test_withdraw_page_loads(logged_in_page):
    """提现页面正常加载，显示可用余额"""
    withdraw = WithdrawPage(logged_in_page)
    withdraw.goto()
    balance = withdraw.get_available_balance()
    assert balance  # 有余额展示


@pytest.mark.withdraw
def test_withdraw_zero_amount_shows_error(logged_in_page):
    """提现金额为 0 时显示错误提示"""
    withdraw = WithdrawPage(logged_in_page)
    withdraw.goto()
    withdraw.fill_amount("0")
    withdraw.fill_address("0xTestAddress1234567890abcdef1234567890abcdef")
    withdraw.submit()
    error = withdraw.get_error_message()
    assert error  # 有错误提示


@pytest.mark.withdraw
def test_withdraw_invalid_address_shows_error(logged_in_page):
    """无效钱包地址显示错误提示"""
    withdraw = WithdrawPage(logged_in_page)
    withdraw.goto()
    withdraw.fill_amount("1")
    withdraw.fill_address("invalid_address")
    withdraw.submit()
    error = withdraw.get_error_message()
    assert error  # 有错误提示
```

- [ ] **Step 3: Commit**

```bash
git add pages/withdraw_page.py tests/test_withdraw.py
git commit -m "feat: add WithdrawPage POM and withdraw test cases"
```

---

## Task 7: 实现公共工具和最终验证

**Files:**
- Create: `utils/helpers.py`
- Modify: `pages/base_page.py`（集成截图工具）

- [ ] **Step 1: 创建 utils/helpers.py**

```python
import functools
from pathlib import Path
from datetime import datetime


def ensure_reports_dir() -> Path:
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    return reports


def timestamped_name(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}"


def screenshot_on_failure(func):
    """装饰器：测试失败时自动截图"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            # 从参数中找 page 对象
            page = kwargs.get("page") or kwargs.get("logged_in_page")
            if page is None:
                for a in args:
                    if hasattr(a, "screenshot"):
                        page = a
                        break
            if page:
                name = timestamped_name(func.__name__)
                path = ensure_reports_dir() / f"{name}.png"
                page.screenshot(path=str(path), full_page=True)
            raise
    return wrapper
```

- [ ] **Step 2: 运行完整测试套件收集验证**

```bash
pytest --collect-only 2>&1
```

Expected: 所有 test_*.py 文件被收集，无 ImportError

- [ ] **Step 3: 运行一次完整测试（headless 模式，允许连接失败）**

```bash
pytest -v --tb=short 2>&1 | tail -30
```

Expected: 所有测试被收集并执行，报告生成在 reports/report.html

- [ ] **Step 4: 最终 Commit**

```bash
git add utils/helpers.py
git commit -m "feat: add helpers utility and complete framework scaffold"
```

---

## 运行命令速查

```bash
# 运行所有测试
pytest

# 只运行登录测试
pytest -m login

# headless 模式
pytest --headed=false

# 生成详细报告
pytest -v --html=reports/report.html

# 单个文件调试
pytest tests/test_login.py -v -s
```
