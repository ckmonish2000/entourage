"""Types and constants for conversation messages."""
from typing import Literal


class MessageRole:
    """Message roles for conversation history"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    DEVELOPER = "developer"


MessageRoleType = Literal["user", "assistant", "system", "developer"]
