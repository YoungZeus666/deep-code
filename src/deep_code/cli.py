"""Interactive CLI for Deep Code."""

from __future__ import annotations

import sys
from pathlib import Path

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from prompt_toolkit.shortcuts import prompt as Prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from deep_code.agent_commands import (
    AgentCommandError,
    build_agent_routing_message,
    parse_agent_command,
)
from deep_code.agents import create_coding_agent
from deep_code.config import AppConfig, load_config, get_trusted_workspaces, add_trusted_workspace
from deep_code.i18n import SUPPORTED_LANGUAGES, set_language, t
from deep_code.session import list_sessions, load_session, save_session
from deep_code.plan_mode import run_plan_mode
from deep_code.subagents import get_subagent_names

SKILL_DESC_MAX_LEN = 200

SLASH_COMMANDS = [
    "/help",
    "/agent",
    "/model",
    "/workspace",
    "/language",
    "/clear",
    "/init",
    "/plan",
    "/quit",
]

_input_style = Style.from_dict({"prompt": "bold green"})
_slash_completer = WordCompleter(SLASH_COMMANDS)

_combined_style = Style.from_dict({
    "prompt": "bold #00d4aa",
    "completion-menu.completion": "bg:#1a1a2e #cdd6f4",
    "completion-menu.completion.current": "bg:#585b70 #cdd6f4",
    "completion-menu.meta": "bg:#313244 #a6adc8",
    "completion-menu.meta.current": "bg:#45475a #cdd6f4",
    "completion-menu.border": "bg:#1a1a2e",
    "scrollbar.background": "bg:#313244",
    "scrollbar.button": "bg:#45475a",
})


# ── Helpers ──────────────────────────────────────────────────────────

def _relative_time(iso_str: str) -> str:
    """Convert an ISO 8601 timestamp to a human-friendly relative string."""
    from datetime import datetime, timezone
    try:
        then = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - then
        total_secs = int(delta.total_seconds())
        if total_secs < 60:
            return "刚刚"
        if total_secs < 3600:
            return f"{total_secs // 60} 分钟前"
        if total_secs < 86400:
            return f"{total_secs // 3600} 小时前"
        return f"{total_secs // 86400} 天前"
    except (ValueError, OSError):
        return iso_str


def _check_trusted_workspace(config: AppConfig, console: Console) -> bool:
    """Prompt for workspace confirmation if not already trusted. Returns True if confirmed."""
    trusted = get_trusted_workspaces()
    if str(config.workspace.resolve()) in trusted:
        return True

    console.print(t("workspace_display", workspace=str(config.workspace)))
    try:
        answer = console.input(t("workspace_prompt")).strip()
    except (KeyboardInterrupt, EOFError):
        console.print(f"\n[dim]{t('goodbye')}[/dim]")
        raise SystemExit(0)

    if answer.lower() in ("n", "no"):
        console.print(f"[dim]{t('cancelled')}[/dim]")
        raise SystemExit(0)
    elif answer and answer.lower() not in ("y", "yes", ""):
        from pathlib import Path
        new_path = Path(answer).expanduser().resolve()
        if not new_path.is_dir():
            console.print(t("dir_not_exist", path=str(new_path)))
            raise SystemExit(0)
        config.workspace = new_path

    add_trusted_workspace(config.workspace)
    if answer and answer.lower() not in ("y", "yes", ""):
        console.print(t("workspace_changed", workspace=str(config.workspace)))
    return True


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


