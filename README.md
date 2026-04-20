# Deep Code

AI programming assistant built on the [LangChain Deep Agents](https://github.com/langchain-ai/deepagents) framework.

## Feature Map

```
Deep Code
├── Interactive REPL
│   ├── Streaming response with real-time token output
│   ├── Tool call visualization
│   ├── Conversation history management
│   └── Slash commands (/help, /model, /workspace, /language, /clear, /quit)
│
├── Orchestrator Agent
│   ├── Intelligent task routing — delegates to subagents or handles directly
│   ├── Dynamic system prompt = base prompt + AGENTS.md + skills + language instruction
│   └── 4 Specialized Subagents
│       ├── code-generator  — write new code (functions, classes, modules, files)
│       ├── code-reviewer   — review for bugs, style, performance, security
│       ├── code-explainer  — explain how code works step by step
│       └── bug-fixer       — reproduce → diagnose → fix → verify cycle
│
├── Multi-Provider Support
│   ├── Anthropic (native, default)
│   ├── OpenAI (native)
│   └── OpenAI-Like (Qwen, DeepSeek, Kimi, GLM, Doubao, Ollama, vLLM, ...)
│
├── Project Context Integration
│   ├── AGENTS.md — project-level agent instructions, auto-injected into system prompt
│   └── Skills System
│       ├── skills/<name>/SKILL.md          — root-level skill definitions
│       ├── .agents/skills/<name>/SKILL.md  — agent-specific skills
│       └── references/*.md                 — optional reference docs per skill
│
├── Project Initialization (deep-code init)
│   ├── Language & framework detection (18 languages, 30+ frameworks)
│   ├── Entry point discovery
│   ├── Dev command detection (test, lint, build)
│   ├── Directory tree generation
│   └── Generates AGENTS.md + .agents/ scaffold
│
├── Internationalization (i18n)
│   ├── Chinese (default) / English
│   ├── /language command for runtime switching
│   └── DEEP_CODE_LANGUAGE env var for default
│
├── Built-in Tools (from Deep Agents)
│   ├── Filesystem: ls, read_file, write_file, edit_file, glob, grep
│   ├── Execution: execute (shell commands)
│   └── Planning: write_todos, task (subagent delegation)
│
└── Extension Point
    └── tools.py — add custom tools, merged with built-in tools
```

## Architecture

```
User prompt
  │
  ▼
CLI (Rich terminal UI, streaming)
  │
  ▼
Orchestrator Agent
  │  system_prompt = ORCHESTRATOR_PROMPT + AGENTS.md + skills + language
  │  delegates via `task` tool
  │
  ├─► code-generator   — writes new code
  ├─► code-reviewer    — reviews code quality
  ├─► code-explainer   — explains code logic
  └─► bug-fixer        — diagnoses and fixes bugs

All agents share: LocalShellBackend (filesystem + shell within workspace)
```

## Prerequisites

- Python 3.11+
- An API key for at least one provider

## Installation

```bash
git clone https://github.com/Yangzhi1201/deep-code.git
cd deep-code
pip install -e .
```

## Configuration

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

The system auto-detects which provider to use based on which `*_MODEL` env var is set. Priority: `OPENAI_LIKE_MODEL` > `OPENAI_MODEL` > `ANTHROPIC_MODEL` (default).

| Mode | Required env vars |
|---|---|
| **Anthropic** (default) | `ANTHROPIC_API_KEY` (+ optional `ANTHROPIC_MODEL`) |
| **OpenAI** | `OPENAI_MODEL` + `OPENAI_API_KEY` |
| **OpenAI-Like** | `OPENAI_LIKE_MODEL` + `OPENAI_LIKE_API_KEY` + `OPENAI_LIKE_BASE_URL` |

The **OpenAI-Like** mode works with any OpenAI-compatible endpoint: Qwen, MiniMax, Kimi, DeepSeek, GLM, Doubao, Ollama, vLLM, LiteLLM, etc.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Anthropic model name |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `OPENAI_MODEL` | - | OpenAI model name (e.g. `gpt-4o`) |
| `OPENAI_LIKE_API_KEY` | - | API key for OpenAI-Like endpoint |
| `OPENAI_LIKE_BASE_URL` | - | Base URL for OpenAI-Like endpoint |
| `OPENAI_LIKE_MODEL` | - | Model name for OpenAI-Like endpoint |
| `DEEP_CODE_WORKSPACE` | Current directory | Working directory for file operations |
| `DEEP_CODE_LANGUAGE` | `zh` | Interface language (`zh` or `en`) |

## Usage

```bash
# Start interactive assistant
deep-code

# Run as Python module
python -m deep_code

# Initialize a project (generates AGENTS.md + .agents/)
deep-code init
deep-code init /path/to/project
```

### Interactive Commands

| Command | Description |
|---|---|
| `/help` | Show help message |
| `/model` | Show current provider and model |
| `/workspace` | Show current workspace path |
| `/language` | Show current language |
| `/language zh` | Switch to Chinese |
| `/language en` | Switch to English |
| `/clear` | Clear conversation history |
| `/quit` | Exit the application |

### Example Prompts

```
You > Write a Python function that implements binary search
You > Review the code in src/main.py
You > Explain how the authentication middleware works
You > This test is failing with KeyError, can you fix it?
```

## Project Initialization

`deep-code init` scans a project directory and generates:

- **`AGENTS.md`** — Project context file with auto-detected metadata:
  - Languages and frameworks
  - Entry points (scripts, main files)
  - Directory structure
  - Development commands (test, lint, build)
- **`.agents/`** — Directory for additional agent context and custom skills

Supported detection:
- **18 languages**: Python, JavaScript, TypeScript, Java, Go, Rust, Ruby, PHP, Swift, Kotlin, C#, C++, C, Dart, Lua, Scala, Zig, Elixir
- **30+ frameworks**: Django, Flask, FastAPI, Next.js, Nuxt, Vite, Angular, Vue, Svelte, React, Spring, Cargo, Docker, GitHub Actions, and more

## Skill System

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

## Project Structure

```
src/deep_code/
├── __init__.py       # Package version
├── __main__.py       # python -m deep_code entry point
├── cli.py            # Interactive REPL, streaming, slash commands
├── agents.py         # Orchestrator + subagent factory, system prompt assembly
├── config.py         # AppConfig, provider auto-detection from env vars
├── init.py           # deep-code init — project scanner, AGENTS.md generator
├── prompts.py        # System prompts for orchestrator and 4 subagents
├── i18n.py           # Translation dictionaries (zh/en), language switching
└── tools.py          # Custom tool extension point
```

## Extending

Add custom tools in `src/deep_code/tools.py`. They are merged with the built-in Deep Agents tools (filesystem, execute, planning, subagents).

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

## License

MIT
