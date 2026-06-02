"""Session persistence: save, load, list, and clean up conversation history."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Default max sessions to keep per workspace
DEFAULT_MAX_SESSIONS = 20


@dataclass
class SessionInfo:
    """Metadata for a saved session."""

    session_id: str
    created_at: str  # ISO 8601
    summary: str
    message_count: int
    language: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> SessionInfo:
        return cls(**data)


def _serialize_messages(messages: list[BaseMessage]) -> list[dict]:
    """Convert LangChain messages to JSON-serializable dicts."""
    result = []
    for msg in messages:
        content = msg.content
        additional_kwargs = {}
        if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
            additional_kwargs = msg.additional_kwargs
        tool_calls = None
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_calls = msg.tool_calls

        result.append({
            "type": "human" if isinstance(msg, HumanMessage) else "ai",
            "content": content,
            "additional_kwargs": additional_kwargs,
            "tool_calls": tool_calls,
        })
    return result


def _deserialize_messages(data: list[dict]) -> list[BaseMessage]:
    """Convert JSON dicts back to LangChain messages."""
    messages = []
    for item in data:
        msg_type = item.get("type", "")
        content = item.get("content", "")
        additional_kwargs = item.get("additional_kwargs", {})
        tool_calls = item.get("tool_calls")

        if msg_type == "human":
            msg = HumanMessage(content=content, additional_kwargs=additional_kwargs)
        else:
            kwargs: dict = {"content": content, "additional_kwargs": additional_kwargs}
            if tool_calls:
                kwargs["tool_calls"] = tool_calls
            msg = AIMessage(**kwargs)
        messages.append(msg)
    return messages


def _generate_summary(messages: list[BaseMessage]) -> str:
    """Generate a short summary from session messages.

    Takes the first and last human message to create a meaningful summary.
    """
    human_msgs = [m for m in messages if isinstance(m, HumanMessage)]

    if not human_msgs:
        return "(空会话)"

    first = human_msgs[0].content
    first_line = first.split("\n")[0] if "\n" in first else first
    first_line = first_line[:80] + ("..." if len(first_line) > 80 else "")

    if len(human_msgs) >= 2:
        last = human_msgs[-1].content
        last_line = last.split("\n")[0] if "\n" in last else last
        last_line = last_line[:60] + ("..." if len(last_line) > 60 else "")
        return f"{first_line} → {last_line}"

    return first_line


def _sessions_dir(workspace: Path) -> Path:
    """Return the sessions directory path for a workspace."""
    return workspace / ".agents" / "sessions"


def save_session(
    workspace: Path,
    messages: list[BaseMessage],
    language: str = "zh",
    max_sessions: int = DEFAULT_MAX_SESSIONS,
) -> str:
    """Save a conversation session to disk.

    Writes two files:
      <workspace>/.agents/sessions/<timestamp>_<id>.json       (messages)
      <workspace>/.agents/sessions/<timestamp>_<id>.meta.json  (metadata)

    Returns the session_id.
    """
    if not messages:
        return ""

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    session_id = f"{timestamp}_{os.urandom(4).hex()}"

    summary = _generate_summary(messages)
    message_count = len(messages)
    created_at = datetime.now(timezone.utc).isoformat()

    serialized = _serialize_messages(messages)
    meta = SessionInfo(
        session_id=session_id,
        created_at=created_at,
        summary=summary,
        message_count=message_count,
        language=language,
    )

    sessions_dir = _sessions_dir(workspace)
    sessions_dir.mkdir(parents=True, exist_ok=True)

    msg_path = sessions_dir / f"{session_id}.json"
    msg_path.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")

    meta_path = sessions_dir / f"{session_id}.meta.json"
    meta_path.write_text(json.dumps(meta.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    _cleanup_old_sessions(sessions_dir, max_sessions)

    return session_id


def _cleanup_old_sessions(sessions_dir: Path, max_sessions: int) -> None:
    """Remove sessions beyond max_sessions count (oldest first)."""
    if not sessions_dir.is_dir():
        return

    meta_files = sorted(
        sessions_dir.glob("*.meta.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for meta_file in meta_files[max_sessions:]:
        session_id = meta_file.stem
        msg_file = sessions_dir / f"{session_id}.json"
        meta_file.unlink(missing_ok=True)
        msg_file.unlink(missing_ok=True)


def list_sessions(
    workspace: Path,
    limit: int = 3,
) -> list[SessionInfo]:
    """Return the most recent sessions for the given workspace.

    Sessions are sorted by created_at descending (newest first).
    """
    sessions_dir = _sessions_dir(workspace)
    if not sessions_dir.is_dir():
        return []

    meta_files = sorted(
        sessions_dir.glob("*.meta.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    results = []
    for meta_file in meta_files[:limit]:
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            results.append(SessionInfo.from_dict(data))
        except (OSError, json.JSONDecodeError, KeyError):
            continue

    return results


def load_session(workspace: Path, session_id: str) -> list[BaseMessage]:
    """Load and deserialize a session by session_id.

    Returns an empty list if the session doesn't exist.
    """
    sessions_dir = _sessions_dir(workspace)
    msg_path = sessions_dir / f"{session_id}.json"
    if not msg_path.is_file():
        return []

    try:
        data = json.loads(msg_path.read_text(encoding="utf-8"))
        return _deserialize_messages(data)
    except (OSError, json.JSONDecodeError):
        return []


def delete_session(workspace: Path, session_id: str) -> None:
    """Delete both message and metadata files for a session."""
    sessions_dir = _sessions_dir(workspace)
    msg_path = sessions_dir / f"{session_id}.json"
    meta_path = sessions_dir / f"{session_id}.meta.json"
    msg_path.unlink(missing_ok=True)
    meta_path.unlink(missing_ok=True)