def _handle_mode_command(
    user_input: str,
    config: AppConfig,
    console: Console,
    agent_ref: list | None,
    current_mode_ref: list | None,
) -> tuple[bool, object | None, str | None]:
    """Handle /mode command. Returns (handled, new_agent_or_None, new_mode_or_None).

    agent_ref: list containing the current agent (mutated in place).
    current_mode_ref: list containing the current mode string (mutated in place).
    """
    parts = user_input.strip().split(maxsplit=1)

    if len(parts) == 1:
        # No argument: show current mode
        mode = current_mode_ref[0] if current_mode_ref else "agent"
        console.print(t("mode_current", mode=mode))
        console.print(f"[dim]{t('mode_available_modes')}[/dim]")
        return True, None, None

    arg = parts[1].strip().lower()
    if arg not in ("agent", "plan"):
        console.print(t("mode_invalid_arg", arg=arg))
        console.print(f"[dim]{t('mode_available_modes')}[/dim]")
        return True, None, None

    new_mode = arg
    if current_mode_ref is not None:
        current_mode_ref[0] = new_mode

    console.print(t("mode_switched", mode=new_mode))

    if new_mode == "plan":
        # Switch to plan mode - pass current agent for Step 3 execution
        from deep_code.plan_mode import run_plan_mode
        current_agent = agent_ref[0] if agent_ref else None
        run_plan_mode(config, console, agent=current_agent)
        # After plan mode exits, switch back to agent mode
        if current_mode_ref is not None:
            current_mode_ref[0] = "agent"
        console.print(t("mode_switched", mode="agent"))

    return True, None, None


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

    # Workspace trust check (skipped if already trusted)
    _check_trusted_workspace(config, console)

    # ── Session restore ─────────────────────────────────────────────
    recent = list_sessions(config.workspace, limit=3)
    messages: list = []
    if recent:
        console.print(t("recent_sessions"))
        for i, s in enumerate(recent, 1):
            console.print(
                t("session_option", n=i, summary=s.summary, time=_relative_time(s.created_at))
            )
        try:
            choice = console.input(t("restore_prompt")).strip()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[dim]{t('goodbye')}[/dim]")
            return
        if choice.isdigit() and 1 <= int(choice) <= len(recent):
            messages = load_session(config.workspace, recent[int(choice) - 1].session_id)
            console.print(t("session_restored"))
    # ── Init reminder + agent setup ──────────────────────────────────
    if not (config.workspace / "AGENTS.md").is_file():
        console.print(f"[yellow]{t('init_reminder')}[/yellow]")

    console.print(f"[dim]{t('loading_agent')}[/dim]")
    try:
        agent = create_coding_agent(config)
    except Exception as e:
        console.print(t("agent_create_failed", error=str(e)))
        return

    agents_md = config.workspace / "AGENTS.md"
    if agents_md.is_file():
        console.print(t("loaded_agents_md"))

    skill_info: list[tuple[str, str]] = []
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

    try:
        while True:
            console.print("[dim]─" * console.width)
            try:
                user_input = Prompt("> ", completer=_slash_completer, style=_combined_style)
            except (KeyboardInterrupt, EOFError):
                console.print(f"\n[dim]{t('goodbye')}[/dim]")
                break
            console.print("[dim]─" * console.width)

            if not user_input.strip():
                continue

            if user_input.strip().startswith("/"):
                cmd_lower = user_input.strip().lower()
                available_agents = get_subagent_names()

                if cmd_lower.startswith("/agent"):
                    try:
                        parsed = parse_agent_command(user_input.strip(), available_agents)
                    except AgentCommandError as error:
                        agents_text = ", ".join(available_agents)
                        if error.code == "missing_agent":
                            console.print(t("agent_usage", agents=agents_text))
                        elif error.code == "missing_task":
                            console.print(
                                t("agent_missing_task", agent=error.detail or "")
                            )
                            console.print(t("agent_available_list", agents=agents_text))
                        elif error.code == "unknown_agent":
                            console.print(
                                t("agent_unknown", agent=error.detail or "")
                            )
                            console.print(t("agent_available_list", agents=agents_text))
                        else:
                            console.print(t("agent_usage", agents=agents_text))
                        continue

                    user_input = build_agent_routing_message(
                        parsed.agent_name,
                        parsed.task,
                    )

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

                if cmd_lower.startswith("/mode"):
                    handled, new_agent, new_mode = _handle_mode_command(
                        user_input.strip(), config, console, [agent], None
                    )
                    if handled:
                        continue

                if handle_slash_command(user_input.strip(), config, console):
                    continue

            messages.append(HumanMessage(content=user_input))
            console.print()
            messages = stream_response(agent, messages, console)
            console.print()
    finally:
        if messages:
            try:
                session_id = save_session(
                    config.workspace, messages, config.language, config.max_sessions
                )
                console.print(t("session_saved"))
            except Exception as e:
                console.print(t("session_save_error", error=str(e)))
