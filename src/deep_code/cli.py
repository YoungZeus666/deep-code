"""Interactive CLI for Deep Code."""

from __future__ import annotations

import sys
from pathlib import Path

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from deep_code.agents import create_coding_agent
from deep_code.config import AppConfig, load_config
from deep_code.i18n import SUPPORTED_LANGUAGES, set_language, t

SKILL_DESC_MAX_LEN = 200


def print_welcome(console: Console, config: AppConfig) -> None:
    """Print the welcome banner with model and workspace info."""
    console.print(
        Panel(
            t(
                "welcome_body",
                provider=config.provider,
                model=config.model_name,
                workspace=config.workspace,
            ),
            title=t("welcome_title"),
            border_style="blue",
        )
    )
    console.print()


def handle_slash_command(command: str, config: AppConfig, console: Console) -> bool:
    """Handle CLI meta-commands. Returns True if handled."""
    cmd = command.strip().lower()

    if cmd in ("/quit", "/exit"):
        console.print(f"[dim]{t('goodbye')}[/dim]")
        raise SystemExit(0)

    if cmd == "/help":
        console.print(Markdown(t("help_text")))
        return True

    if cmd == "/model":
        console.print(t("current_model", model=f"{config.provider}:{config.model_name}"))
        return True

    if cmd == "/workspace":
        console.print(t("current_workspace", workspace=str(config.workspace)))
        return True

    if cmd == "/clear":
        return True  # Caller handles clearing messages

    console.print(t("unknown_command", command=command))
    return True


def stream_response(agent, messages: list, console: Console) -> list:
    """Stream an agent response with rich rendering.

    Uses LangGraph message streaming to show tokens as they arrive.
    Returns updated message history.
    """
    input_state = {"messages": messages}
    accumulated_text = ""
    tool_calls_shown: set[str] = set()

    try:
        for chunk, metadata in agent.stream(input_state, stream_mode="messages"):
            if isinstance(chunk, AIMessageChunk):
                # Accumulate text content
                if chunk.content:
                    text = ""
                    if isinstance(chunk.content, str):
                        text = chunk.content
                    elif isinstance(chunk.content, list):
                        for block in chunk.content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text += block.get("text", "")
                    if text:
                        accumulated_text += text
                        console.print(text, end="", highlight=False)

                # Show tool calls (deduplicated)
                if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                    for tc in chunk.tool_call_chunks:
                        tc_name = tc.get("name", "")
                        tc_id = tc.get("id", "")
                        if tc_name and tc_id not in tool_calls_shown:
                            tool_calls_shown.add(tc_id)
                            console.print(
                                f"\n[dim cyan]> Tool: {tc_name}[/dim cyan]",
                                highlight=False,
                            )

    except Exception as e:
        console.print(t("response_error", error=str(e)))

    if accumulated_text:
        console.print()
        messages.append(AIMessage(content=accumulated_text))

    return messages


def _handle_language_command(
    user_input: str,
    config: AppConfig,
    console: Console,
) -> tuple[bool, object | None]:
    """Handle /language command. Returns (handled, new_agent_or_None)."""
    parts = user_input.strip().split(maxsplit=1)

    if len(parts) == 1:
        # No argument: show current language
        lang = config.language
        name = SUPPORTED_LANGUAGES[lang]
        console.print(f"[cyan]{t('current_language', lang=lang, name=name)}[/cyan]")
        return True, None

    lang_code = parts[1].strip().lower()
    if lang_code not in SUPPORTED_LANGUAGES:
        supported = ", ".join(f"{k} ({v})" for k, v in SUPPORTED_LANGUAGES.items())
        console.print(t("unsupported_language", lang=lang_code, supported=supported))
        return True, None

    # Switch language
    config.language = lang_code
    set_language(lang_code)
    name = SUPPORTED_LANGUAGES[lang_code]
    console.print(f"[green]{t('language_switched', lang=lang_code, name=name)}[/green]")

    # Recreate agent with updated system prompt
    console.print(f"[dim]{t('loading_agent')}[/dim]")
    try:
        agent = create_coding_agent(config)
        console.print(f"[dim]{t('agent_ready')}[/dim]")
        return True, agent
    except Exception as e:
        console.print(t("agent_create_failed", error=str(e)))
        return True, None


