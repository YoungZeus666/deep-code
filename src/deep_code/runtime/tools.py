"""Custom tools that extend the built-in Deep Agents toolkit.

Deep Agents already provides: ls, read_file, write_file, edit_file,
glob, grep, execute, write_todos, and task (subagent delegation).

Add your own tools here. They will be merged with the built-in tools.
"""

from __future__ import annotations


def get_custom_tools() -> list:
    """Return custom tools to add to the agent.

    These are merged with Deep Agents' built-in tools, not replacing them.
    By default returns an empty list. Add your own tools as needed.

    Example:
        from langchain_core.tools import tool

        @tool
        def run_tests(command: str = "pytest") -> str:
            \"\"\"Run the project test suite.\"\"\"
            import subprocess
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=120
            )
            return f"Exit code: {result.returncode}\\n{result.stdout}\\n{result.stderr}"

        def get_custom_tools():
            return [run_tests]
    """
    return []
