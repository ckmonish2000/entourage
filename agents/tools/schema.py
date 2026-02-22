import inspect
from typing import Callable, TypedDict
from .types import TYPE_MAPPING


class ExtractedFuncResponse(TypedDict):
    properties: dict[str, object]
    required_parameters: list[str]


def generate_tool_schema(func: Callable[..., object], schema_list: list):
    """Build and store an OpenAI-style tool schema from a function signature.

    Generates a tool schema with function name, description, and parameter
    specifications. Required parameters are inferred from arguments without
    defaults. Parameter annotations are mapped to JSON schema primitive types.
    """
    func_args = extract_func_arguments(func)
    properties = func_args["properties"]
    required_parameters = func_args["required_parameters"]

    schema_list.append({
        "type": "function",
        "name": func.__name__,
        "description": func.__doc__,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required_parameters
        }
    })


def extract_func_arguments(func: object) -> ExtractedFuncResponse:
    """Extract function arguments from a function signature.

    Inspects the function signature to build a properties dict with type
    information and a list of required parameters (those without defaults).
    """
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
