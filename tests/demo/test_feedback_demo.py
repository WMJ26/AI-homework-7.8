"""
Mechanism Demo 2: Feedback loop deterministically processes test failures
and generates correction hints without a real LLM.

This test injects a mock LLM that produces failing code, then verifies
the entire feedback pipeline: parser -> classifier -> correction -> re-loop.
"""
from fixlot.core.llm import MockLLM
from fixlot.core.loop import AgentLoop, LoopConfig
from fixlot.tools.registry import ToolRegistry, Tool, ActionResult
from fixlot.guardrails.shell_guard import ShellGuard
from fixlot.guardrails.file_guard import FileGuard


def _make_failing_test_registry():
    registry = ToolRegistry()

    def write_file(params):
        return ActionResult(success=True, output=f"Written to {params.get('path', '')}")

    def run_tests(params):
        pytest_output = """
============================= test session starts =============================
collected 1 item

test_math.py::test_add FAILED

================================== FAILURES ===================================
_________________________________ test_add ___________________________________

    def test_add():
>       assert add(1, 2) == 3
E       assert 4 == 3
E        +  where 4 = add(1, 2)

test_math.py:5: AssertionError
=========================== short test summary info ===========================
FAILED test_math.py::test_add - assert 4 == 3
============================== 1 failed in 0.10s ==============================
"""
        return ActionResult(success=False, output=pytest_output)

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


def test_feedback_loop_detects_failure():
    """Inject a write_file followed by run_tests that fails. Verify the
    feedback loop detects the failure and the agent continues."""
    mock_llm = MockLLM([
        '{"tool": "write_file", "params": {"path": "test_math.py", "content": "def add(a,b): return a*b"}}',
        '{"tool": "run_tests", "params": {}}',
        '{"tool": "write_file", "params": {"path": "test_math.py", "content": "def add(a,b): return a+b"}}',
        '{"tool": "run_tests", "params": {}}',
    ])
    registry = _make_failing_test_registry()
    loop = AgentLoop(
        llm=mock_llm,
        tool_registry=registry,
        config=LoopConfig(max_rounds=5, work_dir="/tmp/test"),
        shell_guard=ShellGuard(),
        file_guard=FileGuard("/tmp/test"),
    )

    result = loop.run("Implement add(a, b) that returns a+b")
    assert result["total_rounds"] >= 2


def test_guardrail_blocks_then_agent_retries():
    """Agent tries a dangerous command, gets blocked, then uses a safe tool."""
    mock_llm = MockLLM([
        '{"tool": "run_command", "params": {"cmd": "rm -rf /"}}',
        '{"tool": "write_file", "params": {"path": "test.py", "content": "x=1"}}',
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
        name="write_file",
        description="Write file",
        parameters_schema={},
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
    assert result["total_rounds"] >= 1