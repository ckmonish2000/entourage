import inspect
from typing import Callable, Optional,Literal,TypedDict
from agents.constants import TYPE_MAPPING

tool_registry = {}
tool_schema = []

class ExtractedFuncResponse(TypedDict):
    properties: dict[str, object]
    required_parameters: list[str]

def register_tool(func: Callable[..., object]):
    """Register a callable tool and generate its schema metadata.

    The tool is indexed by function name in ``tool_registry`` and exposed to
    the model through a generated schema entry in ``tool_schema``.
    """
    tool_registry[func.__name__] = func
    generate_tool_schema(func)
    return func

def generate_tool_schema(func: Callable[..., object]):
    """Build and store an OpenAI-style tool schema from a function signature.

    Required parameters are inferred from arguments without defaults. Parameter
    annotations are mapped to JSON schema primitive types where possible.
    """
    func_args = extract_func_arguments(func)
    properties = func_args["properties"]
    required_parameters = func_args["required_parameters"]

    tool_schema.append({
        "type": "function",
        "name": func.__name__,
        "description": func.__doc__,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required_parameters
        }
    })

def extract_func_arguments(func:object) -> ExtractedFuncResponse:
    """Extract function arguments from a function signature."""
    signature = inspect.signature(func)
    properties = {}
    required_parameters = []

    # computes the required properties and parameters types for tool call
    for param, param_type in signature.parameters.items():
        is_optional = param_type.default != inspect.Parameter.empty
        properties[param] = {
            "type": TYPE_MAPPING.get(param_type.annotation, "string"),
        }
        if not is_optional:
            required_parameters.append(param)

    return {
        "properties": properties,
        "required_parameters": required_parameters
    }

   

def execute_tool(tool_name:str,arguments:dict):
    """Execute a registered tool by name with keyword arguments.

    Returns the tool result when found, otherwise a not-found message.
    """
    if tool_name in tool_registry:
        return tool_registry[tool_name](**arguments)
    else:
        return f"Tool {tool_name} not found"
