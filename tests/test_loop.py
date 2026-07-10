import pytest
from fixlot.core.llm import MockLLM
from fixlot.core.loop import AgentLoop, LoopConfig
from fixlot.tools.registry import ToolRegistry, Tool, ActionResult
from fixlot.guardrails.shell_guard import ShellGuard
from fixlot.guardrails.file_guard import FileGuard


def _make_registry():
    registry = ToolRegistry()

    def write_file(params):
        return ActionResult(success=True, output=f"Written to {params.get('path', '')}")

    def run_tests(params):
        return ActionResult(success=True, output="1 passed")

    registry.register(Tool(
        name="write_file",
        description="Write a file",
        parameters_schema={},
        handler=write_file,
    ))
    registry.register(Tool(
        name="run_tests",
        description="Run tests",
        parameters_schema={},
        handler=run_tests,
    ))
    return registry


class TestAgentLoop:
    def test_loop_completes_with_mock_llm_passing(self):
        mock_llm = MockLLM([
            '{"tool": "write_file", "params": {"path": "test.py", "content": "def add(a,b): return a+b"}}',
            '{"tool": "run_tests", "params": {}}',
        ])
        registry = _make_registry()
        loop = AgentLoop(
            llm=mock_llm,
            tool_registry=registry,
            config=LoopConfig(max_rounds=5, work_dir="/tmp/test"),
            shell_guard=ShellGuard(),
            file_guard=FileGuard("/tmp/test"),
        )

        result = loop.run("Implement add function")
        assert result["state"] in ("PASSED", "MAX_RETRIES")

    def test_loop_handles_guardrail_block(self):
        mock_llm = MockLLM([
            '{"tool": "run_command", "params": {"cmd": "rm -rf /"}}',
            '{"tool": "run_tests", "params": {}}',
        ])
        registry = ToolRegistry()
        registry.register(Tool(
            name="run_command",
            description="Run command",
            parameters_schema={"cmd": "string"},
            handler=lambda p: ActionResult(success=True, output="ok"),
        ))
        registry.register(Tool(
            name="run_tests",
            description="Run tests",
            parameters_schema={},
            handler=lambda p: ActionResult(success=True, output="1 passed"),
        ))

        loop = AgentLoop(
            llm=mock_llm,
            tool_registry=registry,
            config=LoopConfig(max_rounds=5, work_dir="/tmp/test"),
            shell_guard=ShellGuard(),
            file_guard=FileGuard("/tmp/test"),
        )

        result = loop.run("Do something")
        assert result["state"] in ("PASSED", "MAX_RETRIES", "ERROR")

    def test_loop_stops_at_max_rounds(self):
        responses = ['{"tool": "run_tests", "params": {}}'] * 10
        mock_llm = MockLLM(responses)
        registry = _make_registry()
        loop = AgentLoop(
            llm=mock_llm,
            tool_registry=registry,
            config=LoopConfig(max_rounds=3, work_dir="/tmp/test"),
            shell_guard=ShellGuard(),
            file_guard=FileGuard("/tmp/test"),
        )

        result = loop.run("Task")
        assert result["total_rounds"] <= 3

    def test_loop_handles_invalid_json(self):
        mock_llm = MockLLM([
            "not valid json at all",
            '{"tool": "run_tests", "params": {}}',
        ])
        registry = _make_registry()
        loop = AgentLoop(
            llm=mock_llm,
            tool_registry=registry,
            config=LoopConfig(max_rounds=5, work_dir="/tmp/test"),
            shell_guard=ShellGuard(),
            file_guard=FileGuard("/tmp/test"),
        )

        result = loop.run("Task")
        assert result["total_rounds"] >= 1

    def test_loop_handles_missing_tool_key(self):
        mock_llm = MockLLM([
            '{"params": {}}',
            '{"tool": "run_tests", "params": {}}',
        ])
        registry = _make_registry()
        loop = AgentLoop(
            llm=mock_llm,
            tool_registry=registry,
            config=LoopConfig(max_rounds=5, work_dir="/tmp/test"),
            shell_guard=ShellGuard(),
            file_guard=FileGuard("/tmp/test"),
        )

        result = loop.run("Task")
        assert result["total_rounds"] >= 1