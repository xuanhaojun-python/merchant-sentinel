# Merchant Sentinel 可视化测试平台 — 设计文档

- 日期：2026-11-09
- 状态：待评审
- 范围：整体架构 + 第 1 期详细设计

## 1. 背景与目标

现有 merchant-sentinel 是 pytest + Playwright 的 UI 自动化脚本工程（12 条用例），只能命令行执行、查看静态 HTML 报告。

目标：在其之上构建一个**本机使用**的可视化测试平台，左侧菜单包含：

数据看板、项目管理、元素管理、用例管理、脚本录制、脚本列表、套件管理、执行记录、报告管理、定时任务、通知列表。

### 已确定的约束

| 项 | 决定 |
|---|---|
| 用例形态 | **代码为主**：用例仍是 Python + Playwright 代码，平台负责管理 / 执行 / 调度 / 报告 |
| 使用方式 | **本机单人**：不做登录与权限 |
| 技术栈 | 后端 FastAPI + SQLite；前端 Vue 3 + Element Plus（Vite） |
| 端口 | 后端 / 平台访问端口 **8082**；前端开发服务器 5173（代理到 8082） |
| 现有代码 | `pages/`、`tests/`、`config/` 不改动，继续作为执行层，脱离平台仍可命令行 `pytest` |

### 非目标

- 低代码 / 可视化步骤编排（不做）
- 多用户、登录、权限、远程部署（不做）
- 自研测试引擎（不做，复用 pytest）

## 2. 分期规划

| 期 | 模块 | 交付效果 |
|---|---|---|
| **第 1 期（本文档详细设计）** | 平台骨架（11 项菜单）、项目管理、用例管理、执行记录、报告管理 | 选项目和环境 → 勾选用例 → 执行 → 实时日志 → 查看报告 |
| 第 2 期 | 套件管理、定时任务、通知列表 | 套件定时自动跑，结果推送到飞书 / 企微 |
| 第 3 期 | 元素管理、脚本录制、脚本列表 | 集中管理选择器；调用 `playwright codegen` 录制并保存脚本 |
| 第 4 期 | 数据看板 | 通过率趋势、失败最多的用例、耗时统计 |

第 1 期中，11 个菜单全部显示，未实现模块的页面显示"建设中"。

## 3. 整体架构

```
┌───────────── 浏览器 localhost:8082 ────────────┐
│  Vue3 + Element Plus（左侧 11 个菜单）           │
└───────────────┬───────────────────────────────┘
                │ HTTP（REST）/ WebSocket（实时日志）
┌───────────────▼───────────────────────────────┐
│ FastAPI 后端（sentinel/backend）                │
│  ├─ API 层：项目 / 环境 / 用例 / 执行 / 报告     │
│  ├─ 用例扫描器：pytest --collect-only           │
│  ├─ 执行器：队列 + 子进程运行 pytest ─────┐      │
│  ├─ 调度器：APScheduler（第 2 期）         │      │
│  └─ 通知：webhook（第 2 期）               │      │
│ SQLite（元数据） + 文件系统（运行产物）      │      │
└───────────────────────────────────────────┼─────┘
                                            ▼
                pytest + Playwright（现有 tests/ pages/ config/）
                输出：pytest-json-report JSON + 截图 → 回写数据库
```

核心原则：**平台只负责调度 pytest，不实现测试逻辑。**

## 4. 目录结构

```
merchant-sentinel/
├── config/ pages/ tests/ utils/      # 现有执行层，不改动
├── sentinel/                         # 新增：平台
│   ├── __main__.py                   # python -m sentinel → 启动 uvicorn :8082
│   ├── backend/
│   │   ├── main.py                   # FastAPI app、路由注册、静态文件托管
│   │   ├── db.py                     # SQLAlchemy engine / session
│   │   ├── models.py                 # ORM 模型
│   │   ├── schemas.py                # Pydantic 请求 / 响应模型
│   │   ├── api/                      # projects.py environments.py cases.py runs.py reports.py
│   │   └── services/
│   │       ├── scanner.py            # 用例扫描
│   │       ├── runner.py             # 执行队列与子进程管理
│   │       └── result_parser.py      # 解析 JSON 结果 → CaseResult
│   ├── frontend/                     # Vite + Vue3 + Element Plus + Vue Router + Pinia
│   │   └── src/{layout,views,api,router,stores}/
│   ├── tests/                        # 平台自身的后端测试
│   └── data/                         # 运行时数据（不入库）
│       ├── sentinel.db
│       └── runs/<run_id>/            # output.log, report.json, screenshots/
└── Makefile                          # make dev / make build / make test-platform
```

