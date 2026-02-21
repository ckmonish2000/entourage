from .executor import register_tool
from typing import Optional
@register_tool
def get_current_weather(location: str) -> str:
    """Get the current weather in a given location"""
    # Replace this with a real implementation
    return f"The current weather in {location} is 30C."