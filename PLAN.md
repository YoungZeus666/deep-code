# ⏺ 基于对项目的深入了解，以下是功能规划建议，按优先级分三个阶段：

---

## Phase 1: 核心体验增强（近期）

### 1. 会话持久化

当前退出后对话全部丢失。可以做：

- `/save` / `/load` — 保存/恢复对话历史到 `.agents/sessions/`
- 自动保存最近一次会话，启动时提示是否恢复
- 支持命名会话：`/save debug-auth`

### 2. Git 集成

编程助手不集成 git 是最大的短板：

- `/commit` — 智能生成 commit message（分析 diff，Conventional Commits 格式）
- `/diff` — 展示当前改动摘要，让 agent 理解上下文
- `/branch` — 创建/切换分支
- agent 在修改文件前自动 stash，出错可回滚

### 3. 项目上下文增强

- 自动索引：启动时扫描项目结构，构建文件摘要缓存（不是每次都让 agent 从头 `ls`/`grep`）
- `.agents/context.md`：用户手写的持久上下文（比如 "这个项目用的是 monorepo，前端在 packages/web"）
- 智能文件推荐：用户提问时根据关键词自动推荐相关文件

### 4. 测试套件

项目本身没有测试，应该补上：

- 为每个模块写单元测试
- CI 配置（GitHub Actions）
- `hatch test` 或 `pytest` 集成

---

## Phase 2: 能力扩展（中期）

### 5. 新增子 Agent

- `test-writer` — 自动生成单元测试（分析函数签名、边界条件、mock 依赖）
- `refactorer` — 代码重构专家（提取函数、消除重复、改进命名）
- `doc-writer` — 自动生成/更新文档（docstring、API 文档、changelog）

### 6. MCP Server 支持

让 Deep Code 可以被 Claude Code / Cursor 等工具作为 MCP server 调用：

- 暴露 `code-review`、`code-explain` 等能力为 MCP tools
- 反过来也可以作为 MCP client 调用外部工具（数据库、API 等）

### 7. 技能市场（Skills Marketplace）

当前技能系统只支持本地文件：

- `deep-code skills search <keyword>` — 搜索社区技能
- `deep-code skills install <name>` — 从远程仓库安装技能到 `.agents/skills/`
- `deep-code skills publish` — 发布技能到社区
- 技能版本管理和依赖声明

### 8. 交互式 Diff 审查

- agent 修改文件后不直接写入，先展示 diff 预览
- 用户可以逐块 accept/reject
- 类似 `git add -p` 的交互体验

### 9. 多轮任务规划

- `/plan` — 让 agent 先制定计划，用户审批后再执行
- 复杂任务自动分解为子任务，逐步执行
- 任务进度可视化（类似 todo list）

---

## Phase 3: 高级特性（远期）

### 10. RAG / 代码库语义搜索

- 对大型项目建立向量索引（文件、函数、类）
- agent 提问时自动检索相关代码片段
- 增量更新索引（文件变更时）
- 可选后端：本地 FAISS 或 ChromaDB

### 11. Web UI

- 基于 WebSocket 的浏览器界面
- Markdown 渲染、代码高亮、diff 展示
- 文件树侧边栏
- 可以嵌入 VS Code WebView

### 12. 多 Agent 协作

- 多个 agent 并行工作（比如 reviewer 和 `test-writer` 同时运行）
- agent 之间可以交流（reviewer 发现问题 → bug-fixer 自动修复）
- 流水线模式：generate → review → fix → test → commit

### 13. 项目模板系统

- `deep-code new <template>` — 从模板创建新项目
- 内置模板：Python CLI、FastAPI、React、Go service 等
- 社区模板仓库

### 14. 团队配置共享

- `.agents/team-config.yml` — 团队级 agent 配置
- 统一的代码规范、review 标准、commit 风格
- 可以提交到 git 共享给团队

---

## 优先级建议

| 优先级 | 功能 | 理由 |
| --- | --- | --- |
| P0 | 会话持久化 | 用户最痛的点，退出即丢失 |
| P0 | Git 集成 | 编程助手的核心场景 |
| P0 | 测试套件 | 项目自身质量保障 |
| P1 | 交互式 Diff 审查 | 安全性和用户信任 |
| P1 | 新增子 Agent (test-writer) | 自动测试是高频需求 |
| P1 | 多轮任务规划 | 复杂任务的体验提升 |
| P2 | 技能市场 | 生态建设 |
| P2 | MCP Server | 与主流工具链集成 |
| P2 | RAG 索引 | 大型项目的必备能力 |
| P3 | Web UI | 拓展使用场景 |
| P3 | 多 Agent 协作 | 技术深水区，demo 价值大 |
