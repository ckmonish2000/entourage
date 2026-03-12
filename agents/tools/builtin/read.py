from pathlib import Path
from itertools import islice
from utils.file_utils import get_file_type
from agents.core.config import MAX_LINE_LENGTH, UNSUPPORTED_FILE_TYPES
# from ..registry import register_tool
from typing import TypedDict
from .write_file import mark_file_as_read

class ReadResponse(TypedDict):
    path: str
    content: str
    start_line: int
    end_line: int
    lines_returned: int
    total_lines: int
    has_more: bool
    file_size_bytes: int
    encoding: str



# @register_tool
def read(path: str, encoding: str = "utf-8", offset: int = 1, limit: int = 2000) -> ReadResponse:
    """
    Read the contents of a file with comprehensive metadata.

    This function reads a specified range of lines from a file and returns formatted content
    along with detailed metadata about the file and read operation. Lines exceeding MAX_LINE_LENGTH
    are automatically truncated with an ellipsis indicator.

    Args:
        path (str): The path to the file to read. Supports ~ expansion and relative paths.
        encoding (str, optional): The character encoding of the file. Defaults to "utf-8".
        offset (int, optional): The starting line number (1-indexed). Defaults to 1.
        limit (int, optional): The maximum number of lines to read from the offset. Defaults to 2000.

    Returns:
        ReadResponse: A TypedDict containing:
            - path (str): Absolute resolved path to the file
            - content (str): Formatted file content with line numbers (e.g., "  42 | line content")
            - start_line (int): The first line number returned
            - end_line (int): The last line number returned
            - lines_returned (int): Total number of lines in the response
            - total_lines (int): Total number of lines in the entire file
            - has_more (bool): True if there are lines beyond the returned range
            - file_size_bytes (int): File size in bytes
            - encoding (str): The encoding used to read the file

    Raises:
        FileNotFoundError: If the specified path does not exist
        ValueError: If the path is not a file or the file type is unsupported
        UnicodeDecodeError: If the file cannot be decoded with the specified encoding

    Examples:
        >>> result = read("example.txt")
        >>> print(f"Read {result['lines_returned']} of {result['total_lines']} lines")
        >>> print(result['content'])

        >>> result = read("large_file.py", offset=100, limit=50)
        >>> if result['has_more']:
        ...     print("More content available")
    """
    path_obj = Path(path).expanduser().resolve()

    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {path_obj}")

    if not path_obj.is_file():
        raise ValueError(f"Path is not a file: {path_obj}")

    file_type = get_file_type(path_obj)

    if file_type in UNSUPPORTED_FILE_TYPES:
        raise ValueError(f"File type {file_type} is not supported")

    # Get file size in bytes
    file_size_bytes = path_obj.stat().st_size

    # Count total lines in the file
    with open(path_obj, "r", encoding=encoding) as f:
        total_lines = sum(1 for _ in f)

    # Read the specified range of lines
    with open(path_obj, "r", encoding=encoding) as f:
        lines = []

        # Skip lines before offset
        for _ in range(offset - 1):
            next(f, None)

        # Read up to limit lines starting from offset
        for index, line in enumerate(islice(f, limit), start=offset):
            truncated_line = line.rstrip('\n\r')
            if len(truncated_line) > MAX_LINE_LENGTH:
                truncated_line = truncated_line[:MAX_LINE_LENGTH] + "..."
            lines.append(f"{index:4d} | {truncated_line}")

        # Calculate metadata
        lines_returned = len(lines)
        end_line = offset + lines_returned - 1 if lines_returned > 0 else offset
        has_more = end_line < total_lines
        content = "\n".join(lines)

        # Mark file as read to enable write_file safety mechanism
        mark_file_as_read(str(path_obj))

        return ReadResponse(
            path=str(path_obj),
            content=content,
            start_line=offset,
            end_line=end_line,
            lines_returned=lines_returned,
            total_lines=total_lines,
            has_more=has_more,
            file_size_bytes=file_size_bytes,
            encoding=encoding
        )

