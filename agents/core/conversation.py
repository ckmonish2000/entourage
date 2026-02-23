from .types import MessageRole, MessageRoleType
from datetime import datetime


class Conversation:
    def __init__(self, session_id:str, system_prompt):
        self.session_id = session_id
        self.message = [
            {"session_id": session_id, "role": MessageRole.SYSTEM, "content": system_prompt, "createdAt": datetime.now()}
        ]
        self.tool_calls = []

    def add_message(self, role: MessageRoleType, content):
        message = {"session_id": self.session_id, "role": role, "content": content,"createdAt":datetime.now()}
        self.message.append(message)

    def add_tool_call(self, tool_call):
        tool_call = {**tool_call, "session_id": self.session_id, "createdAt":datetime.now(), "role":"Function Call"}
        self.tool_calls.append(tool_call)
    
    def get_tool_by_id(self, tool_call_id):
        """Find a tool call by its call_id in the tracking list.

        Returns the index and tool call dict if found, otherwise (None, None).
        """
        for index, tool_call in enumerate(self.tool_calls):
            if tool_call['call_id'] == tool_call_id:
                return index, tool_call
        return None, None

    def update_tool_call(self, type, call_id, name, arguments={}, output=None):
        """Update or add a tool call entry in the tracking list.

        If a tool call with the given call_id exists, it's updated.
        Otherwise, a new entry is appended with session metadata.
        """
        index, tool_call = self.get_tool_by_id(call_id)
        tool_call_data = {
            "type": type,
            "call_id": call_id,
            "name": name,
            "arguments": arguments,
            "output": output,
            "session_id": self.session_id,
            "createdAt": datetime.now(),
            "role":"Function Call"
        }

        if index is not None:
            self.tool_calls[index] = tool_call_data
        else:
            self.tool_calls.append(tool_call_data)

    def get_messages(self):
        messages = []
        for msg in self.message:
            messages.append({"role": msg["role"], "content": msg["content"]})
        return messages
    
    def get_history(self):
        """Return all messages and tool calls sorted by createdAt timestamp."""
        history = [*self.tool_calls, *self.message]
        return sorted(history, key=lambda x: x.get('createdAt', datetime.min))

    def get_tool_calls(self):
        """Return all tool calls tracked in this conversation sorted by createdAt."""
        return sorted(self.tool_calls, key=lambda x: x.get('createdAt', datetime.min))
