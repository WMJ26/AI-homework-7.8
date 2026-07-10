import os
import tempfile
import pytest
from fixlot.tools.test_runner import run_tests, create_test_runner_tools
from fixlot.tools.registry import ToolRegistry


class TestRunTests:
    def test_runs_pytest_in_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_sample.py")
            with open(test_file, "w") as f:
                f.write("""
def test_pass():
    assert True

def test_fail():
    assert False
""")

            result = run_tests({"work_dir": tmpdir})
            assert result.success is False
            assert "passed" in result.output.lower() or "failed" in result.output.lower()

    def test_all_passing_tests(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_sample.py")
            with open(test_file, "w") as f:
                f.write("""
def test_pass1():
    assert True

def test_pass2():
    assert 1 + 1 == 2
""")

            result = run_tests({"work_dir": tmpdir})
            assert result.success is True

    def test_uses_default_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_tests({"work_dir": tmpdir})
            assert "no tests" in result.output.lower() or "collected" in result.output.lower() or "error" in result.output.lower()


class TestTestRunnerRegistration:
    def test_registers_run_tests(self):
        registry = ToolRegistry()
        create_test_runner_tools(registry)
        tools = registry.list_tools()
        assert "run_tests" in tools