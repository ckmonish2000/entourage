"""Types and constants for conversation messages."""
from typing import Literal, TypedDict


class MessageRole:
    """Message roles for conversation history"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    DEVELOPER = "developer"


MessageRoleType = Literal["user", "assistant", "system", "developer"]

class Usage(TypedDict):
    input_tokens: int
    output_tokens: int
    total_tokens: int