不使用 `platform` 作为包名，避免与 Python 标准库 `platform` 冲突。

## 5. 数据模型

| 表 | 关键字段 | 说明 |
|---|---|---|
| Project | id, name, description, root_path, created_at | `root_path` 指向一个 pytest 工程目录，默认当前仓库 |
| Environment | id, project_id, name, base_url, email, password, headless, is_default | 执行时通过环境变量注入；密码明文存本机 SQLite |
| TestCase | id, project_id, nodeid, file, name, markers(JSON), docstring, remark, tags(JSON), status(active/removed), synced_at | `nodeid` 如 `tests/test_00_login.py::test_login_success`，唯一键 (project_id, nodeid) |
| Run | id, project_id, environment_id, trigger(manual/schedule), status, selected_nodeids(JSON), total, passed, failed, skipped, duration, exit_code, created_at, started_at, finished_at | 一次执行 |
| CaseResult | id, run_id, test_case_id(nullable), nodeid, outcome, duration, steps(JSON), error, screenshot_path | 一条用例的结果 |

第 2–3 期再增加：Suite、SuiteCase、Schedule、Notification、Element、Script。

**Run.status 状态机**：`queued → running → passed | failed | error | stopped | interrupted`

- `passed`：退出码 0
- `failed`：存在失败用例（退出码 1）
- `error`：pytest 异常退出（退出码 ≥ 2）或未生成 JSON 结果
- `stopped`：用户手动停止
- `interrupted`：后端重启时仍处于 queued / running 的执行

## 6. 关键流程

### 6.1 用例同步

1. 在 `project.root_path` 下以子进程运行 `python -m pytest --collect-only -q -p sentinel.backend.services.collect_plugin`。这个插件在 `pytest_collection_finish` 中把每个用例的 nodeid、markers、docstring 写入 `MS_COLLECT_FILE` 指定的 JSON 文件，并在 `pytest_collectreport` 中记录导入失败的文件和错误信息。
2. 与数据库比对：新增的用例插入；已存在的更新 markers 和 docstring；代码中已删除的标记为 `removed`（不物理删除，保留历史结果关联）。
3. `remark` 和 `tags` 是平台侧的附加信息，同步时不会被覆盖。
4. 某个文件导入失败时，记录错误并在页面上提示，其他文件照常同步。

### 6.2 执行

1. 前端提交 `{project_id, environment_id, nodeids[]}`，创建一条 `queued` 状态的 Run。
2. 执行器是单 worker 队列：**同一时间只运行 1 个 Run**（现有用例共享 session 级登录态，而且 Playwright 资源占用高）。
3. 启动子进程，`cwd` 设为 `project.root_path`：
   ```
   python -m pytest <nodeids...> -p no:cacheprovider
     --json-report --json-report-file=sentinel/data/runs/<id>/report.json
   ```
   通过环境变量注入：`MS_BASE_URL`、`MS_EMAIL`、`MS_PASSWORD`、`MS_HEADLESS`、`MS_RUN_DIR`。
4. 逐行读取 stdout 和 stderr，同时写入 `output.log` 并通过 WebSocket `/ws/runs/{id}/log` 推送；前端中途连上时，先补发已有日志。
5. 进程结束后，解析 JSON 结果生成 CaseResult，更新 Run 的统计数据和状态。
6. **停止执行**：发送 SIGTERM，5 秒后进程仍未退出则 SIGKILL，状态记为 `stopped`。

### 6.3 截图与步骤

- 现有 `tests/conftest.py` 中的截图路径改为优先使用环境变量 `MS_RUN_DIR`（未设置时保持原行为 `reports/screenshots/`）。这是对执行层唯一的改动，向后兼容。
- 步骤沿用现有约定：stdout 中以 `[` 开头的行，从 JSON 结果的 `call.stdout` 中解析。

