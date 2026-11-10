# 商户端业务场景覆盖 — 总体规划 + 子项目 A（测试基础设施）设计

- 日期：2026-11-10
- 状态：已实现（子项目 A）
- 范围：第 1 部分是 Leptage 商户端业务场景覆盖的总体规划（拆分子项目）；第 2 部分是子项目 A 的详细设计
- 前置文档：`2026-11-09-test-platform-design.md`（Web3Rec 平台第 1 期）

---

## 第 1 部分：总体规划

### 1.1 目标

按以下优先级表，把 **Leptage 商户端（`www1.sit.planckage.cc`）上存在的功能**全部纳入 UI 自动化覆盖：

| 优先级 | 场景 | 原因 |
|---|---|---|
| P0 | 登录、权限、菜单可访问 | 打不开就全部受影响 |
| P0 | 付款/转账/提现下单 → 审批 → 状态流转 | 直接涉及资金 |
| P0 | 金额、币种、汇率、手续费的页面展示和计算 | 展示错误会导致客诉，甚至资损 |
| P1 | 费率、限额、风控规则配置 | 配错影响面大 |
| P1 | 商户入驻、KYC 资料提交和审核 | 业务入口 |
| P1 | 交易查询、对账单、报表导出 | 客户高频使用 |
| P2 | 一般信息维护类页面 | 风险低 |

### 1.2 现状盘点（2026-11-09 SIT 实测）

**商户端菜单与功能：**

| 菜单 | 功能点 |
|---|---|
| 登录 | 密码登录、合规声明弹窗 |
| Wallet | Available / Total / Treasury Balance、Last-Day Earnings、各币种余额（USDC/USDT/USD/EUR/GBP）、快捷入口 |
| Deposit | Crypto（币种、网络、充值地址）、Fiat（USD） |
| Withdraw | Fiat / Crypto；金额、Max、套餐（Flexi，免费额度）、汇率 + 10s 刷新、Beneficiary 选择与管理、Total Fee、Recipient Gets、Payment Note、Withdraw Authentication（2FA）、Auto Withdrawal 策略 |
| Convert | Sell / Buy、Max、报价 + 3s 刷新、Submit |
| Treasury | 推荐产品、Subscribe、My Positions |
| Transaction | 按 Currency / Type / Status / Transaction ID / 时间筛选、Export、详情弹窗、分页 |
| Setting | 修改密码、2FA、提现白名单 + 地址管理 |

商户端是单一用户角色，没有成员管理和 Maker/Checker 审批；KYC 只出现在新商户的注册流程中。

**运营后台 proto（`proto1.sit.planckage.cc`）：** 走 SSO（`sso1.dev.photontech.cc`），用专用 QA 账号的账号密码登录，没有二次验证，token 有效期 18 小时。与本规划相关的菜单：

- 审批：Risk Management → Crypto / Fiat / Beneficiary Review / Address Review；Finance Review → Payout Order Review
- KYC：Risk Management → KYC Cases
- 配置：FeeEngine → Fee Config；FX Manager
- 邮件验证码：Event Center → History Event，Topic = `chnl_email`。Payload 中 `dataModel.to` 是收件邮箱，`dataModel.code` 是验证码，`exp` 是有效期（分钟），模板为 `verify.code.sp2.v1`
  - 接口：`POST /proto/ec/queryHistory`，列表参数 `{pageNum, limit, topic, startTime, endTime, ...}`，详情参数 `{eventId}`

### 1.3 已确定的决策

| 项 | 决定 |
|---|---|
| 覆盖范围 | 商户端上存在的功能全部覆盖；proto 只作为辅助（取码、审批放行、核对），不作为被测对象 |
| 接入方式 | **商户端走 Playwright UI；proto 走 HTTP API**（httpx + SSO token） |
| 资金类用例 | **混合模式**：日常回归只做到提交前；真实下单用例打 `fund` 标记，默认不执行，手动或定时触发 |
| 2FA | TOTP 密钥 + `pyotp` 生成验证码 |
| 邮箱验证码 | 通过 proto 事件中心的 `chnl_email` 事件获取 |
| KYC | 完整流程：新邮箱注册 → 取码 → 填 KYC → 提交 |

