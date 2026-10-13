# 🧪 Merchant Sentinel — UI 自动化测试

> Leptage 商户后台自动化测试框架 · Python + Playwright + pytest

---

## 📌 项目简介

对 Leptage 商户后台核心页面进行 UI 自动化回归测试。

- 单次运行只启动一次浏览器、只登录一次
- 所有用例顺序共享同一个 page 实例
- 测试结束自动生成 HTML 可视化报告

---

## 🗂️ 目录结构

```
merchant-sentinel/
├── config/
│   ├── config.yaml          # 环境配置（URL、账号、超时、浏览器参数）
│   └── settings.py          # 配置加载，暴露 settings 单例
│
├── pages/                   # Page Object Model 层
│   ├── base_page.py         # 基类：goto / wait_for_element / screenshot
│   ├── login_page.py
│   ├── dashboard_page.py
│   ├── deposit_page.py
│   ├── treasury_page.py
│   ├── withdraw_page.py     # 含 Fiat / Crypto tab 切换逻辑
│   ├── convert_page.py
│   ├── transaction_page.py
│   ├── orders_page.py
│   └── setting_page.py
│
├── tests/
│   ├── conftest.py          # Fixture 定义 + 自定义报告钩子
│   ├── test_01_dashboard.py
│   ├── test_02_deposit.py
│   ├── test_03_treasury.py
│   ├── test_04_withdraw.py
│   ├── test_05_convert.py
│   ├── test_06_transaction.py
│   ├── test_07_orders.py
│   └── test_08_setting.py
│
├── reports/                 # 报告输出（运行后自动生成）
├── pytest.ini
└── requirements.txt
```

---

## ⚙️ 技术栈

| 组件 | 版本 |
|---|---|
| Python | 3.11 |
| Playwright | 1.44.0 |
| pytest | 8.2.2 |
| pytest-playwright | 0.5.0 |
| pytest-html | 4.1.1 |
| pyyaml | 6.0.1 |

---

## 🔧 环境配置

配置文件：`config/config.yaml`

```yaml
base_url: "https://..."
credentials:
  email: "jimmy.xuan@leptage.com"
  password: "..."
timeouts:
  default: 10000       # ms，元素等待超时
  navigation: 30000    # ms，页面导航超时
browser:
  headless: false      # true = 无头模式
  slow_mo: 0           # ms，操作间隔，调试时可设 500
```

> ⚠️ **账号说明**：只允许使用 `jimmy.xuan@leptage.com`，禁止使用其他账号登录。

---

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 安装 Playwright 浏览器
playwright install chromium

# 3. 运行全部冒烟用例
pytest -m smoke

# 4. 运行全部用例（按文件名顺序）
pytest

# 5. 运行单个模块
pytest tests/test_04_withdraw.py -v
```

---

## ✅ 测试用例（8 条冒烟用例）

页面访问顺序固定为：
**Dashboard → Deposit → Treasury → Withdraw → Convert → Transaction → Orders → Setting**

| # | 页面 | 标记 | 检查项 |
|---|---|---|---|
| 01 | Wallet 首页 | `dashboard` | 欢迎标题 / 余额卡片 / Deposit 按钮 / All Currencies 区块 |
| 02 | Deposit | `deposit` | 页面核心元素 × 4 |
| 03 | Treasury | `treasury` | 页面核心元素 × 5 |
| 04 | Withdraw | `withdraw` | Fiat & Crypto tab 可见 / 默认 Fiat 高亮 / tab 切换高亮 |
| 05 | Convert | `convert` | 页面核心元素 × 5 |
| 06 | Transaction | `transaction` | 页面核心元素 × 4 |
| 07 | Orders | `orders` | 页面核心元素 × 3 |
| 08 | Setting | `setting` | 页面核心元素 × 4 |

所有用例同时标记 `@pytest.mark.smoke`，可通过 `pytest -m smoke` 一键执行。

---

## 🏗️ Fixture 架构

```
_browser  (scope=session)
│   整个 session 只启动一次 Chromium
│
├── page  (scope=session)
│       登录一次，所有用例共享同一 page 实例
│       └── logged_in_page  (scope=session)
│               透传 page，语义更清晰，供各测试用例注入
│
└── fresh_page  (scope=function)
        无登录态，每个用例独立 context
        预留给登录流程测试使用
```

---

## 📊 测试报告

运行结束后在 `reports/` 目录生成两份报告：

| 文件 | 说明 |
|---|---|
| `report.html` | pytest-html 标准报告，需点击展开才能看到步骤 |
| `custom_report.html` | **推荐** · 自定义报告，检查步骤直接可见，PASSED / FAILED 色块醒目 |

---

## 💡 关键设计说明

**单浏览器单页面复用**
`page` fixture 为 session 级，整个测试套件只启动一次浏览器、只登录一次，各用例复用同一 page，大幅缩短执行时间。

**用例执行顺序**
测试文件以 `test_01_` ~ `test_08_` 前缀命名，pytest 按字母顺序收集，确保页面访问顺序固定。

**Withdraw Tab 高亮**
Fiat / Crypto 切换本质是 Vue Router 路由跳转（`<a href="/withdraw/fiat">`），并非普通 tab 组件。使用 `page.url` 是否包含对应路径判断激活状态，点击后等待 URL 变化而非等待 class 变化。

**Dialog 处理**
进入 Withdraw 页面时可能出现弹框，检测到后发送 `Escape` 键关闭，等待 500ms 让动画完成。
