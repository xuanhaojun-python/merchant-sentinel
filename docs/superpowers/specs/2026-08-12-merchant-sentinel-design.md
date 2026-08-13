# Merchant Sentinel — Web3 商户端 UI 自动化框架设计

**日期：** 2026-08-12
**项目：** merchant-sentinel
**技术栈：** Playwright (Python) + pytest + Page Object Model

---

## 概述

面向 Web3 支付收款类 toB 商户后台的 UI 自动化测试框架。覆盖登录、Dashboard、订单、提现四大核心模块，采用标准 POM 分层架构。

---

## 架构

### 目录结构

```
merchant-sentinel/
├── pages/
│   ├── base_page.py        # BasePage 基类（wait / screenshot / goto）
│   ├── login_page.py       # 登录页（账号密码 + 2FA）
│   ├── dashboard_page.py   # Dashboard 总览（余额、统计）
│   ├── orders_page.py      # 收款订单列表 & 详情
│   └── withdraw_page.py    # 提现 / 转账流程
│
├── tests/
│   ├── conftest.py         # browser / page / logged_in_page fixtures
│   ├── test_login.py
│   ├── test_dashboard.py
│   ├── test_orders.py
│   └── test_withdraw.py
│
├── config/
│   ├── config.yaml         # base_url、账号、超时
│   └── settings.py         # 读取 config.yaml，全局单例
│
├── utils/
│   └── helpers.py          # 截图、日志等公共工具
│
├── reports/                # pytest-html 报告输出
├── pytest.ini
└── requirements.txt
```

### 分层关系

```
tests/ → pages/ → Playwright (Chromium)
   ↑
conftest.py (fixtures)
   ↑
config/settings.py
```

---

## 组件设计

### BasePage
- `__init__(page)` — 接收 Playwright page 对象
- `goto(path)` — 拼接 base_url 导航
- `wait_for_element(selector, timeout)` — 统一等待策略
- `screenshot(name)` — 失败时截图

### Page Objects
每个页面继承 BasePage，封装该页面的定位器和操作方法，不暴露原始 selector 给测试层。

### conftest.py Fixtures
- `browser` (session scope) — 启动一次浏览器
- `page` (function scope) — 每个测试新 page
- `logged_in_page` (function scope) — 自动完成登录，返回已认证 page

### config.yaml
```yaml
base_url: https://merchant-staging.example.com
credentials:
  email: test@merchant.com
  password: TestPass123
timeouts:
  default: 30000
  navigation: 60000
```

---

## 测试覆盖范围

| 模块 | 用例类型 |
|------|---------|
| 登录 | 正常登录、错误密码、2FA 流程 |
| Dashboard | 余额展示、统计数据加载 |
| 订单 | 列表加载、搜索/筛选、详情查看 |
| 提现 | 发起提现、金额校验、状态确认 |

---

## 报告
- 默认：pytest-html（`reports/report.html`）
- 可选：Allure（后期接入）

---

## 依赖
```
playwright
pytest
pytest-playwright
pytest-html
pyyaml
```
