"""Interactive init command: generate AGENTS.md and .agents/ directory for a project."""

from __future__ import annotations

import json
import os
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt

from deep_code._detection_maps import (
    _EXT_TO_LANG,
    _FRAMEWORK_MARKERS,
    _SKIP_DIRS,
    _SKIP_FILES,
    _MAX_TREE_FILES,
    _MAX_READ_SIZE,
)

# ---------------------------------------------------------------------------
# Scanning helpers
# ---------------------------------------------------------------------------

def _collect_tree(root: Path) -> list[str]:
    """Collect relative file paths under *root*, skipping hidden/build dirs."""
    result: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in _SKIP_DIRS and not d.startswith(".")
        )
        for fname in sorted(filenames):
            if fname in _SKIP_FILES or fname.startswith("."):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fname), root)
            result.append(rel)
            if len(result) >= _MAX_TREE_FILES:
                return result
    return result


def _detect_languages(files: list[str]) -> list[str]:
    """Detect languages from file extensions."""
    found: list[str] = []
    seen: set[str] = set()
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        lang = _EXT_TO_LANG.get(ext)
        if lang and lang not in seen:
            found.append(lang)
            seen.add(lang)
    return found


def _detect_frameworks(root: Path) -> list[str]:
    """Detect frameworks/tools by checking for known marker files."""
    found: list[str] = []
    seen: set[str] = set()
    for marker, framework in _FRAMEWORK_MARKERS:
        if (root / marker).exists() and framework not in seen:
            found.append(framework)
            seen.add(framework)
    return found


def _read_safe(path: Path) -> str | None:
    """Read a text file, returning None on failure or if too large."""
    try:
        if path.stat().st_size > _MAX_READ_SIZE:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return None


def _find_readme(root: Path) -> str | None:
    """Return README content if present."""
    for name in ("README.md", "README.rst", "README.txt", "README"):
        p = root / name
        if p.is_file():
            return _read_safe(p)
    return None


def _extract_brief(readme: str) -> str | None:
    """Extract the first meaningful paragraph from README."""
    lines: list[str] = []
    past_title = False
    for line in readme.strip().splitlines():
        stripped = line.strip()
        if not past_title:
            if stripped.startswith("#") or not stripped:
                continue
            past_title = True
        if past_title:
            if stripped.startswith("#"):
                break
            lines.append(stripped)
            if len(lines) >= 5:
                break
    return " ".join(lines) if lines else None


def _get_entry_points(root: Path, files: list[str]) -> list[str]:
    """Identify likely entry point files."""
    candidates = [
        "main.py", "app.py", "manage.py", "cli.py",
        "src/main.py", "src/app.py", "src/cli.py",
        "__main__.py",
        "index.js", "index.ts", "src/index.js", "src/index.ts",
        "main.go", "cmd/main.go",
        "src/main.rs", "src/lib.rs",
    ]
    file_set = set(files)
    entry = [c for c in candidates if c in file_set]

    # Check pyproject.toml for [project.scripts]
    content = _read_safe(root / "pyproject.toml")
    if content and "[project.scripts]" in content:
        in_section = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "[project.scripts]":
                in_section = True
                continue
            if in_section:
                if stripped.startswith("["):
                    break
                if "=" in stripped and not stripped.startswith("#"):
                    entry.append(f"(script) {stripped}")
    return entry


def _identify_key_files(files: list[str]) -> list[tuple[str, str]]:
    """Identify key files and provide short descriptions."""
    key_map: list[tuple[str, str]] = [
        ("pyproject.toml", "Python project configuration and dependencies"),
        ("setup.py", "Python package setup"),
        ("package.json", "Node.js project configuration and dependencies"),
        ("Cargo.toml", "Rust project configuration and dependencies"),
        ("go.mod", "Go module definition and dependencies"),
        ("pom.xml", "Maven project configuration"),
        ("Makefile", "Build commands"),
        ("Dockerfile", "Container build definition"),
        ("docker-compose.yml", "Multi-container Docker configuration"),
        ("docker-compose.yaml", "Multi-container Docker configuration"),
        (".env.example", "Environment variables template"),
        ("README.md", "Project documentation"),
    ]
    file_set = set(files)
    return [(n, d) for n, d in key_map if n in file_set]


