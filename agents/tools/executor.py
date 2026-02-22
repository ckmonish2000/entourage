from typing import Literal, TypedDict, Any
from .registry import tool_registry


class ToolSuccessResponse(TypedDict):
    type: Literal["success"]
    result: Any


class ToolErrorResponse(TypedDict):
    type: Literal["error"]
    message: str


ToolExecutionResult = ToolSuccessResponse | ToolErrorResponse


def execute_tool(tool_name: str, arguments: dict[str, Any]) -> ToolExecutionResult:
    """Execute a registered tool by name with keyword arguments.

    Returns the tool result when found, otherwise a not-found message.
    """
    try:
        if tool_name in tool_registry:
            return {"type": "success", "result": tool_registry[tool_name](**arguments)}
        else:
            return {"type": "error", "message": "Tool not found"}
    except Exception as e:
        return {"type": "error", "message": str(e)}
