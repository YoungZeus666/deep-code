"""Init command: generate AGENTS.md and .agents/ directory for a project."""

from __future__ import annotations

import json
import os
from pathlib import Path

from rich.console import Console

# ---------------------------------------------------------------------------
# Language / framework detection
# ---------------------------------------------------------------------------

# (extension, language_name)
_EXT_TO_LANG: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".jsx": "JavaScript (React)",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".dart": "Dart",
    ".lua": "Lua",
    ".scala": "Scala",
    ".zig": "Zig",
    ".ex": "Elixir",
    ".exs": "Elixir",
}

# (marker_file_or_dir, framework_name)
_FRAMEWORK_MARKERS: list[tuple[str, str]] = [
    ("pyproject.toml", "Python (pyproject)"),
    ("setup.py", "Python (setuptools)"),
    ("requirements.txt", "Python (pip)"),
    ("Pipfile", "Python (pipenv)"),
    ("poetry.lock", "Python (poetry)"),
    ("manage.py", "Django"),
    ("package.json", "Node.js"),
    ("tsconfig.json", "TypeScript"),
    ("next.config.js", "Next.js"),
    ("next.config.ts", "Next.js"),
    ("next.config.mjs", "Next.js"),
    ("nuxt.config.ts", "Nuxt.js"),
    ("vite.config.ts", "Vite"),
    ("vite.config.js", "Vite"),
    ("webpack.config.js", "Webpack"),
    ("angular.json", "Angular"),
    ("vue.config.js", "Vue"),
    ("svelte.config.js", "Svelte"),
    ("Cargo.toml", "Rust (Cargo)"),
    ("go.mod", "Go modules"),
    ("pom.xml", "Maven (Java)"),
    ("build.gradle", "Gradle"),
    ("build.gradle.kts", "Gradle (Kotlin)"),
    ("Gemfile", "Ruby (Bundler)"),
    ("composer.json", "PHP (Composer)"),
    ("CMakeLists.txt", "CMake"),
    ("Makefile", "Make"),
    ("Dockerfile", "Docker"),
    ("docker-compose.yml", "Docker Compose"),
    ("docker-compose.yaml", "Docker Compose"),
    (".github/workflows", "GitHub Actions"),
    ("pubspec.yaml", "Flutter/Dart"),
    ("Package.swift", "Swift Package Manager"),
]

# Directories to skip when scanning
_SKIP_DIRS: set[str] = {
    ".git", ".svn", ".hg",
    "node_modules", "__pycache__", ".ruff_cache", ".mypy_cache", ".pytest_cache",
    ".tox", ".venv", "venv", "env",
    "dist", "build", "target", "out",
    ".next", ".nuxt",
    ".agents",
}

_SKIP_FILES: set[str] = {
    ".DS_Store", "Thumbs.db",
}

# Limits
_MAX_TREE_FILES = 200
_MAX_READ_SIZE = 8192


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

def generate_agents_md(root: Path) -> str:
    """Scan a project directory and generate AGENTS.md content."""
    files = _collect_tree(root)
    truncated = len(files) >= _MAX_TREE_FILES

    languages = _detect_languages(files)
    frameworks = _detect_frameworks(root)
    entry_points = _get_entry_points(root, files)
    readme_text = _find_readme(root)

    sections: list[str] = []

    sections.append("# AGENTS.md\n")
    sections.append(
        "> This file helps AI agents understand this project. "
        "Auto-generated by `deep-code init`.\n"
    )

    # Overview
    sections.append("## Project Overview\n")
    if readme_text:
        brief = _extract_brief(readme_text)
        if brief:
            sections.append(brief + "\n")

    # Tech stack
    if languages or frameworks:
        sections.append("## Tech Stack\n")
        if languages:
            sections.append(f"**Languages:** {', '.join(languages)}")
        if frameworks:
            sections.append(f"**Frameworks / Tools:** {', '.join(frameworks)}")
        sections.append("")

    # Entry points
    if entry_points:
        sections.append("## Entry Points\n")
        for ep in entry_points:
            sections.append(f"- `{ep}`")
        sections.append("")

    # Directory structure
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
    dev_cmds = _detect_dev_commands(root)
    if dev_cmds:
        sections.append("## Development\n")
        for label, cmd in dev_cmds:
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

def run_init(target_dir: Path | None = None) -> None:
    """Run the init command: generate AGENTS.md and .agents/ directory."""
    console = Console()
    root = (target_dir or Path.cwd()).resolve()

    if not root.is_dir():
        console.print(f"[red]Error: {root} is not a directory.[/red]")
        raise SystemExit(1)

    console.print(f"Initializing project at: [cyan]{root}[/cyan]")

    agents_md_path = root / "AGENTS.md"
    agents_dir = root / ".agents"

    # Ask before overwriting
    if agents_md_path.exists():
        try:
            answer = console.input(
                "AGENTS.md already exists. Overwrite? (y/[bold green]N[/bold green]): "
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Cancelled.[/dim]")
            return
        if answer not in ("y", "yes"):
            console.print("[dim]Skipped AGENTS.md (kept existing).[/dim]")
            _ensure_agents_dir(agents_dir, console)
            return

    # Decide: full scan or empty template
    has_content = _has_project_content(root)

    if has_content:
        console.print("[dim]Scanning project...[/dim]")
        content = generate_agents_md(root)
        console.print("[green]Generated AGENTS.md from project analysis.[/green]")
    else:
        content = generate_empty_agents_md()
        console.print("[green]Generated empty AGENTS.md template.[/green]")

    agents_md_path.write_text(content, encoding="utf-8")
    console.print(f"  [dim]-> {agents_md_path}[/dim]")

    _ensure_agents_dir(agents_dir, console)

    console.print()
    console.print("[bold green]Done![/bold green] Your project is ready for AI agents.")
    console.print("[dim]Edit AGENTS.md to add custom instructions for your project.[/dim]")


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
