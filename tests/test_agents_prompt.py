from __future__ import annotations

from deep_code.agents import _build_system_prompt


def test_system_prompt_includes_dynamic_subagent_catalog(tmp_path) -> None:
    prompt = _build_system_prompt(tmp_path, "en")

    assert "test-writer" in prompt
    assert "git-committer" in prompt
    assert "generate -> review -> fix -> test -> commit" in prompt
    assert "parallel" in prompt.lower()
    assert "four specialized subagents" not in prompt
