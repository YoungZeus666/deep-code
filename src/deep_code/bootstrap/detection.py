"""Detection constants for project scanning."""

from __future__ import annotations

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
