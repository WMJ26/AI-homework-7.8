import pytest
from fixlot.core.context import ContextBuilder, build_system_prompt


class TestContextBuilder:
    def test_builds_basic_messages(self):
        builder = ContextBuilder(task="Fix the failing test")
        messages = builder.build()

        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"

    def test_includes_task_in_user_prompt(self):
        builder = ContextBuilder(task="Fix the failing test")
        messages = builder.build()
        user_msg = [m for m in messages if m["role"] == "user"][0]
        assert "Fix the failing test" in user_msg["content"]

    def test_includes_tool_descriptions(self):
        tools = [
            {"name": "read_file", "description": "Read a file", "parameters_schema": {}},
            {"name": "write_file", "description": "Write a file", "parameters_schema": {}},
        ]
        builder = ContextBuilder(task="test", tools=tools)
        messages = builder.build()
        system_msg = messages[0]["content"]
        assert "read_file" in system_msg
        assert "write_file" in system_msg

    def test_includes_feedback_in_user_prompt(self):
        builder = ContextBuilder(task="Fix bug")
        builder.add_feedback("Test failed: assertion error")
        messages = builder.build()
        user_msg = [m for m in messages if m["role"] == "user"][0]
        assert "Test failed: assertion error" in user_msg["content"]

    def test_includes_history(self):
        builder = ContextBuilder(task="Fix bug")
        builder.add_history("user", "Run the tests")
        builder.add_history("assistant", "Tests passed")
        messages = builder.build()
        contents = [m["content"] for m in messages]
        assert any("Run the tests" in c for c in contents)
        assert any("Tests passed" in c for c in contents)

    def test_resets_builder(self):
        builder = ContextBuilder(task="task1")
        builder.add_feedback("feedback")
        builder.reset("task2")
        messages = builder.build()
        user_msg = [m for m in messages if m["role"] == "user"][0]
        assert "task2" in user_msg["content"]
        assert "feedback" not in user_msg["content"]


class TestBuildSystemPrompt:
    def test_includes_tools(self):
        tools = [{"name": "read_file", "description": "Read a file", "parameters_schema": {}}]
        prompt = build_system_prompt(tools)
        assert "read_file" in prompt

    def test_includes_role_instruction(self):
        prompt = build_system_prompt([])
        assert "coding agent" in prompt.lower() or "assistant" in prompt.lower()

    def test_includes_output_format(self):
        prompt = build_system_prompt([])
        assert "json" in prompt.lower() or "format" in prompt.lower()