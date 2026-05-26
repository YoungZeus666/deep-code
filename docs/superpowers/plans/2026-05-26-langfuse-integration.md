# Langfuse Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Langfuse LangChain CallbackHandler into Deep Code so that all LLM calls, subagent calls, and tool calls are traced automatically.

**Architecture:** A new `observability.py` module reads Langfuse env vars and returns a `CallbackHandler` (or `None` if unconfigured). `create_coding_agent` in `agents.py` calls it and passes the result to `create_deep_agent` via the `callbacks` parameter. LangGraph propagates the callback to all nested layers automatically.

**Tech Stack:** `langfuse>=2.0.0`, `langfuse.langchain.CallbackHandler` (v3) with `langfuse.callback.CallbackHandler` as fallback (v2), existing `python-dotenv` env loading.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/deep_code/observability.py` | Create | Read env vars, build and return `CallbackHandler` or `None` |
| `src/deep_code/agents.py` | Modify | Import and call `get_langfuse_callback()`, pass result to `create_deep_agent` |
| `pyproject.toml` | Modify | Add `langfuse>=2.0.0` to runtime dependencies |
| `tests/test_observability.py` | Create | Unit tests for `get_langfuse_callback` |
| `tests/test_agents_prompt.py` | Modify | Add callback-wiring smoke tests |
| `README.md` | Modify | Document Langfuse env vars |

---

## Task 1: Add langfuse dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add dependency**

Edit `pyproject.toml`, add `langfuse>=2.0.0` to the `dependencies` list:

```toml
dependencies = [
    "deepagents>=0.5.0",
    "langchain-anthropic>=1.4.0",
    "langchain-openai>=0.3.0",
    "rich>=13.0.0",
    "python-dotenv>=1.0.0",
    "prompt_toolkit>=3.0.0",
    "pytest>=8.0.0",
    "langfuse>=2.0.0",
]
```

- [ ] **Step 2: Install the dependency**

```bash
pip install langfuse
```

Expected: exits 0, `pip show langfuse` shows version ≥ 2.0.0.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "feat(observability): add langfuse dependency"
```

---

## Task 2: Create observability module (TDD)

**Files:**
- Create: `tests/test_observability.py`
- Create: `src/deep_code/observability.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_observability.py`:

```python
from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch


def _reload():
    import deep_code.observability as m
    importlib.reload(m)
    return m


def test_returns_none_when_public_key_missing(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert _reload().get_langfuse_callback() is None


def test_returns_none_when_secret_key_missing(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert _reload().get_langfuse_callback() is None


def test_returns_handler_when_both_keys_present(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)

    mock_handler = MagicMock()
    with patch("deep_code.observability._build_handler", return_value=mock_handler):
        result = _reload().get_langfuse_callback()

    assert result is mock_handler


def test_returns_none_and_warns_when_init_raises(monkeypatch, capsys):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    with patch("deep_code.observability._build_handler", side_effect=Exception("bad key")):
        result = _reload().get_langfuse_callback()

    assert result is None
    captured = capsys.readouterr()
    assert "langfuse" in captured.out.lower()


def test_passes_custom_host_to_builder(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_HOST", "https://my.langfuse.example.com")

    captured_kwargs: dict = {}

    def fake_build(**kwargs):
        captured_kwargs.update(kwargs)
        return MagicMock()

    with patch("deep_code.observability._build_handler", side_effect=fake_build):
        _reload().get_langfuse_callback()

    assert captured_kwargs.get("host") == "https://my.langfuse.example.com"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_observability.py -v
```

Expected: `ModuleNotFoundError: No module named 'deep_code.observability'`

- [ ] **Step 3: Create `src/deep_code/observability.py`**

```python
"""Langfuse observability integration for Deep Code."""

from __future__ import annotations

import os


def _build_handler(**kwargs):
    """Construct a Langfuse CallbackHandler. Separated for testability."""
    try:
        from langfuse.langchain import CallbackHandler
    except ImportError:
        from langfuse.callback import CallbackHandler  # type: ignore[no-redef]
    return CallbackHandler(**kwargs)


def get_langfuse_callback() -> object | None:
    """Return a Langfuse CallbackHandler if credentials are configured.

    Returns None silently when LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY
    is absent. Returns None with a warning if initialisation fails.
    """
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        return None

    kwargs: dict = {
        "public_key": public_key,
        "secret_key": secret_key,
    }
    host = os.environ.get("LANGFUSE_HOST")
    if host:
        kwargs["host"] = host

    try:
        return _build_handler(**kwargs)
    except Exception as exc:
        print(f"[deep-code] Langfuse init failed, tracing disabled: {exc}")
        return None
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_observability.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/deep_code/observability.py tests/test_observability.py
git commit -m "feat(observability): add get_langfuse_callback with graceful fallback"
```