### 1.4 子项目拆分

每个子项目单独走 spec → plan → 实现。

| 子项目 | 内容 | 依赖 |
|---|---|---|
| **A. 基础设施**（本文第 2 部分） | 标记体系、资金保护闸、ProtoClient、TOTP、金额工具、测试数据工具、平台小改 | — |
| B. P0 登录/权限/安全 | 登录异常分支、未登录访问拦截、会话失效、菜单可访问、2FA 开启时提现要求验证、白名单拦截 | A |
| C. P0 金额/汇率/手续费 | Withdraw：Max、超余额校验、Total Fee 和 Recipient Gets 计算、汇率刷新、套餐免费额度；Convert：报价计算与刷新；Wallet：余额汇总一致性 | A |
| D. P0 资金下单 E2E（`fund`） | 小额 Convert；Withdraw（Crypto/Fiat）→ proto 审批通过/拒绝 → Transaction 状态流转；Treasury 申购 | A、C |
| E. P1 交易查询/导出 | Transaction 各筛选条件、分页、详情字段、Export 文件内容与列表一致 | A |
| F. P1 注册 + KYC | 注册 → proto 取码 → KYC 填写与上传 → 提交 → proto KYC Cases 可查 | A |
| G. P1 配置生效验证 | 在商户端核对 proto 中费率、限额、白名单配置的效果（只读，不改 proto 配置） | A、C |
| P2 | 保留现有 Setting 冒烟用例 | — |

推进顺序：A → B → C → D → E → F → G。

**遗留事项：**
- 子项目 D 开始前，确认 proto QA 账号是否有 Payout Order Review / Risk 审核权限。
- 商户账号的 TOTP 密钥需要由账号持有人重新绑定 2FA 后写入 `config.local.yaml`，由人工完成。

---

## 第 2 部分：子项目 A — 测试基础设施

### 2.1 标记体系

| 维度 | marker | 含义 |
|---|---|---|
| 优先级 | `p0` / `p1` / `p2` | 每条用例必须有且只有一个 |
| 风险 | `fund` | 真实资金操作（Convert、Withdraw、Treasury 申购） |
| 风险 | `e2e` | 跨系统，依赖 proto |
| 风险 | `creates_data` | 会在 SIT 留下数据（注册新商户、提交 KYC） |
| 模块 | `login` `dashboard` `deposit` `withdraw` `convert` `treasury` `transaction` `setting` `orders` `smoke` | 保持不变 |

所有 marker 都在 `pytest.ini` 中注册。

**优先级检查：** 在 `pytest_collection_modifyitems` 中，对没有优先级 marker 或有多个优先级 marker 的用例发出 `PytestWarning`（**不报错**）。警告信息包含 nodeid。

**现有用例补标：** `test_00_login` ~ `test_06_transaction`、`test_08_orders` 标 `p0`（登录与菜单可访问）；`test_07_setting` 标 `p2`。

### 2.2 资金保护闸

- 在 `pytest_collection_modifyitems` 中，`MS_ALLOW_FUND` 不为真时，给所有 `fund` 用例加上 `skip(reason="资金类用例未开启：设置 MS_ALLOW_FUND=1")`。
- 不使用 `-m "not fund"`，否则平台显式勾选的 nodeid 也会被过滤掉，用户看不到被跳过的原因。
- `fund_guard` fixture：`fund` 用例**显式依赖**（如果依赖它的用例没有 `fund` 标记，直接报错，防止漏标），提供 `check_amount(amount: Decimal, currency: str)`。金额大于 `settings.fund_max_amount` 时抛出 `ValueError`，这个检查发生在任何页面提交动作之前。
- `fund_max_amount` 是一个不区分币种的面值上限，默认 `1`。

### 2.3 配置扩展

`config/config.yaml` 新增（只放非机密的默认值）：

