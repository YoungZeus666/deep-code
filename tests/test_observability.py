from __future__ import annotations

import importlib
import json
from unittest.mock import MagicMock, patch


def _reload():
    import deep_code.runtime.observability as m
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
    monkeypatch.delenv("LANGFUSE_BASE_URL", raising=False)

    module = _reload()
    mock_handler = MagicMock()
    with patch.object(module, "_build_handler", return_value=mock_handler):
        result = module.get_langfuse_callback()

    assert result is mock_handler


def test_returns_none_and_warns_when_init_raises(monkeypatch, capsys):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    module = _reload()
    with patch.object(module, "_build_handler", side_effect=Exception("bad key")):
        result = module.get_langfuse_callback()

    assert result is None
    captured = capsys.readouterr()
    assert "langfuse" in captured.out.lower()


def test_passes_custom_host_to_builder(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_HOST", "https://my.langfuse.example.com")

    captured_kwargs: dict = {}
    module = _reload()

    def fake_build(**kwargs):
        captured_kwargs.update(kwargs)
        return MagicMock()

    with patch.object(module, "_build_handler", side_effect=fake_build):
        module.get_langfuse_callback()

    assert captured_kwargs.get("host") == "https://my.langfuse.example.com"


def test_prefers_base_url_when_host_missing(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.setenv("LANGFUSE_BASE_URL", "http://localhost:3000")

    captured_kwargs: dict = {}
    module = _reload()

    def fake_build(**kwargs):
        captured_kwargs.update(kwargs)
        return MagicMock()

    with patch.object(module, "_build_handler", side_effect=fake_build):
        module.get_langfuse_callback()

    assert captured_kwargs.get("host") == "http://localhost:3000"


def test_get_langfuse_run_config_wraps_handler(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    module = _reload()
    mock_handler = MagicMock()
    with patch.object(module, "_build_handler", return_value=mock_handler):
        run_config = module.get_langfuse_run_config()

    assert run_config == {
        "callbacks": [mock_handler],
        "metadata": {
            "ls_integration": "deepagents",
            "versions": json.dumps({"deepagents": "0.5.3"}, ensure_ascii=False, sort_keys=True),
        },
    }


def test_build_handler_initializes_v4_client_before_callback_handler(monkeypatch):
    module = _reload()

    created: list[tuple[str, dict]] = []

    class FakeCallbackHandler:
        def __init__(self, **kwargs):
            created.append(("handler", kwargs))

    def fake_init_v4_client(*, public_key: str, secret_key: str, host: str | None) -> None:
        created.append(
            (
                "client",
                {
                    "public_key": public_key,
                    "secret_key": secret_key,
                    "host": host,
                    "base_url": host,
                },
            )
        )

    monkeypatch.setattr(module, "_init_v4_client", fake_init_v4_client)
    monkeypatch.setattr(module, "_import_v4_callback_handler", lambda: FakeCallbackHandler)

    handler = module._build_handler(
        public_key="pk-test",
        secret_key="sk-test",
        host="http://localhost:3000",
    )

    assert isinstance(handler, FakeCallbackHandler)
    assert created == [
        (
            "client",
            {
                "public_key": "pk-test",
                "secret_key": "sk-test",
                "host": "http://localhost:3000",
                "base_url": "http://localhost:3000",
            },
        ),
        ("handler", {"public_key": "pk-test"}),
    ]
