import subprocess
import time
from fixlot.tools.registry import ActionResult, Tool, ToolRegistry


def run_command(params: dict) -> ActionResult:
    command = params.get("cmd", params.get("command", ""))
    timeout = params.get("timeout", 60)

    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = proc.stdout
        if proc.stderr:
            output += proc.stderr

        return ActionResult(
            success=(proc.returncode == 0),
            output=output.strip(),
            error=None if proc.returncode == 0 else f"Command exited with code {proc.returncode}",
        )
    except subprocess.TimeoutExpired:
        return ActionResult(
            success=False,
            output="",
            error=f"Command timed out after {timeout}s",
        )
    except FileNotFoundError:
        return ActionResult(
            success=False,
            output="",
            error=f"Command not found: {command.split()[0] if command else command}",
        )
    except Exception as e:
        return ActionResult(
            success=False,
            output="",
            error=f"Command execution error: {e}",
        )


def create_shell_tools(registry: ToolRegistry):
    registry.register(Tool(
        name="run_command",
        description="Execute a shell command and return its output.",
        parameters_schema={
            "cmd": {"type": "string", "description": "The shell command to execute"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"},
        },
        handler=run_command,
    ))