```yaml
credentials:
  totp_secret: ""
proto:
  base_url: "https://proto1.sit.planckage.cc"
  sso_url: "https://sso1.dev.photontech.cc"
  username: ""
  password: ""
fund:
  max_amount: "1"
test_data:
  email_domain: "test.com"
  email_prefix: "autotest"
```

机密只放在 `config.local.yaml`（已在 gitignore 中）或环境变量里：

| 字段 | 环境变量 |
|---|---|
| `credentials.totp_secret` | `MS_TOTP_SECRET` |
| `proto.username` | `MS_PROTO_USERNAME` |
| `proto.password` | `MS_PROTO_PASSWORD` |
| — | `MS_ALLOW_FUND`（只用环境变量，不进配置文件） |

`Settings` 新增：`totp_secret`、`proto_base_url`、`proto_sso_url`、`proto_username`、`proto_password`、`fund_max_amount: Decimal`、`email_domain`、`email_prefix`（`MS_ALLOW_FUND` 由插件在运行时直接读取环境变量，不放进 Settings，避免出现两个来源），以及：

- `require_totp()`：未配置时抛出 `RuntimeError`，提示配置方法
- `require_proto()`：同上

这两个检查只在对应 fixture 首次使用时调用。`pytest_sessionstart` 中只保留原有的 `require_credentials()`，不配置 proto / TOTP 也能跑冒烟用例。

`config.local.yaml.example` 同步补充这些字段的示例（值留空）。

### 2.4 新增模块

#### `clients/proto_client.py` — `ProtoClient`

基于 `httpx.Client`。构造参数为 `base_url, sso_url, username, password`，并可注入 `transport`，便于单元测试。

| 方法 | 行为 |
|---|---|
| `login()` | 走 OAuth2 授权码流程（见下方"实现时验证结果"），拿到 cookie `proto-token` 和当前用户 `userId`；任意一步失败都抛出 `ProtoAuthError`（信息里不含密码） |
| `_call(method, path, json)` | 尚未登录时先登录；HTTP 401 时**重新登录一次**并重试，仍失败则抛错；业务码不是 `0000` 时抛出 `ProtoError`。proto-token 的有效期未知，所以不按过期时间主动刷新，只在 401 时重登 |
| `query_events(topic, start_ms, end_ms, page=1, limit=50) -> list[dict]` | `POST /proto/ec/queryHistory` |
| `wait_for_email_code(to, since_ms, timeout=120, interval=3) -> str` | 轮询 `chnl_email` 事件，时间窗口为 `[since_ms - 5s, now]`；按 `dataModel.to == to`（忽略大小写）匹配，取最新一条的 `dataModel.code`；超时抛出 `TimeoutError`，信息中包含邮箱和已等待的时长 |

**实现时验证结果（2026-11-10）：** 纯 httpx 即可完成登录，不需要浏览器。
1. `GET {proto}/redirect/proto/oauth2/authorization/sso?redirectUrl=…` 返回 302 到 SSO，location 里带 `state`
2. `POST {sso}/api/user/login {username, password, type: "account"}` 返回 `access_token`
3. `GET {sso}/api/oauth/authorize?<第 1 步 location 的 query>`，带 `Authorization: Bearer <access_token>`，返回 `data.redirect_uri`
4. `GET data.redirect_uri`，proto 写入 cookie `proto-token`

proto 业务接口必须带 header `x-pd-uri: api`（否则 nginx 返回 405），并且要带 `x-lp-user-id`（取自 `GET /proto/ops/user`），否则查询结果为空。成功响应的格式是 `{code: "0000", data}`。列表接口的 `records[].detail.payload.dataModel` 里直接就有 `to` / `code`，不需要再调详情接口。**事件中心只保留最近约 1 小时的事件。** QA 账号的角色包括 Compliance、CSOps、marketing、Finance、Finance Leader、Risk。

#### `utils/otp.py`

- `current_code(secret: str, min_remaining: int = 5) -> str`：当前周期剩余时间少于 `min_remaining` 秒时，等到下一周期再生成。可注入时钟，便于测试。

#### `utils/money.py`