---

## Task 3: Wire callback into create_coding_agent

**Files:**
- Modify: `src/deep_code/agents.py`
- Modify: `tests/test_agents_prompt.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_agents_prompt.py`:

```python
import importlib
from unittest.mock import MagicMock, patch


def test_create_coding_agent_passes_langfuse_callback_when_present(tmp_path):
    mock_handler = MagicMock()
    captured: dict = {}

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with (
        patch("deep_code.agents.get_langfuse_callback", return_value=mock_handler),
        patch("deep_code.agents.create_deep_agent", side_effect=fake_create_deep_agent),
    ):
        import deep_code.agents as ag
        importlib.reload(ag)
        from deep_code.config import AppConfig
        config = AppConfig(
            workspace=tmp_path,
            provider="anthropic",
            model_name="claude-sonnet-4-20250514",
        )
        ag.create_coding_agent(config)

    assert mock_handler in (captured.get("callbacks") or [])


def test_create_coding_agent_omits_callbacks_when_langfuse_not_configured(tmp_path):
    captured: dict = {}

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with (
        patch("deep_code.agents.get_langfuse_callback", return_value=None),
        patch("deep_code.agents.create_deep_agent", side_effect=fake_create_deep_agent),
    ):
        import deep_code.agents as ag
        importlib.reload(ag)
        from deep_code.config import AppConfig
        config = AppConfig(
            workspace=tmp_path,
            provider="anthropic",
            model_name="claude-sonnet-4-20250514",
        )
        ag.create_coding_agent(config)

    assert not captured.get("callbacks")
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_agents_prompt.py -v -k "langfuse"
```

Expected: FAIL — `get_langfuse_callback` not yet imported in `agents.py`.

- [ ] **Step 3: Modify `src/deep_code/agents.py`**

Add import after the existing `from deep_code.tools import get_custom_tools` line:

```python
from deep_code.observability import get_langfuse_callback
```

Replace the `create_coding_agent` function with:

```python
def create_coding_agent(config: AppConfig) -> CompiledStateGraph:
    """Create the main Deep Code orchestrator agent."""
    backend = LocalShellBackend(root_dir=config.workspace)
    model = _build_chat_model(config)
    subagents = build_subagents(model)
    custom_tools = get_custom_tools()
    system_prompt = _build_system_prompt(config.workspace, config.language)

    langfuse_handler = get_langfuse_callback()
    callbacks = [langfuse_handler] if langfuse_handler is not None else None

    return create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        subagents=subagents,
        backend=backend,
        tools=custom_tools if custom_tools else None,
        name="deep-code",
        callbacks=callbacks,
    )
```

- [ ] **Step 4: Run all tests**

```bash
pytest -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/deep_code/agents.py tests/test_agents_prompt.py
git commit -m "feat(observability): wire Langfuse callback into create_coding_agent"
```

---

## Task 4: Document env vars in README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Find where env vars are documented**

```bash
grep -n "ANTHROPIC_API_KEY\|\.env\|env" README.md | head -20
```

- [ ] **Step 2: Add Langfuse section**

In the `.env` configuration section, after the existing provider env vars block, add:

```markdown
### Langfuse Observability (optional)

To enable LLM call tracing in [Langfuse](https://langfuse.com):

```env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com   # optional, defaults to cloud
```

When these variables are set, all orchestrator calls, subagent calls, and
tool calls are traced automatically. If they are absent, Deep Code runs
normally with no tracing.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add Langfuse env var documentation to README"
```

---

## Task 5: Manual smoke test

No automated test can verify actual Langfuse connectivity without real credentials.

- [ ] **Step 1: Configure .env with real credentials**

```env
LANGFUSE_PUBLIC_KEY=pk-lf-your-key
LANGFUSE_SECRET_KEY=sk-lf-your-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

- [ ] **Step 2: Start Deep Code and send a message**

```bash
deep-code
```

At the `>` prompt type: `What is 2 + 2?`

Expected: agent responds normally, no Langfuse error printed.

- [ ] **Step 3: Verify trace in Langfuse UI**

Open Langfuse → Traces. Confirm a trace exists with LLM spans for the orchestrator. If a subagent was invoked, nested spans should appear under it.

- [ ] **Step 4: Verify graceful degradation**

Remove `LANGFUSE_PUBLIC_KEY` from `.env`, restart, send a message.

Expected: Deep Code runs normally, no error or warning about Langfuse.