def _detect_dev_commands(root: Path) -> list[tuple[str, str]]:
    """Detect common development commands from project config files."""
    commands: list[tuple[str, str]] = []

    # Python
    pyproject_text = _read_safe(root / "pyproject.toml") or ""
    if pyproject_text:
        if "pytest" in pyproject_text or (root / "tests").is_dir():
            commands.append(("Test", "pytest"))
        if "ruff" in pyproject_text:
            commands.append(("Lint", "ruff check ."))
        if "hatchling" in pyproject_text:
            commands.append(("Build", "hatch build"))

    # Node
    pkg_path = root / "package.json"
    if pkg_path.is_file():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            for key in ("dev", "start", "build", "test", "lint"):
                if key in pkg.get("scripts", {}):
                    commands.append((key.capitalize(), f"npm run {key}"))
        except (json.JSONDecodeError, OSError):
            pass

    # Go
    if (root / "go.mod").is_file():
        commands.append(("Test", "go test ./..."))
        commands.append(("Build", "go build ./..."))

    # Rust
    if (root / "Cargo.toml").is_file():
        commands.append(("Test", "cargo test"))
        commands.append(("Build", "cargo build"))

    # Makefile
    if (root / "Makefile").is_file():
        commands.append(("Make", "make"))

    return commands


# ---------------------------------------------------------------------------
# AGENTS.md content builders
# ---------------------------------------------------------------------------

def _collect_project_info(root: Path) -> dict:
    """Auto-detect project information."""
    files = _collect_tree(root)
    truncated = len(files) >= _MAX_TREE_FILES

    languages = _detect_languages(files)
    frameworks = _detect_frameworks(root)
    entry_points = _get_entry_points(root, files)
    dev_cmds = _detect_dev_commands(root)
    readme_text = _find_readme(root)

    brief = None
    if readme_text:
        brief = _extract_brief(readme_text)

    return {
        "languages": languages,
        "frameworks": frameworks,
        "entry_points": entry_points,
        "dev_commands": dev_cmds,
        "description": brief,
        "files": files,
        "truncated": truncated,
    }


def generate_agents_md(info: dict) -> str:
    """Build AGENTS.md content from a project info dict."""
    sections: list[str] = []

    sections.append("# AGENTS.md\n")
    sections.append(
        "> This file helps AI agents understand this project. "
        "Auto-generated by `deep-code init`.\n"
    )

    # Overview
    sections.append("## Project Overview\n")
    if info.get("description"):
        sections.append(info["description"] + "\n")

    # Tech stack
    if info.get("languages") or info.get("frameworks"):
        sections.append("## Tech Stack\n")
        if info.get("languages"):
            sections.append(f"**Languages:** {', '.join(info['languages'])}")
        if info.get("frameworks"):
            sections.append(f"**Frameworks / Tools:** {', '.join(info['frameworks'])}")
        sections.append("")

    # Entry points
    if info.get("entry_points"):
        sections.append("## Entry Points\n")
        for ep in info["entry_points"]:
            sections.append(f"- `{ep}`")
        sections.append("")

    # Directory structure
    files = info.get("files", [])
    truncated = info.get("truncated", False)
    tree_text = "\n".join(f"- {f}" for f in files)
    if truncated:
        tree_text += f"\n... (truncated at {_MAX_TREE_FILES} files)"
    sections.append("## Directory Structure\n")
    sections.append(f"```\n{tree_text}\n```\n")

    # Key files
    key_files = _identify_key_files(files)
    if key_files:
        sections.append("## Key Files\n")
        for name, desc in key_files:
            sections.append(f"- `{name}` — {desc}")
        sections.append("")

    # Dev commands
    if info.get("dev_commands"):
        sections.append("## Development\n")
        for label, cmd in info["dev_commands"]:
            sections.append(f"- **{label}**: `{cmd}`")
        sections.append("")

    # Agent instructions
    sections.append("## Agent Instructions\n")
    sections.append("- Read this file before making changes to understand the project layout.")
    sections.append("- Check `.agents/` directory for additional context files.")
    sections.append("- Follow existing code conventions and patterns.")
    sections.append("- Run tests after making changes when a test suite exists.\n")

    return "\n".join(sections)