## 7. API（第 1 期）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET/POST | `/api/projects` | 列表 / 新建 |
| GET/PUT/DELETE | `/api/projects/{id}` | 详情 / 修改 / 删除 |
| GET/POST | `/api/projects/{id}/environments` | 环境列表 / 新建 |
| PUT/DELETE | `/api/environments/{id}` | 修改 / 删除 |
| POST | `/api/projects/{id}/cases/sync` | 同步用例，返回 新增/更新/移除 数量和错误 |
| GET | `/api/projects/{id}/cases` | 用例列表，支持按 文件 / marker / 关键字 / 状态 筛选 |
| PUT | `/api/cases/{id}` | 修改 remark / tags |
| POST | `/api/runs` | 创建执行 |
| GET | `/api/runs` | 执行记录列表（分页，按项目 / 状态筛选） |
| GET | `/api/runs/{id}` | 执行详情和用例结果 |
| POST | `/api/runs/{id}/stop` | 停止执行 |
| GET | `/api/runs/{id}/log` | 完整日志（文本） |
| WS | `/ws/runs/{id}/log` | 实时日志 |
| GET | `/api/runs/{id}/screenshots/{name}` | 截图文件 |

**报告管理**直接复用 Run 数据：报告列表等于状态已结束的 Run 列表，报告详情页由前端用 Run 详情和 CaseResult 渲染。第 1 期不另建报告表。

## 8. 前端页面（第 1 期）

- **布局**：左侧固定菜单（11 项，带图标）；顶部显示当前项目切换器；右侧是内容区。
- **项目管理**：项目表格 + 新建 / 编辑对话框；项目详情页里有环境子表格。
- **用例管理**：左侧按文件分组的树；右侧用例表格（nodeid、marker 标签、描述、最近一次结果），支持多选；顶部有"同步用例"按钮，以及"执行所选"按钮（执行前选择环境）。
- **执行记录**：表格（ID、状态标签、通过/失败/跳过、耗时、触发方式、时间）；详情页上半部分是实时日志终端（等宽字体、自动滚动），下半部分是用例结果表；运行中可以停止。
- **报告管理**：已结束执行的列表；报告详情包括汇总卡片（通过/失败/跳过/总计/耗时），以及逐条用例的步骤、错误信息和失败截图（点击放大）。
- **未实现模块**：使用 `el-empty`，提示"建设中，计划于第 N 期上线"。

## 9. 异常处理

| 场景 | 处理 |
|---|---|
| 后端重启时存在 queued / running 的 Run | 启动时统一标记为 `interrupted` |
| pytest 异常退出 / 未生成 report.json | Run 记为 `error`，保留完整日志 |
| 用例同步时某文件导入失败 | 跳过该文件，接口返回错误列表，前端提示 |
| 项目 `root_path` 不存在或不是 pytest 工程 | 新建 / 修改项目时校验并拒绝 |
| 环境未配置密码 | 允许保存；执行时由现有的 `require_credentials()` 报错，Run 记为 `error` |
| 删除有执行记录的项目 | 二次确认后级联删除，包括运行产物目录 |

## 10. 测试策略

- **后端**：pytest + FastAPI `TestClient`，使用临时 SQLite。
  - 扫描器和执行器使用 `sentinel/tests/fixtures/sample_project/`：一个不依赖浏览器的假 pytest 工程，包含通过、失败、跳过三类用例，几秒就能跑完，**不连接 SIT**。
  - 覆盖：同步时的增改删、执行状态机、停止执行、重启后标记 interrupted、结果解析。
- **前端**：第 1 期不写自动化测试，手工冒烟。
- **验收**：在平台上创建 merchant-sentinel 项目和 SIT 环境，同步出 12 条用例，全量执行，实时日志正常，报告和截图展示正确，12 条全部通过。

## 11. 运行方式

| 场景 | 命令 |
|---|---|
| 开发 | `make dev`：同时启动 uvicorn `:8082`（--reload）和 Vite `:5173`（`/api`、`/ws` 代理到 8082） |
| 构建前端 | `make build`：输出到 `sentinel/frontend/dist` |
| 日常使用 | `python -m sentinel`：在 `:8082` 同时提供 API 和前端页面，访问 `http://localhost:8082` |
| 平台测试 | `make test-platform` |

新增依赖：后端 `fastapi`、`uvicorn[standard]`、`sqlalchemy`、`pytest-json-report`（第 2 期再加 `apscheduler`）；前端需要 Node.js 18 以上。

`.gitignore` 新增：`sentinel/data/`、`sentinel/frontend/node_modules/`、`sentinel/frontend/dist/`。
