from typing import Literal, TypedDict, Any
from .registry import tool_registry
import asyncio
import inspect


class ToolSuccessResponse(TypedDict):
    type: Literal["success"]
    result: Any


class ToolErrorResponse(TypedDict):
    type: Literal["error"]
    message: str


ToolExecutionResult = ToolSuccessResponse | ToolErrorResponse


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> ToolExecutionResult:
    """Execute a registered tool by name with keyword arguments.

    Returns the tool result when found, otherwise a not-found message.
    Handles both sync and async tools automatically.
    """
    try:
        if tool_name in tool_registry:
            tool_func = tool_registry[tool_name]

            # Check if the tool is async
            if inspect.iscoroutinefunction(tool_func):
                result = await tool_func(**arguments)
            else:
                result = tool_func(**arguments)

            return {"type": "success", "result": result}
        else:
            return {"type": "error", "message": "Tool not found"}
    except Exception as e:
        return {"type": "error", "message": str(e)}
