import inspect
from typing import Optional
tool_registry = {}
tool_schema = []

def register_tool(func: callable):
    """Register a tool with the tool registry"""
    tool_registry[func.__name__] = func
    generate_tool_schema(func)
    return func

def generate_tool_schema(func: callable):
    """Generate tool schema from function signature"""
    type_mapping = {
        int: "integer",
        str: "string",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object"
    }

    signature = inspect.signature(func)
    parameter = {}
    for param, param_type in signature.parameters.items():
        is_optional = param_type.default != inspect.Parameter.empty
        parameter[param] = {
            "type": type_mapping.get(param_type.annotation, "string"),
            "required": not is_optional
        }

    tool_schema.append({
        "type": "function",
        "name": func.__name__,
        "description": func.__doc__,
        "parameters": parameter
    })

def execute_tool(tool_name:str,arguments:dict):
    """Execute a tool"""
    if tool_name in tool_registry:
        return tool_registry[tool_name](**arguments)
    else:
        return f"Tool {tool_name} not found"