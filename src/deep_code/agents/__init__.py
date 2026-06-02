"""Agent factory and subagent registry."""
from deep_code.agents.factory import (
    create_coding_agent,
    build_subagents,
    get_agent_run_config,
)
from deep_code.agents.registry import (
    SubAgentSpec,
    get_subagent_specs,
    get_subagent_names,
    get_subagent_spec,
    render_subagent_catalog,
)
from deep_code.agents.collaboration import (
    ReviewFinding,
    ReviewReport,
    FixReport,
    TestReport,
    CommitReport,
    render_collaboration_playbook,
)

__all__ = [
    "create_coding_agent", "build_subagents", "get_agent_run_config",
    "SubAgentSpec", "get_subagent_specs", "get_subagent_names", "get_subagent_spec",
    "render_subagent_catalog",
    "ReviewFinding", "ReviewReport", "FixReport", "TestReport", "CommitReport",
    "render_collaboration_playbook",
]
