<p align="center">
  <h1 align="center">🛠️ Deep Code / 深度代码</h1>
  <p align="center">AI programming assistant built on <a href="https://github.com/langchain-ai/deepagents">LangChain Deep Agents</a></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"/>
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen" alt="PRs Welcome"/>
  <img src="https://img.shields.io/badge/Powered%20by-LangChain-important" alt="LangChain"/>
  <img src="https://img.shields.io/badge/version-0.1.0-blueviolet" alt="Version 0.1.0"/>
</p>

---

<details>
<summary><b>🇨🇳 中文介绍</b></summary>

**Deep Code (深度代码)** 是一款基于 [LangChain Deep Agents](https://github.com/langchain-ai/deepagents) 框架构建的 AI 编程助手。它通过交互式 REPL 与用户协作，支持多智能体协作、多模型提供商、项目上下文感知和国际化（中文/英文）。

核心特性包括：
- **交互式终端** — 实时流式输出、工具调用可视化、对话历史管理
- **编排智能体** — 智能任务路由，自动委派给 6 个内置子智能体
- **多提供商支持** — Anthropic（默认）、OpenAI、OpenAI-Like（Qwen、DeepSeek、Kimi 等）
- **项目感知** — 自动检测 18 种语言、30+ 框架，生成 `AGENTS.md`
- **技能系统** — 通过 Markdown 技能文件扩展编排器能力
- **可观测性** — 可选 Langfuse LLM 追踪集成

</details>

---

## 📑 Table of Contents

<details open>
<summary><b>Expand / Collapse</b></summary>

- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [💻 Usage](#-usage)
- [🏗️ Architecture](#️-architecture)
- [📁 Project Structure](#-project-structure)
- [🔭 Observability](#-observability)
- [🛠️ Skill System](#️-skill-system)
- [📐 Extending](#-extending)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)
- [🔗 Related Projects](#-related-projects)
- [❓ Troubleshooting](#-troubleshooting)
- [📄 License](#-license)

</details>

---

## ✨ Features

| Category | Features |
|----------|----------|
| **💬 Interactive REPL** | Streaming response with real-time token output · Tool call visualization · Conversation history management · Slash commands (`/help`, `/agent`, `/model`, `/workspace`, `/language`, `/clear`, `/init`, `/plan`, `/mode`, `/quit`) |
| **🧠 Orchestrator Agent** | Intelligent task routing — delegates to subagents or handles directly · Dynamic system prompt = base prompt + subagent catalog + `AGENTS.md` + skills + language instruction · Automatic multi-agent collaboration for parallel work and delivery pipelines |
| **🤖 6 Built-in Subagents** | `code-generator` — write new code (functions, classes, modules, files) · `code-reviewer` — review for bugs, style, performance, security · `code-explainer` — explain how code works step by step · `bug-fixer` — reproduce → diagnose → fix → verify cycle · `test-writer` — add or extend automated tests for existing code · `git-committer` — create verified task-related git commits |
| **🔌 Multi-Provider Support** | Anthropic (native, default) · OpenAI (native) · OpenAI-Like (Qwen, DeepSeek, Kimi, GLM, Doubao, Ollama, vLLM, etc.) |
| **📂 Project Context Integration** | `AGENTS.md` — project-level agent instructions, auto-injected into system prompt · Skills System: `skills/<name>/SKILL.md` (root-level) + `.agents/skills/<name>/SKILL.md` (agent-specific) + `references/*.md` (optional reference docs per skill) |
| **🚀 Project Initialization** | `deep-code init` — Language & framework detection (18 languages, 30+ frameworks) · Entry point discovery · Dev command detection (test, lint, build) · Directory tree generation · Generates `AGENTS.md` + `.agents/` scaffold |
| **💾 Session Persistence** | Auto-saves conversation history per workspace · Restore recent sessions at startup (up to 3 shown) · Configurable max sessions via `DEEP_CODE_MAX_SESSIONS` |
| **🔒 Workspace Trust** | Prompts once for workspace confirmation · Persists trusted workspaces to `~/.config/deep-code/trusted.json` |
| **🌐 Internationalization (i18n)** | Chinese (default) / English · `/language` command for runtime switching · `DEEP_CODE_LANGUAGE` env var for default |
| **📊 Observability (Langfuse)** | Optional LLM tracing via Langfuse callback · Zero-config when credentials absent — tracing silently disabled · Configurable host for self-hosted Langfuse deployments |
| **🧰 Built-in Tools (from Deep Agents)** | Filesystem: `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep` · Execution: `execute` (shell commands) · Planning: `write_todos`, `task` (subagent delegation) |
| **🔧 Extension Point** | `runtime/tools.py` — add custom tools, merged with built-in tools |

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Yangzhi1201/deep-code.git
cd deep-code

# 2. Copy and configure environment
cp .env.example .env
# Edit .env and add your API key (see Configuration section)

# 3. Install
pip install -e .

# 4. Run
deep-code
```

> [!TIP]
> If you just want to test things out, set `ANTHROPIC_API_KEY` in `.env` and run `deep-code` — the default model is Claude Sonnet 4.

---

## 📦 Installation

### Basic Install

```bash
git clone https://github.com/Yangzhi1201/deep-code.git
cd deep-code
pip install -e .
```

### Development Install

```bash
pip install -e ".[dev]"
```

### Run as Module

```bash
python -m deep_code
```

### Prerequisites

- **Python 3.11+**
- An API key for at least one provider (Anthropic, OpenAI, or OpenAI-compatible)

---

## ⚙️ Configuration

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

### Provider Selection

The system auto-detects which provider to use based on which `*_MODEL` env var is set.

**Priority:** `OPENAI_LIKE_MODEL` > `OPENAI_MODEL` > `ANTHROPIC_MODEL` (default)

| Mode | Required env vars | Description |
|------|-------------------|-------------|
| **Anthropic** (default) | `ANTHROPIC_API_KEY` (+ optional `ANTHROPIC_MODEL`) | Claude models via Anthropic API |
| **OpenAI** | `OPENAI_MODEL` + `OPENAI_API_KEY` | GPT models via OpenAI API |
| **OpenAI-Like** | `OPENAI_LIKE_MODEL` + `OPENAI_LIKE_API_KEY` + `OPENAI_LIKE_BASE_URL` | Any OpenAI-compatible endpoint |

The **OpenAI-Like** mode works with any OpenAI-compatible endpoint: Qwen, MiniMax, Kimi, DeepSeek, GLM, Doubao, Ollama, vLLM, LiteLLM, etc.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Anthropic model name |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_MODEL` | — | OpenAI model name (e.g. `gpt-4o`) |
| `OPENAI_LIKE_API_KEY` | — | API key for OpenAI-Like endpoint |
| `OPENAI_LIKE_BASE_URL` | — | Base URL for OpenAI-Like endpoint |
| `OPENAI_LIKE_MODEL` | — | Model name for OpenAI-Like endpoint |
| `DEEP_CODE_WORKSPACE` | Current directory | Working directory for file operations |
| `DEEP_CODE_LANGUAGE` | `zh` | Interface language (`zh` or `en`) |
| `DEEP_CODE_MAX_SESSIONS` | `20` | Max saved sessions per workspace |
| `LANGFUSE_PUBLIC_KEY` | — | Langfuse public key (enables tracing when set) |
| `LANGFUSE_SECRET_KEY` | — | Langfuse secret key (enables tracing when set) |
| `LANGFUSE_HOST` | Langfuse cloud | Override for self-hosted Langfuse (e.g. `http://localhost:3000`) |

### Provider Examples

To change models, set the corresponding env vars in your `.env`:

```bash
# Anthropic Claude (default)
ANTHROPIC_API_KEY=sk-xxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o

# OpenAI-Like: Qwen
OPENAI_LIKE_MODEL=qwen-max
OPENAI_LIKE_API_KEY=sk-xxx
OPENAI_LIKE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# OpenAI-Like: Kimi
OPENAI_LIKE_MODEL=kimi-k2
OPENAI_LIKE_API_KEY=sk-xxx
OPENAI_LIKE_BASE_URL=https://api.moonshot.cn/v1

# OpenAI-Like: DeepSeek
OPENAI_LIKE_MODEL=deepseek-chat
OPENAI_LIKE_API_KEY=sk-xxx
OPENAI_LIKE_BASE_URL=https://api.deepseek.com/v1

# OpenAI-Like: local Ollama
OPENAI_LIKE_MODEL=llama3
OPENAI_LIKE_API_KEY=ollama
OPENAI_LIKE_BASE_URL=http://localhost:11434/v1
```

---

## 💻 Usage

### Starting the Assistant

```bash
# Start interactive assistant
deep-code

# Run as Python module
python -m deep_code
```

### Project Initialization

```bash
# Initialize the current project
deep-code init

# Initialize a specific project directory
deep-code init /path/to/project
```

`deep-code init` scans a project directory and generates:

- **`AGENTS.md`** — Project context file with auto-detected metadata:
  - Languages and frameworks
  - Entry points (scripts, main files)
  - Directory structure
  - Development commands (test, lint, build)
- **`.agents/`** — Directory for additional agent context and custom skills

**Supported detection:**
- **18 languages**: Python, JavaScript, TypeScript, Java, Go, Rust, Ruby, PHP, Swift, Kotlin, C#, C++, C, Dart, Lua, Scala, Zig, Elixir
- **30+ frameworks**: Django, Flask, FastAPI, Next.js, Nuxt, Vite, Angular, Vue, Svelte, React, Spring, Cargo, Docker, GitHub Actions, and more

### Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help message |
| `/agent` | Route a task to a specific built-in subagent |
| `/model` | Show current provider and model |
| `/workspace` | Show current workspace path |
| `/language` | Show current language |
| `/language zh` | Switch to Chinese |
| `/language en` | Switch to English |
| `/clear` | Clear conversation history |
| `/init` | Re-generate `AGENTS.md` for the current workspace |
| `/plan` | Enter plan mode |
| `/mode agent` | Switch to agent mode |
| `/mode plan` | Switch to plan mode |
| `/quit` | Exit the application |

### Example Prompts

```
You > Write a Python function that implements binary search
You > Review the code in src/main.py
You > Explain how the authentication middleware works
You > This test is failing with KeyError, can you fix it?
You > /agent test-writer add tests for src/deep_code/cli/app.py
```

---

## 🏗️ Architecture

```
User prompt
  │
  ▼
CLI (Rich terminal UI, streaming)
  │
  ▼
Orchestrator Agent
  │  system_prompt = ORCHESTRATOR_PROMPT + subagent catalog + AGENTS.md + skills + language
  │  delegates via `task` tool
  │  can launch parallel subagents and coordinate
  │  generate -> review -> fix -> test -> commit
  │
  ├─► code-generator   — writes new code
  ├─► code-reviewer    — reviews code quality
  ├─► code-explainer   — explains code logic
  ├─► bug-fixer        — diagnoses and fixes bugs
  ├─► test-writer      — writes and updates tests
  └─► git-committer    — commits verified task-related changes

All agents share: LocalShellBackend (filesystem + shell within workspace)
```

Automatic collaboration is triggered from normal conversation flow when a task naturally decomposes into independent work or a delivery pipeline. Agent-to-agent handoffs are mediated by the orchestrator using structured stage summaries.

---

## 📁 Project Structure

<details>
<summary><b>Click to expand</b></summary>

```
src/deep_code/
├── __init__.py       # Package version
├── __main__.py       # python -m deep_code entry point
├── agents/
│   ├── factory.py        # Orchestrator factory, system prompt assembly
│   ├── registry.py       # Built-in subagent registry and catalog rendering
│   ├── prompts.py        # System prompts for orchestrator and built-in subagents
│   └── collaboration.py  # Structured reports + collaboration playbook
├── bootstrap/
│   ├── runner.py         # deep-code init — project scanner, AGENTS.md generator
│   └── detection.py      # Language/framework detection constants
├── cli/
│   ├── app.py            # Interactive REPL, streaming, slash commands
│   ├── commands.py       # /agent parser and explicit routing helpers
│   └── plan_mode.py      # /plan and /mode command handlers
├── core/
│   ├── config.py         # AppConfig, provider auto-detection, trusted workspaces
│   ├── i18n.py           # Translation dictionaries (zh/en), language switching
│   └── session.py        # Session persistence: save/load/list/delete
└── runtime/
    ├── tools.py          # Custom tool extension point
    └── observability.py  # Langfuse tracing — get_langfuse_run_config()
```

</details>

---

## 🔭 Observability

Deep Code integrates with [Langfuse](https://langfuse.com) for LLM tracing. Set the following env vars to enable:

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
# Optional: override for self-hosted Langfuse
LANGFUSE_HOST=http://localhost:3000
```

> [!NOTE]
> Tracing is **opt-in**: when the keys are absent, the system starts normally with no tracing and no errors. Traces are attached as LangChain callbacks, so every orchestrator and subagent invocation is captured automatically.

---

## 🛠️ Skill System

Skills are markdown files that extend the orchestrator's capabilities. They are loaded from two directories:

```
skills/                        # Root-level skills
  └── git-commit/
      └── SKILL.md

.agents/skills/                # Agent-specific skills
  └── my-custom-skill/
      ├── SKILL.md             # Required: skill definition
      └── references/          # Optional: reference documents
          └── api-docs.md
```

Skill content is appended to the system prompt at startup. The `/language` command recreates the agent, re-loading all skills.

---

## 📐 Extending

### Custom Tools

Add custom tools in `src/deep_code/runtime/tools.py`. They are merged with the built-in Deep Agents tools (filesystem, execute, planning, subagents).

### Custom Subagents

Built-in subagents are defined through a registry in `src/deep_code/agents/registry.py`. To add another one, register its metadata there and add the corresponding prompt constant in `src/deep_code/agents/prompts.py`.

### Custom Models

To change models, set the corresponding env vars in your `.env` (see the [Configuration](#️-configuration) section for full examples).

---

## 🗺️ Roadmap

### Phase 1: Core Experience Enhancement (Near-term)

| Feature | Description |
|---------|-------------|
| **Session Persistence** | `/save` / `/load` — save/restore conversation history to `.agents/sessions/`; auto-save last session; named sessions (`/save debug-auth`) |
| **Git Integration** | `/commit` — smart commit message generation (diff analysis, Conventional Commits); `/diff` — show change summary; `/branch` — create/switch branches; auto-stash before edits, rollback on error |
| **Project Context Enhancement** | Auto-index: scan project on startup, build file summary cache; `.agents/context.md` — user-written persistent context; smart file recommendations based on keywords |
| **Test Suite** | Unit tests for every module; CI configuration (GitHub Actions); `hatch test` / `pytest` integration |

### Phase 2: Capability Expansion (Medium-term)

| Feature | Description |
|---------|-------------|
| **New Subagents** | `test-writer` — auto-generate unit tests; `refactorer` — code refactoring expert; `doc-writer` — auto-generate/update documentation |
| **MCP Server Support** | Expose Deep Code capabilities as MCP tools for Claude Code / Cursor; act as MCP client for external tools (databases, APIs) |
| **Skills Marketplace** | `deep-code skills search` — search community skills; `deep-code skills install` — install from remote; `deep-code skills publish` — publish to community; version management and dependency declarations |
| **Interactive Diff Review** | Show diff preview before file writes; per-hunk accept/reject; `git add -p`-like interactive experience |
| **Multi-turn Task Planning** | `/plan` — agent creates plan, user approves before execution; complex tasks auto-decomposed into subtasks; task progress visualization |

### Phase 3: Advanced Features (Long-term)

| Feature | Description |
|---------|-------------|
| **RAG / Codebase Semantic Search** | Vector index for large projects (files, functions, classes); auto-retrieve relevant code snippets; incremental index updates; local FAISS or ChromaDB backends |
| **Web UI** | Browser-based interface via WebSocket; Markdown rendering, code highlighting, diff display; file tree sidebar; VS Code WebView embeddable |
| **Multi-Agent Collaboration** | Parallel subagent execution; inter-agent communication (reviewer finds issues → bug-fixer auto-fixes); pipeline mode: generate → review → fix → test → commit |
| **Project Templates** | `deep-code new <template>` — create projects from templates; built-in templates: Python CLI, FastAPI, React, Go service, etc.; community template repository |
| **Team Configuration Sharing** | `.agents/team-config.yml` — team-level agent configuration; unified code style, review standards, commit conventions; git-shareable |

### Priority Summary

| Priority | Feature | Rationale |
|----------|---------|-----------|
| P0 | Session Persistence | Most painful user pain point — exit loses everything |
| P0 | Git Integration | Core scenario for a programming assistant |
| P0 | Test Suite | Project's own quality assurance |
| P1 | Interactive Diff Review | Safety and user trust |
| P1 | New Subagents (test-writer) | Auto-testing is a high-frequency need |
| P1 | Multi-turn Task Planning | Complex task experience improvement |
| P2 | Skills Marketplace | Ecosystem building |
| P2 | MCP Server | Integration with mainstream toolchains |
| P2 | RAG Index | Essential for large projects |
| P3 | Web UI | Expanding use cases |
| P3 | Multi-Agent Collaboration | Deep tech, high demo value |

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Guidelines

- Follow the existing code style and conventions
- Add tests for new features when possible
- Update documentation as needed
- Keep pull requests focused on a single concern

> [!NOTE]
> This project is in early development. The API and architecture are still evolving. Feel free to open issues for bugs, feature requests, or questions!

---

## 🔗 Related Projects

| Project | Description |
|---------|-------------|
| [LangChain Deep Agents](https://github.com/langchain-ai/deepagents) | The foundational agent framework that Deep Code builds upon |
| [LangChain](https://github.com/langchain-ai/langchain) | LLM application development framework |
| [DeepSeek](https://deepseek.com) | OpenAI-compatible LLM provider supported via OpenAI-Like mode |
| [Langfuse](https://langfuse.com) | Open-source LLM observability & tracing platform |

---

## ❓ Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **`ModuleNotFoundError: No module named 'deep_code'`** | Ensure you've run `pip install -e .` from the project root directory |
| **API key not recognized** | Verify your `.env` file is present and correctly formatted. Check that the relevant env var (e.g. `ANTHROPIC_API_KEY`) is set |
| **Model not found / API error** | Confirm your API key has access to the specified model. For OpenAI-Like providers, verify the `BASE_URL` is correct |
| **Session not restored** | Sessions are per-workspace. Run `deep-code` from the same directory where you previously worked |
| **Language not switching** | Use `/language zh` or `/language en` in the REPL, or set `DEEP_CODE_LANGUAGE` env var before starting |
| **Langfuse tracing not working** | Ensure all three `LANGFUSE_*` env vars are set correctly. Tracing is silently disabled when any key is missing |
| **`deep-code init` detects wrong language** | Check that your project files are in the working directory. The detector scans for known file extensions and framework markers |

> [!TIP]
> For more help, open an issue on the [GitHub repository](https://github.com/Yangzhi1201/deep-code/issues).

---

## 📄 License

Distributed under the MIT License. See the repository for details.
