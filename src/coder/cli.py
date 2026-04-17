"""Interactive CLI for AI Deep Coder."""

from __future__ import annotations

import sys
from pathlib import Path

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from coder.agents import create_coding_agent
from coder.config import AppConfig, load_config

HELP_TEXT = """\
**AI Deep Coder** - AI Programming Assistant

**Subcommands (run from shell):**
- `ai-deep-coder init [path]` — Initialize AGENTS.md and .agents/ for a project

**Interactive commands:**
- `/help`      — Show this help message
- `/model`     — Show current model
- `/workspace` — Show current workspace
- `/clear`     — Clear conversation history
- `/quit`      — Exit the application

**Capabilities:**
- Ask to **generate** code: "Write a Python function that..."
- Ask to **review** code: "Review the code in src/main.py"
- Ask to **explain** code: "What does the handle_request function do?"
- Ask to **fix bugs**: "This test is failing with IndexError..."
"""


def print_welcome(console: Console, config: AppConfig) -> None:
    """Print the welcome banner with model and workspace info."""
    console.print(
        Panel(
            f"[bold]AI Deep Coder[/bold] v0.1.0\n"
            f"Provider: [cyan]{config.provider}[/cyan]\n"
            f"Model: [cyan]{config.model_name}[/cyan]\n"
            f"Workspace: [cyan]{config.workspace}[/cyan]\n\n"
            f"[dim]Type /help for commands, /quit to exit.[/dim]",
            title="Welcome",
            border_style="blue",
        )
    )
    console.print()


def handle_slash_command(command: str, config: AppConfig, console: Console) -> bool:
    """Handle CLI meta-commands. Returns True if handled."""
    cmd = command.strip().lower()

    if cmd in ("/quit", "/exit"):
        console.print("[dim]Goodbye![/dim]")
        raise SystemExit(0)

    if cmd == "/help":
        console.print(Markdown(HELP_TEXT))
        return True

    if cmd == "/model":
        console.print(f"Current model: [cyan]{config.provider}:{config.model_name}[/cyan]")
        return True

    if cmd == "/workspace":
        console.print(f"Current workspace: [cyan]{config.workspace}[/cyan]")
        return True

    if cmd == "/clear":
        return True  # Caller handles clearing messages

    console.print(f"[yellow]Unknown command: {command}[/yellow]. Type /help for options.")
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
        console.print(f"\n[red]Error during response: {e}[/red]")

    if accumulated_text:
        console.print()
        messages.append(AIMessage(content=accumulated_text))

    return messages


def main() -> None:
    """Main entry point for the CLI application.

    Subcommands:
        init [path]  — Generate AGENTS.md and .agents/ for a project.
        (no args)    — Start the interactive coding assistant.
    """
    # Route subcommands before loading the full agent config
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        from coder.init import run_init

        target = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        run_init(target)
        return

    console = Console()

    try:
        config = load_config()
    except SystemExit:
        return

    print_welcome(console, config)

    # Let user confirm or change the workspace directory
    console.print(f"Workspace: [cyan]{config.workspace}[/cyan]")
    try:
        answer = console.input(
            "Use this directory as workspace? ([bold green]Y[/bold green]/n/path): "
        ).strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Goodbye![/dim]")
        return

    if answer.lower() in ("n", "no"):
        console.print("[dim]Cancelled.[/dim]")
        return
    elif answer and answer.lower() not in ("y", "yes", ""):
        from pathlib import Path

        new_path = Path(answer).expanduser().resolve()
        if not new_path.is_dir():
            console.print(f"[red]Directory does not exist: {new_path}[/red]")
            return
        config.workspace = new_path
        console.print(f"Workspace changed to: [cyan]{config.workspace}[/cyan]")

    console.print("[dim]Loading agent...[/dim]")
    try:
        agent = create_coding_agent(config)
    except Exception as e:
        console.print(f"[red]Failed to create agent: {e}[/red]")
        return
    console.print("[dim]Agent ready.[/dim]\n")

    messages: list = []

    while True:
        try:
            user_input = console.input("[bold green]You > [/bold green]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input.strip():
            continue

        if user_input.strip().startswith("/"):
            if user_input.strip().lower() == "/clear":
                messages.clear()
                console.print("[dim]Conversation cleared.[/dim]")
                continue
            if handle_slash_command(user_input.strip(), config, console):
                continue

        messages.append(HumanMessage(content=user_input))
        console.print()
        messages = stream_response(agent, messages, console)
        console.print()
