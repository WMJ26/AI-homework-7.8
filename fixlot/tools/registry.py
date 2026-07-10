from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Action:
    tool: str
    params: dict
    raw: str


@dataclass
class ActionResult:
    success: bool
    output: str
    error: str | None = None


@dataclass
class Tool:
    name: str
    description: str
    parameters_schema: dict
    handler: Callable[[dict], ActionResult]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_tool_descriptions(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters_schema": t.parameters_schema,
            }
            for t in self._tools.values()
        ]

    def dispatch(self, action: Action) -> ActionResult:
        tool = self._tools.get(action.tool)
        if not tool:
            return ActionResult(
                success=False,
                output="",
                error=f"Unknown tool: {action.tool}",
            )
        try:
            return tool.handler(action.params)
        except Exception as e:
            return ActionResult(
                success=False,
                output="",
                error=f"Tool execution error: {e}",
            )