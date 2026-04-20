# Deep Code

AI programming assistant built on the [LangChain Deep Agents](https://github.com/langchain-ai/deepagents) framework.

## Architecture

```
User <-> CLI (rich) <-> Orchestrator Agent
                          |-- code-generator subagent
                          |-- code-reviewer subagent
                          |-- code-explainer subagent
                          +-- bug-fixer subagent

All agents share: LocalShellBackend (filesystem + shell)
Built-in tools: ls, read_file, write_file, edit_file, glob, grep, execute, write_todos, task
```

The orchestrator delegates tasks to specialized subagents:

- **code-generator** - Writes new code (functions, classes, modules, files)
- **code-reviewer** - Reviews code for bugs, style, performance, security
- **code-explainer** - Explains how code works step by step
- **bug-fixer** - Diagnoses and fixes bugs with reproduce-diagnose-fix-verify cycle

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

## Usage

```bash
# Run with the CLI entry point
deep-code

# Or run as a Python module
python -m coder
```

### CLI Commands

| Command | Description |
|---|---|
| `/help` | Show help message |
| `/model` | Show current model |
| `/workspace` | Show current workspace |
| `/clear` | Clear conversation history |
| `/quit` | Exit the application |

### Example Prompts

```
You > Write a Python function that implements binary search
You > Review the code in src/main.py
You > Explain how the authentication middleware works
You > This test is failing with KeyError, can you fix it?
```

## Extending

Add custom tools in `src/coder/tools.py`. They are merged with the built-in Deep Agents tools (filesystem, execute, planning, subagents).

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