def generate_empty_agents_md() -> str:
    """Generate a minimal AGENTS.md for an empty project."""
    return """\
# AGENTS.md

> This file helps AI agents understand this project.
> Generated by `deep-code init`.

## Project Overview

(Describe your project here.)

## Tech Stack

(List languages, frameworks, and tools.)

## Directory Structure

(Empty project — structure will be filled in as files are added.)

## Agent Instructions

- Read this file before making changes to understand the project layout.
- Check `.agents/` directory for additional context files.
- Follow existing code conventions and patterns.
- Run tests after making changes when a test suite exists.
"""


# ---------------------------------------------------------------------------
# Init command entry point
# ---------------------------------------------------------------------------

def run_init(target_dir: Path | None = None, interactive: bool = True) -> bool:
    """Run the init command: generate AGENTS.md and .agents/ directory.

    Args:
        target_dir: Directory to initialize. Defaults to cwd.
        interactive: If True, show detected info and let user customize.
                     If False, auto-detect and generate without prompts.
    Returns:
        True if AGENTS.md was generated/updated, False if skipped.
    """
    console = Console()
    root = (target_dir or Path.cwd()).resolve()

    if not root.is_dir():
        console.print(f"[red]Error: {root} is not a directory.[/red]")
        raise SystemExit(1)

    console.print(f"Initializing project at: [cyan]{root}[/cyan]")

    agents_md_path = root / "AGENTS.md"
    agents_dir = root / ".agents"

    # Ask before overwriting (only in interactive mode)
    if agents_md_path.exists():
        if interactive:
            if not Confirm.ask(
                "[cyan]AGENTS.md already exists.[/cyan] Overwrite?",
                default=False,
            ):
                console.print("[dim]Skipped AGENTS.md (kept existing).[/dim]")
                _ensure_agents_dir(agents_dir, console)
                return False
        else:
            console.print("[dim]AGENTS.md exists, regenerating...[/dim]")

    has_content = _has_project_content(root)

    # Auto-detect project info
    console.print("[dim]Scanning project...[/dim]")
    info = _collect_project_info(root)

    if not has_content:
        info["languages"] = []
        info["frameworks"] = []
        info["dev_commands"] = []

    # Auto mode: skip customization
    if not interactive:
        content = generate_agents_md(info)
        console.print("[green]Generated AGENTS.md.[/green]")
        agents_md_path.write_text(content, encoding="utf-8")
        console.print(f"  [dim]-> {agents_md_path}[/dim]")
        _ensure_agents_dir(agents_dir, console)
        console.print("[bold green]Done![/bold green] Your project is ready for AI agents.")
        return True

    # Interactive mode: show detected info and let user customize
    console.print()
    console.print("[bold]Detected project info:[/bold]")
    if info.get("languages"):
        console.print(f"  [dim]Languages:[/dim] {', '.join(info['languages'])}")
    else:
        console.print("  [dim]Languages:[/dim] (none detected)")
    if info.get("frameworks"):
        console.print(f"  [dim]Frameworks:[/dim] {', '.join(info['frameworks'])}")
    else:
        console.print("  [dim]Frameworks:[/dim] (none detected)")
    if info.get("description"):
        console.print(f"  [dim]Description:[/dim] {info['description'][:60]}...")
    if info.get("dev_commands"):
        console.print(f"  [dim]Dev commands:[/dim]")
        for label, cmd in info["dev_commands"]:
            console.print(f"    - {label}: {cmd}")

    console.print()
    if not Confirm.ask("[cyan]Modify detected info?[/cyan]", default=False):
        console.print("[dim]Using detected info as-is.[/dim]")
    else:
        console.print()

        # Languages
        langs_raw = Prompt.ask(
            "[cyan]Languages[/cyan] (comma-separated, e.g. Python, Go, TypeScript)",
            default=",".join(info.get("languages", [])) if info.get("languages") else "",
        )
        info["languages"] = [l.strip() for l in langs_raw.split(",") if l.strip()]

        # Frameworks
        fws_raw = Prompt.ask(
            "[cyan]Frameworks / Tools[/cyan] (comma-separated)",
            default=",".join(info.get("frameworks", [])) if info.get("frameworks") else "",
        )
        info["frameworks"] = [f.strip() for f in fws_raw.split(",") if f.strip()]

        # Description
        desc = Prompt.ask(
            "[cyan]Project description[/cyan] (one-line summary)",
            default=info.get("description") or "",
        )
        info["description"] = desc.strip() or None

        # Dev commands
        console.print("[dim]Dev commands (leave empty to skip):[/dim]")
        new_dev_cmds: list[tuple[str, str]] = []
        while True:
            label = Prompt.ask("  [cyan]Command name[/cyan] (e.g. Test, Build, Lint)", default="")
            if not label.strip():
                break
            cmd = Prompt.ask(f"  [cyan]Command for '{label}'[/cyan]")
            if cmd.strip():
                new_dev_cmds.append((label.strip(), cmd.strip()))
        if new_dev_cmds:
            info["dev_commands"] = new_dev_cmds

    content = generate_agents_md(info)
    console.print("[green]Generated AGENTS.md.[/green]")

    agents_md_path.write_text(content, encoding="utf-8")
    console.print(f"  [dim]-> {agents_md_path}[/dim]")

    _ensure_agents_dir(agents_dir, console)

    console.print()
    console.print("[bold green]Done![/bold green] Your project is ready for AI agents.")
    console.print("[dim]Edit AGENTS.md to add custom instructions for your project.[/dim]")
    return True


