"""Types and constants for LLM streaming responses."""


class ChunkType:
    """Event types for streaming response chunks"""
    OUTPUT_TEXT_DELTA = "response.output_text.delta"
    OUTPUT_ITEM_ADDED = "response.output_item.added"
    OUTPUT_ITEM_DONE = "response.output_item.done"
    RESPONSE_COMPLETED = "response.completed"


class ItemType:
    """Item types within streaming responses"""
    FUNCTION_CALL = "function_call"
