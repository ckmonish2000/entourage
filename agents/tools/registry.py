from typing import Callable
from .schema import generate_tool_schema

tool_registry = {}
tool_schema = []


def register_tool(func: Callable[..., object]):
    """Register a callable tool and generate its schema metadata.

    The tool is indexed by function name in ``tool_registry`` and exposed to
    the model through a generated schema entry in ``tool_schema``.
    """
    tool_registry[func.__name__] = func
    generate_tool_schema(func, tool_schema)
    return func
