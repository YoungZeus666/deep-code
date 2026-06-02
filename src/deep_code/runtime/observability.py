"""Langfuse observability integration for Deep Code."""

from __future__ import annotations

import json
import os
from typing import Any


def _import_v4_callback_handler():
    from langfuse.langchain import CallbackHandler

    return CallbackHandler


def _init_v4_client(*, public_key: str, secret_key: str, host: str | None) -> None:
    from langfuse import Langfuse

    client_kwargs: dict[str, str] = {
        "public_key": public_key,
        "secret_key": secret_key,
    }
    if host:
        client_kwargs["host"] = host
        client_kwargs["base_url"] = host

    Langfuse(**client_kwargs)


def _build_handler(**kwargs: Any):
    """Construct a Langfuse CallbackHandler across Langfuse SDK versions."""
    try:
        CallbackHandler = _import_v4_callback_handler()
    except ImportError:
        from langfuse.callback import CallbackHandler  # type: ignore[no-redef]

    public_key = kwargs.get("public_key")
    secret_key = kwargs.get("secret_key")
    host = kwargs.get("host")

    # Langfuse v4 configures the client from env vars rather than constructor args.
    if secret_key:
        os.environ["LANGFUSE_SECRET_KEY"] = secret_key
    if host:
        os.environ["LANGFUSE_HOST"] = host
        os.environ.setdefault("LANGFUSE_BASE_URL", host)

    try:
        if public_key and secret_key:
            _init_v4_client(public_key=public_key, secret_key=secret_key, host=host)
        return CallbackHandler(public_key=public_key)
    except TypeError:
        legacy_kwargs = {"public_key": public_key}
        if secret_key:
            legacy_kwargs["secret_key"] = secret_key
        if host:
            legacy_kwargs["host"] = host
        return CallbackHandler(**legacy_kwargs)


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
    host = os.environ.get("LANGFUSE_HOST") or os.environ.get("LANGFUSE_BASE_URL")
    if host:
        kwargs["host"] = host

    try:
        return _build_handler(**kwargs)
    except Exception as exc:
        print(f"[deep-code] Langfuse init failed, tracing disabled: {exc}")
        return None


def _build_langfuse_metadata() -> dict[str, str]:
    try:
        import deepagents

        version = getattr(deepagents, "__version__", "unknown")
    except Exception:
        version = "unknown"

    return {
        "ls_integration": "deepagents",
        "versions": json.dumps({"deepagents": str(version)}, ensure_ascii=False, sort_keys=True),
    }


def get_langfuse_run_config() -> dict[str, list[object]] | None:
    """Return LangGraph run config with callbacks when Langfuse is enabled."""
    handler = get_langfuse_callback()
    if handler is None:
        return None
    return {
        "callbacks": [handler],
        "metadata": _build_langfuse_metadata(),
    }
