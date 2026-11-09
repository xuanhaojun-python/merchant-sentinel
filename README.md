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
│   ├── test_00_login.py
│   ├── test_01_dashboard.py
│   ├── test_02_deposit.py
│   ├── test_03_treasury.py
│   ├── test_04_withdraw.py
│   ├── test_05_convert.py
│   ├── test_06_transaction.py
│   ├── test_07_setting.py
│   └── test_08_orders.py
│
├── reports/                 # 报告输出（运行后自动生成）
├── pytest.ini
└── requirements.txt
```

---

## 🖥️ Web3Rec 可视化测试平台（sentinel/）

本机使用的 Web 平台：项目管理 → 同步用例 → 勾选执行 → 实时日志 → 查看报告（含失败截图）。
平台只负责调度 pytest，`tests/` `pages/` 仍可脱离平台在命令行运行。设计文档：`docs/superpowers/specs/2026-11-09-test-platform-design.md`

```bash
pip install -r requirements.txt
make install-frontend      # 首次：安装前端依赖（需 Node.js 18+）

make run                   # 构建前端并启动 → http://localhost:8082
make dev                   # 开发模式：后端 :8082 热重载 + 前端 :5173
make test-platform         # 平台自身的后端测试（不连 SIT）
```

**首次使用**：项目管理 → 新建项目（工程目录填本仓库绝对路径）→ 环境配置新建 SIT（账号密码可留空，沿用 `config.local.yaml`）→ 用例管理 → 同步用例 → 勾选执行。

| 菜单 | 状态 |
|---|---|
| 项目管理 / 用例管理 / 执行记录 / 报告管理 | ✅ 第 1 期 |
| 套件管理 / 定时任务 / 通知列表 | 第 2 期 |
| 元素管理 / 脚本录制 / 脚本列表 | 第 3 期 |
| 数据看板 | 第 4 期 |

运行数据（SQLite、日志、截图）保存在 `sentinel/data/`，不入库。

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

配置优先级：**环境变量 > `config/config.local.yaml`（不入库）> `config/config.yaml`**

账号密码**不要**写进 `config.yaml`，二选一：

```bash
# 方式一：本地私有配置文件（已在 .gitignore 中忽略）
cp config/config.local.yaml.example config/config.local.yaml   # 然后填写密码

# 方式二：环境变量（适合 CI）
export MS_EMAIL="jimmy.xuan@leptage.com"
export MS_PASSWORD="..."
export MS_HEADLESS=true   # 可选，无头模式
```

`config/config.yaml` 其余配置：

```yaml
base_url: "https://..."
credentials:
  email: "jimmy.xuan@leptage.com"
  password: ""         # 留空，见上文
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

## ✅ 测试用例（12 条）

页面访问顺序固定为：
**Login → Dashboard → Deposit → Treasury → Withdraw → Convert → Transaction → Setting → Orders**

| # | 页面 | 标记 | 检查项 |
|---|---|---|---|
| 00 | Login × 4 | `login` | 登录成功（`smoke`）/ 空表单校验 / 邮箱格式校验 / 错误密码提示 |
| 01 | Wallet 首页 | `dashboard` | 欢迎标题 / 余额卡片 / Deposit 按钮 / All Currencies 区块 |
| 02 | Deposit | `deposit` | 页面核心元素 × 4 |
| 03 | Treasury | `treasury` | 页面核心元素 × 5 |
| 04 | Withdraw | `withdraw` | Fiat & Crypto tab 可见 / 默认 Fiat 高亮 / tab 切换高亮 |
| 05 | Convert | `convert` | 页面核心元素 × 5 |
| 06 | Transaction | `transaction` | 页面核心元素 × 4 |
| 07 | Setting | `setting` | 页面核心元素 × 4 |
| 08 | Orders | `orders` | 列表加载 / Search / 打开订单详情并校验字段 / 关闭详情 |

除登录异常用例外，其余用例均标记 `@pytest.mark.smoke`，可通过 `pytest -m smoke` 一键执行。

> 错误密码用例每次运行只尝试 1 次，避免触发账号锁定。

**断言规范**：统一使用 Playwright `expect(locator).to_be_visible()`（自动重试，超时取 `timeouts.default`），
不要使用 `locator.is_visible()` 做断言（它只检查调用瞬间的状态，容易误报）。

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
- 进入 Withdraw 页面时可能出现弹框，检测到后发送 `Escape` 键关闭，并等待弹框隐藏。
- 进入 Wallet 首页时可能出现 Compliance Declaration 弹窗，按 `aria-label` 精确定位后勾选并确认（页面上同时存在多个 `role=dialog`，不能用通用选择器）。
