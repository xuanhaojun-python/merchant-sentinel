# 子项目 B — P0 登录 / 权限 / 菜单可访问 / 安全控制

- 日期：2026-11-10
- 状态：已实现
- 上级规划：`2026-11-10-test-infra-design.md` 第 1 部分（子项目 B）

## 1. 范围

商户端是单一用户角色，没有菜单级或按钮级的权限差异。因此"权限"在商户端落实为**会话与安全控制**：

| 场景 | 用例 | 会话 |
|---|---|---|
| 未登录访问 9 个受保护路由，均被拦截到 `/login` | `test_09_session.py::test_protected_route_redirects_to_login[*]` | 无登录态 |
| 左侧 7 个菜单逐一点击：URL 正确、未被踢回登录页、菜单项高亮 | `test_sidebar_menu_accessible[*]` | 共享 |
| 退出登录：回到 `/login`、`lepton-token` 被清除、再访问被拦截、浏览器后退无效 | `test_logout_invalidates_session` | 独立 |
| 清除 token 后访问被拦截 | `test_cleared_token_redirects_to_login` | 独立 |
| 篡改 token 后访问被拦截 | `test_tampered_token_redirects_to_login` | 独立 |
| 未注册邮箱登录：提示账号或密码错误 | `test_login_unregistered_email` | 无登录态 |
| 账号开启 2FA 时，提现必须输入 2FA：确认弹窗含 6 位验证码输入框，空码 Confirm 提示必填，Cancel 可关闭 | `test_10_withdraw_2fa.py::test_withdraw_requires_2fa` | 共享 |

已有的 `test_00_login.py`（成功登录、空字段、邮箱格式错误、密码错误）继续保留。

**不做：**
- 连续输错密码导致锁定：会锁住共享账号，影响所有用例。
- 白名单拦截：开关白名单需要 2FA 验证码，等 TOTP 密钥配置后再补（放进子项目 D 或单独补充）。

## 2. SIT 实测事实（2026-11-10）

- 登录态保存在 cookie `lepton-token` 中。
- **Logout 会作废该账号的所有会话**：同一账号在其他浏览器、共享 page 或人工登录的会话都会失效。而重复登录不会挤掉旧会话。
- localStorage 的 `LOGIN_METHOD` 会记住上次的登录方式，登录页可能直接进入密码模式。
- Withdraw 页的提交按钮是"Withdraw Authentication"：表单完整前为禁用状态；点击后弹出 **Withdrawal Confirmation**，内含 2FA 输入框（placeholder `Enter the 6-digit code from Google Authenticator`，maxlength 6）和 Confirm / Cancel。点击按钮本身不会下单。
- 账户菜单：右上角 `.account-wrap`，悬停后弹出 Account / Logout。页面上有两个 `.account-wrap`，需要通过菜单的 `aria-labelledby` 反查对应的触发元素。

## 3. 实现

| 位置 | 内容 |
|---|---|
| `pages/layout.py` | `AppLayout`（左侧菜单点击、退出登录、token 检查）、`SIDEBAR_MENUS`、`PROTECTED_ROUTES`、`TOKEN_COOKIE` |
| `pages/withdraw_page.py` | 金额输入、提交按钮、选择首个收款账户、确认弹窗 / 2FA 输入框 / Confirm / Cancel |
| `pages/setting_page.py` | `disable_2fa_entry` |
| `pages/login_page.py` | `goto()` 兼容已记住的密码模式 |
| `tests/conftest.py` | `own_session_page`：独立登录的 context，结束后把共享会话标记为 stale；`logged_in_page` 改为 function 级，发现 stale 时清 cookie 并重新登录 |
| `pytest.ini` | 新增 marker `security` |

**2FA 用例的安全闸：** 绝不输入验证码；点击 Confirm 前先断言 2FA 输入框可见且为空。如果账号的 2FA 被关闭（输入框不存在），用例在断言处失败，不会点击 Confirm，从而避免真实下单。用例开头还会断言 Setting 页显示"Disable 2FA"，即 2FA 处于开启状态。

## 4. 注意事项

- 跑 `security` 用例（包含退出登录）时，**同一账号上的人工 SIT 会话会被踢下线**。需要避免时，可用 `-m "not security"` 排除。
- 菜单可访问用例依赖菜单文字（English 界面）。切换语言会导致定位失败。

## 5. 验收

- `tests/` 全量 33 条在 SIT 上通过（12 条原有 + 21 条新增），连续运行两次结果一致。
