from __future__ import annotations

from deep_code.collaboration import CommitReport, render_collaboration_playbook


def test_collaboration_playbook_mentions_parallel_pipeline_retry_and_commit_guard() -> None:
    playbook = render_collaboration_playbook()

    assert "parallel" in playbook.lower()
    assert "generate -> review -> fix -> test -> commit" in playbook
    assert "retry" in playbook.lower()
    assert "git status --porcelain" in playbook


def test_commit_report_supports_blocked_and_success_paths() -> None:
    blocked = CommitReport(
        summary="blocked",
        commit_created=False,
        blocked_reason="dirty tree",
    )
    success = CommitReport(
        summary="ok",
        commit_created=True,
        commit_sha="abc123",
        commit_message="feat: add collaboration",
    )

    assert blocked.blocked_reason == "dirty tree"
    assert success.commit_sha == "abc123"
