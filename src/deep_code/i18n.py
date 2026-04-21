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
- `/quit`      — 退出应用

**功能:**
- **生成**代码: "写一个 Python 函数..."
- **审查**代码: "审查 src/main.py 的代码"
- **解释**代码: "handle_request 函数是做什么的？"
- **修复**缺陷: "这个测试报了 IndexError..."
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
        "input_prompt": "你 > ",
        "current_language": "当前语言: {lang} ({name})",
        "language_switched": "语言已切换至: {lang} ({name})",
        "unsupported_language": "[yellow]不支持的语言: {lang}。支持: {supported}[/yellow]",
        "init_reminder": "输入 /init 初始化项目，生成 AGENTS.md 和 .agents/ 目录",
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
- `/quit`      — Exit the application

**Capabilities:**
- Ask to **generate** code: "Write a Python function that..."
- Ask to **review** code: "Review the code in src/main.py"
- Ask to **explain** code: "What does the handle_request function do?"
- Ask to **fix bugs**: "This test is failing with IndexError..."
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
