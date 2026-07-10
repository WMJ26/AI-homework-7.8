import pytest
from fixlot.tools.registry import Tool, Action, ActionResult, ToolRegistry


class TestTool:
    def test_tool_creation(self):
        def handler(params):
            return ActionResult(success=True, output="done")

        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters_schema={"param1": "string"},
            handler=handler,
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.parameters_schema == {"param1": "string"}

    def test_tool_handler_callable(self):
        def handler(params):
            return ActionResult(success=True, output=params.get("msg", ""))

        tool = Tool(
            name="echo",
            description="echo",
            parameters_schema={},
            handler=handler,
        )
        result = tool.handler({"msg": "hello"})
        assert result.success is True
        assert result.output == "hello"


class TestAction:
    def test_action_creation(self):
        action = Action(tool="read_file", params={"path": "test.py"}, raw="raw response")
        assert action.tool == "read_file"
        assert action.params == {"path": "test.py"}
        assert action.raw == "raw response"


class TestActionResult:
    def test_success_result(self):
        result = ActionResult(success=True, output="content")
        assert result.success is True
        assert result.output == "content"
        assert result.error is None

    def test_failure_result(self):
        result = ActionResult(success=False, output="", error="File not found")
        assert result.success is False
        assert result.output == ""
        assert result.error == "File not found"


class TestToolRegistry:
    def test_register_and_list_tools(self):
        registry = ToolRegistry()

        def handler(params):
            return ActionResult(success=True, output="ok")

        tool = Tool(
            name="my_tool",
            description="desc",
            parameters_schema={},
            handler=handler,
        )
        registry.register(tool)
        assert "my_tool" in registry.list_tools()
        assert registry.get_tool("my_tool") == tool

    def test_dispatch_known_tool(self):
        registry = ToolRegistry()

        def handler(params):
            return ActionResult(success=True, output=f"got {params['x']}")

        tool = Tool(
            name="compute",
            description="desc",
            parameters_schema={"x": "int"},
            handler=handler,
        )
        registry.register(tool)

        action = Action(tool="compute", params={"x": 42}, raw="")
        result = registry.dispatch(action)
        assert result.success is True
        assert result.output == "got 42"

    def test_dispatch_unknown_tool_returns_error(self):
        registry = ToolRegistry()
        action = Action(tool="nonexistent", params={}, raw="")
        result = registry.dispatch(action)
        assert result.success is False
        assert "Unknown tool" in result.error

    def test_get_tool_descriptions(self):
        registry = ToolRegistry()

        def handler(params):
            return ActionResult(success=True, output="")

        registry.register(Tool(
            name="read_file",
            description="Read a file",
            parameters_schema={"path": "string"},
            handler=handler,
        ))
        registry.register(Tool(
            name="write_file",
            description="Write a file",
            parameters_schema={"path": "string", "content": "string"},
            handler=handler,
        ))

        descs = registry.get_tool_descriptions()
        assert len(descs) == 2
        assert any(d["name"] == "read_file" for d in descs)
        assert any(d["name"] == "write_file" for d in descs)