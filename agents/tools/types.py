"""Type mapping for tool schema generation."""

# Type mapping for Python types to JSON schema types
TYPE_MAPPING = {
    int: "integer",
    str: "string",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object"
}
