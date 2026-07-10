import os
from fixlot.tools.registry import ActionResult, Tool, ToolRegistry


def read_file(params: dict) -> ActionResult:
    path = params.get("path", "")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return ActionResult(success=True, output=content)
    except FileNotFoundError:
        return ActionResult(
            success=False, output="", error=f"File not found: {path}"
        )
    except PermissionError:
        return ActionResult(
            success=False, output="", error=f"Permission denied: {path}"
        )
    except Exception as e:
        return ActionResult(
            success=False, output="", error=f"Error reading file: {e}"
        )


def write_file(params: dict) -> ActionResult:
    path = params.get("path", "")
    content = params.get("content", "")
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return ActionResult(success=True, output=f"Written to {path}")
    except PermissionError:
        return ActionResult(
            success=False, output="", error=f"Permission denied: {path}"
        )
    except Exception as e:
        return ActionResult(
            success=False, output="", error=f"Error writing file: {e}"
        )


def create_file_tools(registry: ToolRegistry):
    registry.register(Tool(
        name="read_file",
        description="Read the contents of a file at the given path.",
        parameters_schema={"path": {"type": "string", "description": "Path to the file to read"}},
        handler=read_file,
    ))
    registry.register(Tool(
        name="write_file",
        description="Write content to a file at the given path. Creates parent directories if needed.",
        parameters_schema={
            "path": {"type": "string", "description": "Path to the file to write"},
            "content": {"type": "string", "description": "Content to write to the file"},
        },
        handler=write_file,
    ))