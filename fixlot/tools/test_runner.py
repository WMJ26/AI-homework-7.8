import subprocess
from fixlot.tools.registry import ActionResult, Tool, ToolRegistry


def run_tests(params: dict) -> ActionResult:
    work_dir = params.get("work_dir", ".")
    test_command = params.get("test_command", "pytest")

    try:
        proc = subprocess.run(
            f"{test_command} -v",
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=work_dir,
        )
        output = proc.stdout
        if proc.stderr:
            output += "\n" + proc.stderr

        return ActionResult(
            success=(proc.returncode == 0),
            output=output.strip(),
            error=None if proc.returncode == 0 else f"Tests failed with exit code {proc.returncode}",
        )
    except subprocess.TimeoutExpired:
        return ActionResult(
            success=False,
            output="",
            error="Test run timed out after 120s",
        )
    except FileNotFoundError:
        return ActionResult(
            success=False,
            output="",
            error=f"Test command not found: {test_command}",
        )
    except Exception as e:
        return ActionResult(
            success=False,
            output="",
            error=f"Test execution error: {e}",
        )


def create_test_runner_tools(registry: ToolRegistry):
    registry.register(Tool(
        name="run_tests",
        description="Run the project's test suite and return results.",
        parameters_schema={
            "work_dir": {"type": "string", "description": "Working directory to run tests in"},
            "test_command": {"type": "string", "description": "Test command (default: pytest)"},
        },
        handler=run_tests,
    ))