def main() -> None:
    """Main entry point for the CLI application.

    Subcommands:
        init [path]  — Generate AGENTS.md and .agents/ for a project.
        (no args)    — Start the interactive coding assistant.
    """
    # Route subcommands before loading the full agent config
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        from deep_code.init import run_init

        target = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        run_init(target)
        return

    console = Console()

    try:
        config = load_config()
    except SystemExit:
        return

    # Synchronize i18n module with config
    set_language(config.language)

    print_welcome(console, config)

    # Let user confirm or change the workspace directory
    console.print(t("workspace_display", workspace=str(config.workspace)))
    try:
        answer = console.input(t("workspace_prompt")).strip()
    except (KeyboardInterrupt, EOFError):
        console.print(f"\n[dim]{t('goodbye')}[/dim]")
        return

    if answer.lower() in ("n", "no"):
        console.print(f"[dim]{t('cancelled')}[/dim]")
        return
    elif answer and answer.lower() not in ("y", "yes", ""):
        new_path = Path(answer).expanduser().resolve()
        if not new_path.is_dir():
            console.print(t("dir_not_exist", path=str(new_path)))
            return
        config.workspace = new_path
        console.print(t("workspace_changed", workspace=str(config.workspace)))

    # Remind user to init if AGENTS.md is missing
    if not (config.workspace / "AGENTS.md").is_file():
        console.print(f"[yellow]{t('init_reminder')}[/yellow]")

    console.print(f"[dim]{t('loading_agent')}[/dim]")
    try:
        agent = create_coding_agent(config)
    except Exception as e:
        console.print(t("agent_create_failed", error=str(e)))
        return

    # Report what was loaded
    agents_md = config.workspace / "AGENTS.md"
    if agents_md.is_file():
        console.print(t("loaded_agents_md"))

    skill_info: list[tuple[str, str]] = []  # (name, description)
    for sdir in (config.workspace / "skills", config.workspace / ".agents" / "skills"):
        if sdir.is_dir():
            for entry in sorted(sdir.iterdir()):
                skill_md = entry / "SKILL.md" if entry.is_dir() else None
                if not skill_md or not skill_md.is_file():
                    continue
                desc = ""
                try:
                    text = skill_md.read_text(encoding="utf-8", errors="replace")
                    if text.startswith("---"):
                        end = text.find("---", 3)
                        if end != -1:
                            for line in text[3:end].splitlines():
                                if line.strip().startswith("description:"):
                                    desc = line.split(":", 1)[1].strip()
                                    break
                except OSError:
                    pass
                # Truncate to first line
                first_line = desc.split("\n")[0]
                if len(first_line) > SKILL_DESC_MAX_LEN:
                    first_line = first_line[:SKILL_DESC_MAX_LEN - 3] + "..."
                skill_info.append((entry.name, first_line))

    console.print(t("loaded_skills", count=len(skill_info)))
    for name, desc in skill_info:
        if desc:
            console.print(f"  [dim]- {name}: {desc}[/dim]")
        else:
            console.print(f"  [dim]- {name}[/dim]")

    console.print(f"[dim]{t('agent_ready')}[/dim]\n")

    messages: list = []

    while True:
        try:
            user_input = console.input(f"[bold green]{t('input_prompt')}[/bold green]")
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[dim]{t('goodbye')}[/dim]")
            break

        if not user_input.strip():
            continue

        if user_input.strip().startswith("/"):
            cmd_lower = user_input.strip().lower()

            if cmd_lower == "/clear":
                messages.clear()
                console.print(f"[dim]{t('conversation_cleared')}[/dim]")
                continue

            if cmd_lower.startswith("/language"):
                handled, new_agent = _handle_language_command(
                    user_input.strip(), config, console
                )
                if new_agent is not None:
                    agent = new_agent
                if handled:
                    continue

            if cmd_lower == "/init":
                from deep_code.init import run_init
                run_init(config.workspace, interactive=False)
                continue

            if handle_slash_command(user_input.strip(), config, console):
                continue

        messages.append(HumanMessage(content=user_input))
        console.print()
        messages = stream_response(agent, messages, console)
        console.print()
