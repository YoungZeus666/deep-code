from __future__ import annotations

import pytest

from deep_code.agent_commands import (
    AgentCommandError,
    build_agent_routing_message,
    parse_agent_command,
)


def test_parse_agent_command_success() -> None:
    result = parse_agent_command(
        "/agent test-writer 为 src/deep_code/cli.py 补测试",
        ["code-generator", "test-writer"],
    )

    assert result.agent_name == "test-writer"
    assert result.task == "为 src/deep_code/cli.py 补测试"


def test_parse_agent_command_requires_agent_name() -> None:
    with pytest.raises(AgentCommandError, match="missing_agent"):
        parse_agent_command("/agent", ["test-writer"])


def test_parse_agent_command_requires_task() -> None:
    with pytest.raises(AgentCommandError, match="missing_task"):
        parse_agent_command("/agent test-writer", ["test-writer"])


def test_parse_agent_command_rejects_unknown_agent() -> None:
    with pytest.raises(AgentCommandError, match="unknown_agent"):
        parse_agent_command("/agent mystery 写测试", ["test-writer"])


def test_build_agent_routing_message_mentions_agent_name_and_task() -> None:
    message = build_agent_routing_message("test-writer", "为 foo 写测试")

    assert "test-writer" in message
    assert "为 foo 写测试" in message