- `parse_amount(text: str) -> tuple[Decimal, str | None]`：支持千分位、正负号（`+ 0.030000 USDT`、`- 2.000000 USDT`）、可选的币种后缀；无法解析时抛出 `ValueError`。
- `assert_amount(actual: Decimal, expected: Decimal, places: int)`：按 `places` 位小数量化后比较，失败信息里同时给出两个值和它们的差值。
- 所有金额计算统一使用 `Decimal`，不使用 float。

#### `utils/data_factory.py`

- `unique_email(prefix=None, domain=None) -> str`：返回 `{prefix}{yyyyMMddHHmmssSSS}@{domain}`，默认值取自配置。

### 2.5 Fixtures（`tests/conftest.py`）

| fixture | 作用域 | 说明 |
|---|---|---|
| `proto` | session | 调用 `settings.require_proto()` 后返回 `ProtoClient`，首次请求时登录 |

上述钩子和 fixture 实现在插件 `utils/pytest_guards.py` 中，由 `tests/conftest.py` 通过 `pytest_plugins` 加载，便于用 pytester 单独测试。
| `totp` | session | 调用 `settings.require_totp()` 后返回 `lambda: current_code(settings.totp_secret)` |
| `fund_guard` | function | 见 2.2 |

### 2.6 平台改动（sentinel）

| 位置 | 改动 |
|---|---|
| `Environment` 模型 | 新增 `allow_fund: bool = False`。由于没有迁移工具，启动时检查该列，不存在就执行 `ALTER TABLE ADD COLUMN` |
| 执行器 | 环境 `allow_fund` 为真时注入 `MS_ALLOW_FUND=1`，否则显式设为 `0`，不继承后端进程的环境变量 |
| schemas / API | Environment 的读写接口包含 `allow_fund` |
| 前端：环境编辑 | 新增"允许资金类用例"开关，打开时弹出二次确认；环境列表中开启的环境显示红色标签 |
| 前端：用例管理 | 新增"优先级"列（从 markers 中取 `p0/p1/p2`）和优先级筛选；`fund` 显示为红色标签，`e2e` / `creates_data` 显示为橙色标签；缺少优先级的用例显示黄色"未分级" |

用例的数据库结构不变，优先级在前端从 `markers` 计算。

### 2.7 测试

- **新目录 `unit_tests/`**（不放进 `tests/`，因为 `tests/conftest.py` 的 sessionstart 会检查商户凭据）。新增 `make test-unit`：`$(PY) -m pytest unit_tests -p no:cacheprovider -q -o addopts=""`。
  - `money`：千分位、正负号、币种后缀、非法输入、量化比较
  - `otp`：注入时钟，覆盖剩余时间不足时的等待逻辑；用 RFC 6238 的测试向量校验生成结果
  - `data_factory`：格式正确，连续调用不重复
  - `ProtoClient`（`httpx.MockTransport`）：登录失败、token 过期后自动重新登录、401 重试一次、按收件人匹配、忽略 `since` 之前的旧验证码、超时
  - 收集钩子：用 `pytester` 验证 `fund` 默认被 skip、`MS_ALLOW_FUND=1` 时执行、缺少优先级时出现 warning、金额超限时报错
- **平台**：`sentinel/tests` 补充 `allow_fund` 的增删改，以及执行时注入 `MS_ALLOW_FUND` 的测试（使用 sample_project）。
- **全部单元测试不连 SIT。**
- **验收（人工 + SIT）：**
  1. `make test-unit`、`make test-platform` 全部通过
  2. 命令行跑现有 12 条用例，全部通过，并且没有"未分级"警告
  3. 在 SIT 上触发一次注册验证码，`wait_for_email_code` 能取到正确的 code
  4. 平台用例管理页能按优先级筛选；对未开启 `allow_fund` 的环境，`fund` 示例用例显示为 skipped，并带有原因

### 2.8 新增依赖

- `pyotp`（版本在实现时固定）

### 2.9 非目标（本子项目不做）

- proto 审批接口（放到子项目 D）
- 任何业务场景用例（B–G）
- 按优先级统计覆盖率的看板（放到平台第 4 期的数据看板）
