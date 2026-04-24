"""Internationalization support for Deep Code CLI."""

from __future__ import annotations

SUPPORTED_LANGUAGES: dict[str, str] = {
    "zh": "中文",
    "en": "English",
}

_current_lang: str = "zh"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "zh": {
        "help_text": """\
**Deep Code** - AI 编程助手

**子命令 (在 shell 中运行):**
- `deep-code init [path]` — 为项目初始化 AGENTS.md 和 .agents/ 目录

**交互命令:**
- `/help`      — 显示帮助信息
- `/model`     — 显示当前模型
- `/workspace` — 显示当前工作区
- `/language`  — 切换语言 (zh/en)
- `/clear`     — 清除对话历史
- `/init`      — 初始化项目 (生成 AGENTS.md)
- `/mode`      — 切换模式 (agent/plan)
- `/quit`      — 退出应用

**功能:**
- **生成**代码: "写一个 Python 函数..."
- **审查**代码: "审查 src/main.py 的代码"
- **解释**代码: "handle_request 函数是做什么的？"
- **修复**缺陷: "这个测试报了 IndexError..."
- **计划模式**: 输入 /mode plan 进入三步式编码
""",
        "welcome_title": "欢迎",
        "welcome_body": (
            "[bold]Deep Code[/bold] v0.1.0\n"
            "提供商: [cyan]{provider}[/cyan]\n"
            "模型: [cyan]{model}[/cyan]\n"
            "工作区: [cyan]{workspace}[/cyan]\n\n"
            "[dim]输入 /help 查看命令, /quit 退出。[/dim]"
        ),
        "goodbye": "再见！",
        "current_model": "当前模型: [cyan]{model}[/cyan]",
        "current_workspace": "当前工作区: [cyan]{workspace}[/cyan]",
        "unknown_command": "[yellow]未知命令: {command}[/yellow]。输入 /help 查看可用命令。",
        "workspace_display": "工作区: [cyan]{workspace}[/cyan]",
        "workspace_prompt": "使用此目录作为工作区？([bold green]Y[/bold green]/n/路径): ",
        "workspace_changed": "工作区已切换至: [cyan]{workspace}[/cyan]",
        "cancelled": "已取消。",
        "dir_not_exist": "[red]目录不存在: {path}[/red]",
        "loading_agent": "正在加载代理...",
        "agent_ready": "代理就绪。",
        "agent_create_failed": "[red]创建代理失败: {error}[/red]",
        "loaded_agents_md": "[green]已加载 AGENTS.md[/green]",
        "loaded_skills": "[green]已加载 {count} 个技能[/green]",
        "conversation_cleared": "对话已清除。",
        "response_error": "\n[red]响应出错: {error}[/red]",
        "input_prompt": "> ",
        "current_language": "当前语言: {lang} ({name})",
        "language_switched": "语言已切换至: {lang} ({name})",
        "unsupported_language": "[yellow]不支持的语言: {lang}。支持: {supported}[/yellow]",
        "init_reminder": "输入 /init 初始化项目，生成 AGENTS.md 和 .agents/ 目录",
        "recent_sessions": "最近的会话：",
        "session_option": "  [{n}] {summary}  ({time})",
        "restore_prompt": "恢复会话? 填写编号或按 Enter 跳过: ",
        "session_saved": "[green]会话已自动保存[/green]",
        "session_restored": "[green]已恢复会话[/green]",
        "session_save_error": "[red]保存会话失败: {error}[/red]",
        "session_restore_error": "[red]恢复会话失败: {error}[/red]",
        "plan_optimize_error": "[red]优化问题失败: {error}[/red]",
        "plan_regenerate_error": "[red]重新优化失败: {error}[/red]",
        "plan_generate_error": "[red]生成方案失败: {error}[/red]",
        "plan_regenerate_plan_error": "[red]重新生成方案失败: {error}[/red]",
        "plan_execute_error": "[red]执行方案失败: {error}[/red]",
        "plan_model_create_error": "[red]无法创建模型实例[/red]",
        # Plan mode
        "plan_mode_title": "📋 计划模式",
        "plan_mode_desc": "三步式编码：优化问题 → 确认方案 → 执行",
        "plan_step1_prompt": "\n[bold cyan]步骤 1/3: 优化问题[/bold cyan]\n",
        "plan_step1_streaming": "正在优化问题...",
        "plan_step2_prompt": "\n[bold cyan]步骤 2/3: 确认方案[/bold cyan]\n",
        "plan_step2_streaming": "正在生成方案...",
        "plan_step3_exec": "\n[bold cyan]步骤 3/3: 执行方案[/bold cyan]\n开始执行...\n",
        "plan_step3_exec_no_agent": "\n[bold cyan]步骤 3/3: 执行方案[/bold cyan]\n（无 agent，回退到文本模式）\n",
        "plan_confirm": "\n输入 [bold green]y/yes[/bold green] 确认，或输入修改意见：",
        "plan_cancel": "[yellow]已取消计划模式[/yellow]",
        "plan_restart": "[cyan]输入 /mode plan 重新开始[/cyan]",
        "plan_success": "[green]✅ 计划执行完成！[/green]",
        "plan_regenerating": "正在重新生成...",
        "plan_max_retries": "[yellow]已达最大重试次数，按 Enter 取消[/yellow]",
        "plan_mode_hint": "提示：使用 /mode plan 进入计划模式，可视化每个编码步骤",
        "mode_current": "当前模式: [cyan]{mode}[/cyan]",
        "mode_switched": "[green]已切换至 {mode} 模式[/green]",
        "mode_invalid_arg": "[yellow]无效参数: {arg}。可用: agent, plan[/yellow]",
        "mode_available_modes": "可用模式: [cyan]agent[/cyan] (默认), [cyan]plan[/cyan]",
        "plan_ask_question": "请描述你想要完成的任务或问题：",
    },
    "en": {
        "help_text": """\
**Deep Code** - AI Programming Assistant

**Subcommands (run from shell):**
- `deep-code init [path]` — Initialize AGENTS.md and .agents/ for a project

**Interactive commands:**
- `/help`      — Show this help message
- `/model`     — Show current model
- `/workspace` — Show current workspace
- `/language`  — Switch language (zh/en)
- `/clear`     — Clear conversation history
- `/init`      — Initialize project (generate AGENTS.md)
- `/mode`      — Switch mode (agent/plan)
- `/quit`      — Exit the application

**Capabilities:**
- Ask to **generate** code: "Write a Python function that..."
- Ask to **review** code: "Review the code in src/main.py"
- Ask to **explain** code: "What does the handle_request function do?"
- Ask to **fix bugs**: "This test is failing with IndexError..."
- Use **plan mode**: Type /mode plan for step-by-step coding
""",
        "welcome_title": "Welcome",
        "welcome_body": (
            "[bold]Deep Code[/bold] v0.1.0\n"
            "Provider: [cyan]{provider}[/cyan]\n"
            "Model: [cyan]{model}[/cyan]\n"
            "Workspace: [cyan]{workspace}[/cyan]\n\n"
            "[dim]Type /help for commands, /quit to exit.[/dim]"
        ),
        "goodbye": "Goodbye!",
        "current_model": "Current model: [cyan]{model}[/cyan]",
        "current_workspace": "Current workspace: [cyan]{workspace}[/cyan]",
        "unknown_command": "[yellow]Unknown command: {command}[/yellow]. Type /help for options.",
        "workspace_display": "Workspace: [cyan]{workspace}[/cyan]",
        "workspace_prompt": "Use this directory as workspace? ([bold green]Y[/bold green]/n/path): ",
        "workspace_changed": "Workspace changed to: [cyan]{workspace}[/cyan]",
        "cancelled": "Cancelled.",
        "dir_not_exist": "[red]Directory does not exist: {path}[/red]",
        "loading_agent": "Loading agent...",
        "agent_ready": "Agent ready.",
        "agent_create_failed": "[red]Failed to create agent: {error}[/red]",
        "loaded_agents_md": "[green]Loaded AGENTS.md[/green]",
        "loaded_skills": "[green]Loaded {count} skill(s)[/green]",
        "conversation_cleared": "Conversation cleared.",
        "response_error": "\n[red]Error during response: {error}[/red]",
        "input_prompt": "You > ",
        "current_language": "Current language: {lang} ({name})",
        "language_switched": "Language switched to: {lang} ({name})",
        "unsupported_language": "[yellow]Unsupported language: {lang}. Supported: {supported}[/yellow]",
        "init_reminder": "Type /init to initialize the project, generating AGENTS.md and .agents/",
        "recent_sessions": "Recent sessions:",
        "session_option": "  [{n}] {summary}  ({time} ago)",
        "restore_prompt": "Restore session? Enter number or press Enter to skip: ",
        "session_saved": "[green]Session auto-saved[/green]",
        "session_restored": "[green]Session restored[/green]",
        "session_save_error": "[red]Failed to save session: {error}[/red]",
        "session_restore_error": "[red]Failed to restore session: {error}[/red]",
        "plan_optimize_error": "[red]Failed to optimize question: {error}[/red]",
        "plan_regenerate_error": "[red]Failed to regenerate: {error}[/red]",
        "plan_generate_error": "[red]Failed to generate plan: {error}[/red]",
        "plan_regenerate_plan_error": "[red]Failed to regenerate plan: {error}[/red]",
        "plan_execute_error": "[red]Failed to execute plan: {error}[/red]",
        "plan_model_create_error": "[red]Failed to create model instance[/red]",
        "plan_mode_title": "📋 Plan Mode",
        "plan_mode_desc": "3-step coding: Optimize question → Confirm plan → Execute",
        "plan_step1_prompt": "\n[bold cyan]Step 1/3: Optimize Question[/bold cyan]\n",
        "plan_step1_streaming": "Optimizing...",
        "plan_step2_prompt": "\n[bold cyan]Step 2/3: Confirm Plan[/bold cyan]\n",
        "plan_step2_streaming": "Generating plan...",
        "plan_step3_exec": "\n[bold cyan]Step 3/3: Execute Plan[/bold cyan]\nStarting execution...\n",
        "plan_step3_exec_no_agent": "\n[bold cyan]Step 3/3: Execute Plan[/bold cyan]\n(No agent, text-only fallback)\n",
        "plan_confirm": "\nEnter [bold green]y/yes[/bold green] to confirm, or enter your feedback:",
        "plan_cancel": "[yellow]Plan mode cancelled[/yellow]",
        "plan_restart": "[cyan]Type /mode plan to restart[/cyan]",
        "plan_success": "[green]✅ Plan execution completed![/green]",
        "plan_regenerating": "Regenerating...",
        "plan_max_retries": "[yellow]Max retries reached, press Enter to cancel[/yellow]",
        "plan_mode_hint": "Tip: Use /mode plan to enter plan mode for visual step-by-step coding",
        "mode_current": "Current mode: [cyan]{mode}[/cyan]",
        "mode_switched": "[green]Switched to {mode} mode[/green]",
        "mode_invalid_arg": "[yellow]Invalid argument: {arg}. Available: agent, plan[/yellow]",
        "mode_available_modes": "Available modes: [cyan]agent[/cyan] (default), [cyan]plan[/cyan]",
        "plan_ask_question": "Describe the task or problem you want to accomplish:",
    },
}


def set_language(lang: str) -> None:
    """Set the current language."""
    global _current_lang
    _current_lang = lang


def get_language() -> str:
    """Get the current language code."""
    return _current_lang


def t(key: str, **kwargs: object) -> str:
    """Look up a translated string by key, with optional format arguments."""
    text = TRANSLATIONS.get(_current_lang, TRANSLATIONS["zh"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