def _ensure_agents_dir(agents_dir: Path, console: Console) -> None:
    """Create .agents/ directory with a placeholder README if missing."""
    if agents_dir.is_dir():
        console.print(f"  [dim]-> {agents_dir}/ (already exists)[/dim]")
        return

    agents_dir.mkdir(exist_ok=True)
    (agents_dir / "skills").mkdir(exist_ok=True)
    (agents_dir / "README.md").write_text(
        "# .agents/\n\n"
        "This directory contains context files for AI agents.\n\n"
        "You can add files here to provide additional context:\n\n"
        "- `style-guide.md` -- Coding style and conventions\n"
        "- `architecture.md` -- System architecture notes\n"
        "- `api-reference.md` -- API documentation\n"
        "- `todo.md` -- Current tasks and priorities\n\n"
        "## skills/\n\n"
        "Place `.md` files in the `skills/` subdirectory to define custom skills.\n"
        "Each file is automatically loaded into the agent's system prompt at startup.\n\n"
        "Example `skills/deploy.md`:\n\n"
        "```\n"
        "# Deploy Skill\n\n"
        "When the user asks to deploy, run `make deploy` in the project root.\n"
        "Verify the deployment succeeded by checking the output for errors.\n"
        "```\n",
        encoding="utf-8",
    )
    console.print(f"  [dim]-> {agents_dir}/ (created)[/dim]")
    console.print(f"  [dim]-> {agents_dir}/skills/ (created)[/dim]")


def _has_project_content(root: Path) -> bool:
    """Check if root has meaningful project files (beyond config/hidden)."""
    for item in root.iterdir():
        name = item.name
        if name.startswith(".") or name in ("AGENTS.md", "LICENSE", "README.md"):
            continue
        if item.is_file() or item.is_dir():
            return True
    return False