from __future__ import annotations

from deep_code.collaboration import CommitReport, ReviewReport
from deep_code.subagents import (
    build_subagents,
    get_subagent_names,
    get_subagent_specs,
    render_subagent_catalog,
)


def test_registry_includes_test_writer_and_unique_names() -> None:
    specs = get_subagent_specs()
    names = [spec.name for spec in specs]

    assert len(specs) == 6
    assert len(names) == len(set(names))
    assert "test-writer" in names
    assert "git-committer" in names


def test_build_subagents_uses_registry_order() -> None:
    model = object()

    subagents = build_subagents(model)

    assert [subagent["name"] for subagent in subagents] == get_subagent_names()


def test_build_subagents_propagates_structured_response_formats() -> None:
    model = object()

    subagents = {subagent["name"]: subagent for subagent in build_subagents(model)}

    assert subagents["code-reviewer"]["response_format"] is ReviewReport
    assert subagents["git-committer"]["response_format"] is CommitReport


def test_render_subagent_catalog_mentions_test_writer() -> None:
    catalog = render_subagent_catalog()

    assert "test-writer" in catalog
    assert "git-committer" in catalog
    assert "test" in catalog.lower()
