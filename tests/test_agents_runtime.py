from __future__ import annotations

from pathlib import Path
from unittest.mock import sentinel

from deep_code.config import AppConfig


def test_create_coding_agent_does_not_pass_callbacks(monkeypatch, tmp_path: Path) -> None:
    from deep_code import agents as agents_module

    captured: dict = {}
    backend_calls: list[dict] = []

    monkeypatch.setattr(agents_module, "_build_chat_model", lambda config: "model")
    monkeypatch.setattr(agents_module, "build_subagents", lambda model: ["subagent"])
    monkeypatch.setattr(agents_module, "get_custom_tools", lambda: ["tool"])
    monkeypatch.setattr(agents_module, "_build_system_prompt", lambda workspace, language: "prompt")
    monkeypatch.setattr(agents_module, "get_langfuse_run_config", lambda: {"callbacks": [sentinel.handler]})

    class FakeLocalShellBackend:
        def __init__(self, **kwargs):
            backend_calls.append(kwargs)

    monkeypatch.setattr(agents_module, "LocalShellBackend", FakeLocalShellBackend)

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return sentinel.agent

    monkeypatch.setattr(agents_module, "create_deep_agent", fake_create_deep_agent)

    config = AppConfig(
        provider="anthropic",
        model_name="claude-sonnet-4-20250514",
        workspace=tmp_path,
        language="zh",
    )

    result = agents_module.create_coding_agent(config)

    assert result is sentinel.agent
    assert "callbacks" not in captured
    assert captured["name"] == "deep-code"
    assert backend_calls == [{"root_dir": tmp_path, "virtual_mode": True}]


def test_get_agent_run_config_proxies_langfuse_config(monkeypatch) -> None:
    from deep_code import agents as agents_module

    monkeypatch.setattr(
        agents_module,
        "get_langfuse_run_config",
        lambda: {"callbacks": [sentinel.handler]},
    )

    assert agents_module.get_agent_run_config() == {"callbacks": [sentinel.handler]}
