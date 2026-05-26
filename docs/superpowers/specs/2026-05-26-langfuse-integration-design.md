# Langfuse Integration Design

**Date:** 2026-05-26  
**Status:** Approved

## Goal

Integrate Langfuse observability into Deep Code so that all LLM calls —
orchestrator, subagents, and tool calls — are traced automatically in
Langfuse's UI as a full multi-agent call tree.

## Approach

Use Langfuse's LangChain `CallbackHandler`. Pass it to `create_deep_agent`
in `agents.py`. LangGraph propagates the callback automatically to all
nested subagent invocations and tool calls.

## Configuration

Three environment variables, consistent with existing `ANTHROPIC_API_KEY` etc.
in `.env`:

| Variable               | Required | Default                        |
|------------------------|----------|--------------------------------|
| `LANGFUSE_PUBLIC_KEY`  | Yes      | —                              |
| `LANGFUSE_SECRET_KEY`  | Yes      | —                              |
| `LANGFUSE_HOST`        | No       | `https://cloud.langfuse.com`   |

Langfuse is **disabled silently** when `LANGFUSE_PUBLIC_KEY` or
`LANGFUSE_SECRET_KEY` is absent. No error, no crash.

## Components

### `src/deep_code/observability.py` (new)

Single responsibility: build and return a `CallbackHandler`, or `None`.

```python
def get_langfuse_callback() -> object | None:
    ...
```

- Reads the three env vars.
- Returns `None` if keys are missing.
- Catches all init exceptions (missing package, bad key format, network
  errors at init time), prints a one-line warning, returns `None`.

### `src/deep_code/agents.py` (modified)

`create_coding_agent` calls `get_langfuse_callback()`.  
If the result is not `None`, passes it via `callbacks=[handler]` to
`create_deep_agent`.

No other files change.

## Data Flow

```
User input
  → cli.py: stream_response → agent.stream()
      → Orchestrator LLM call          [Langfuse span]
          → subagent via task tool      [Langfuse span]
              → tool calls (read_file…) [Langfuse span]
```

Callback propagation is handled by LangGraph — no manual passing at each layer.

## Dependency

Add to `pyproject.toml` runtime dependencies:

```
langfuse>=2.0.0
```

## Error Handling

All Langfuse init/runtime errors are caught inside `observability.py`.
Failure degrades gracefully: a warning is printed and tracing is disabled
for the session. The main flow is never interrupted.

## Files Changed

| File                                  | Change         |
|---------------------------------------|----------------|
| `src/deep_code/observability.py`      | New            |
| `src/deep_code/agents.py`             | Minor (5 lines)|
| `pyproject.toml`                      | Add dependency |
| `.env` / README                       | Document vars  |

## Out of Scope

- Manual trace/span naming or session-level grouping.
- Langfuse datasets, evals, or prompt management features.
- Any UI changes to the CLI.
