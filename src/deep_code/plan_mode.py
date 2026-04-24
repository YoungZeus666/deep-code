"""Plan mode: interactive 3-step coding workflow.

Step 1: Optimize the user's question (streaming)
Step 2: Generate and confirm implementation plan (streaming)
Step 3: Execute the confirmed plan via deep agents agent (streaming)
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from rich.console import Console
from rich.panel import Panel

from deep_code.i18n import t

__all__ = ["run_plan_mode"]


# ── State ────────────────────────────────────────────────────────────────────

@dataclass
class PlanState:
    """Mutable state shared across the 3-step plan workflow."""
    optimized_question: str = ""
    plan_content: str = ""


# ── Model helpers ────────────────────────────────────────────────────────────

def _build_model(config) -> ChatOpenAI | None:
    """Build a ChatOpenAI model instance from config for plan mode."""
    if config.provider == "openai-like":
        return ChatOpenAI(
            model=config.model_name,
            base_url=config.base_url,
            api_key=config.api_key,
        )
    # Anthropic via langchain-anthropic
    try:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=config.model_name)
    except ImportError:
        return None


def _stream_model(
    model,
    messages: list,
    console: Console,
    title: str = "",
) -> str:
    """Stream a model response and return accumulated text."""
    accumulated = ""
    first_token = True

    try:
        for chunk in model.stream(messages):
            text = ""
            if hasattr(chunk, "content"):
                content = chunk.content
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text += block.get("text", "")
                elif isinstance(content, dict) and content.get("type") == "text":
                    text = content.get("text", "")

            if text:
                if first_token and title:
                    console.print(title)
                    first_token = False
                console.print(text, end="", highlight=False)
                accumulated += text
    except Exception as e:
        console.print(f"\n[red]{t('response_error', error=str(e))}[/red]")
        return ""

    console.print()
    return accumulated


# ── Confirmation helper ──────────────────────────────────────────────────────

def _confirm(
    console: Console,
    prompt_msg: str,
    messages: list,
    model,
    state_attr: str,
    state: PlanState,
    max_retries: int = 2,
) -> bool:
    """Ask user for confirmation, allow retries. Returns True if confirmed."""
    for _ in range(max_retries):
        console.print(prompt_msg)
        try:
            answer = console.input("> ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[dim]{t('plan_cancel')}[/dim]")
            return False

        if answer in ("y", "yes", ""):
            return True

        if not answer:
            console.print(f"[dim]{t('plan_cancel')}[/dim]")
            return False

        # User gave feedback — regenerate
        messages.append(HumanMessage(content=f"用户反馈：{answer}\n\n请根据反馈重新生成。"))
        console.print(f"\n[dim]{t('plan_regenerating')}[/dim]\n")

        accumulated = _stream_model(model, messages, console)
        if not accumulated:
            return False

        setattr(state, state_attr, accumulated)
        console.print()

    console.print(f"[dim]{t('plan_max_retries')}[/dim]")
    return False


# ── Step 1: Optimize question ─────────────────────────────────────────────────

def _step1_optimize(
    model,
    user_question: str,
    console: Console,
    state: PlanState,
) -> bool:
    """Step 1: Stream the optimized question and store in state. Returns True if confirmed."""
    console.print(t("plan_step1_prompt"))

    messages = [
        HumanMessage(
            content=(
                f"原始问题：{user_question}\n\n"
                "请优化这个问题，使其更清晰、更具体、更可执行。"
                "使用 markdown 格式输出优化后的问题。"
            )
        )
    ]

    accumulated = _stream_model(
        model, messages, console,
        title=f"[dim]{t('plan_step1_streaming')}[/dim]"
    )
    if not accumulated:
        return False

    state.optimized_question = accumulated
    console.print()

    return _confirm(console, t("plan_confirm"), messages, model, "optimized_question", state)


# ── Step 2: Generate plan ────────────────────────────────────────────────────

def _step2_plan(
    model,
    console: Console,
    state: PlanState,
) -> bool:
    """Step 2: Stream the implementation plan and store in state. Returns True if confirmed."""
    console.print(t("plan_step2_prompt"))

    messages = [
        HumanMessage(
            content=(
                f"已确认的问题：\n{state.optimized_question}\n\n"
                "请生成一个详细的实现方案，使用 markdown 格式，包括：\n"
                "1. 步骤列表\n2. 关键文件修改\n3. 代码示例\n4. 预期结果"
            )
        )
    ]

    accumulated = _stream_model(
        model, messages, console,
        title=f"[dim]{t('plan_step2_streaming')}[/dim]"
    )
    if not accumulated:
        return False

    state.plan_content = accumulated
    console.print()

    return _confirm(console, t("plan_confirm"), messages, model, "plan_content", state)


# ── Step 3: Execute via deep agents ──────────────────────────────────────────

def _stream_agent(agent, messages: list, console: Console) -> None:
    """Stream agent execution with rich tool call display."""
    input_state = {"messages": messages}
    tool_calls_shown: set[str] = set()

    try:
        for chunk, metadata in agent.stream(input_state, stream_mode="messages"):
            from langchain_core.messages import AIMessageChunk
            if isinstance(chunk, AIMessageChunk):
                if chunk.content:
                    text = ""
                    if isinstance(chunk.content, str):
                        text = chunk.content
                    elif isinstance(chunk.content, list):
                        for block in chunk.content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text += block.get("text", "")
                    if text:
                        console.print(text, end="", highlight=False)

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

    console.print()


def _step3_execute(
    agent,
    console: Console,
    state: PlanState,
) -> None:
    """Step 3: Execute the confirmed plan using deep agents agent (streaming)."""
    console.print(t("plan_step3_exec"))

    exec_prompt = (
        f"【严格执行以下方案】\n\n{state.plan_content}\n\n"
        "请使用文件系统工具和执行工具严格按方案执行每一步操作。"
        "完成每个步骤后报告结果。"
    )

    messages = [HumanMessage(content=exec_prompt)]
    _stream_agent(agent, messages, console)


# ── Main entry ───────────────────────────────────────────────────────────────

def run_plan_mode(
    config,
    console: Console,
    agent=None,
) -> None:
    """Run the interactive 3-step plan mode.

    Args:
        config: Application configuration
        console: Rich console for output
        agent: Optional deep agents instance for Step 3 execution.
              If None, Step 3 streams via the plan model only (text-only).
    """
    model = _build_model(config)
    if model is None:
        console.print(t("plan_model_create_error"))
        return

    state = PlanState()

    console.print(Panel(
        t("plan_mode_desc"),
        title=t("plan_mode_title"),
        border_style="cyan",
    ))
    console.print()

    # Ask for the task
    try:
        user_question = console.input(
            f"[bold cyan]{t('plan_ask_question')}[/bold cyan]\n> "
        ).strip()
    except (KeyboardInterrupt, EOFError):
        console.print(f"\n[dim]{t('goodbye')}[/dim]")
        return

    if not user_question:
        console.print(f"[dim]{t('plan_cancel')}[/dim]")
        return

    # Step 1: Optimize
    if not _step1_optimize(model, user_question, console, state):
        console.print(f"[dim]{t('plan_restart')}[/dim]")
        return

    # Step 2: Generate plan
    if not _step2_plan(model, console, state):
        console.print(f"[dim]{t('plan_restart')}[/dim]")
        return

    # Step 3: Execute
    if agent is not None:
        _step3_execute(agent, console, state)
    else:
        # Fallback: stream plan model response for execution
        console.print(t("plan_step3_exec_no_agent"))
        exec_messages = [
            HumanMessage(
                content=(
                    f"已确认的方案：\n{state.plan_content}\n\n"
                    "请严格按照方案执行，使用 markdown 格式报告每一步的执行结果。"
                )
            )
        ]
        _stream_model(model, exec_messages, console)

    console.print()
    console.print(t("plan_success"))
