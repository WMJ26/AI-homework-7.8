import pytest
from fixlot.tools.shell import run_command, create_shell_tools
from fixlot.tools.registry import ToolRegistry


class TestRunCommand:
    def test_runs_echo_command(self):
        result = run_command({"cmd": "echo hello"})
        assert result.success is True
        assert "hello" in result.output
        assert result.error is None

    def test_runs_command_with_exit_code(self):
        result = run_command({"cmd": "python -c \"exit(0)\""})
        assert result.success is True

    def test_failed_command(self):
        result = run_command({"cmd": "python -c \"raise SystemExit(1)\""})
        assert result.success is False

    def test_command_not_found(self):
        result = run_command({"cmd": "nonexistent_command_xyz_123"})
        assert result.success is False

    def test_timeout_kills_process(self):
        result = run_command({"cmd": "python -c \"import time; time.sleep(10)\"", "timeout": 0.5})
        assert result.success is False
        error_lower = (result.error or "").lower()
        assert "timeout" in error_lower or "timed out" in error_lower

    def test_captures_stderr(self):
        result = run_command({"cmd": "python -c \"import sys; sys.stderr.write('oops'); raise SystemExit(1)\""})
        assert result.success is False
        assert "oops" in result.output


class TestShellToolsRegistration:
    def test_registers_run_command(self):
        registry = ToolRegistry()
        create_shell_tools(registry)
        tools = registry.list_tools()
        assert "run_command" in tools