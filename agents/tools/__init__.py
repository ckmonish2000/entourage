from . import get_current_weather
WEATHER_TOOL_SCHEMA = {
      "type": "function",
      "name": "get_current_weather",
      "description": "Get the current weather in a given location.",
      "parameters": {
          "type": "object",
          "properties": {
              "location": {"type": "string", "description": "City or location name"}
          },
          "required": ["location"]
      }
  }

DUMMY_TOOL_SCHEMA = {
    "type": "function",
    "name": "dummy_tool",
    "description": "A dummy tool that does nothing.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}
tools = [WEATHER_TOOL_SCHEMA,DUMMY_TOOL_SCHEMA]   