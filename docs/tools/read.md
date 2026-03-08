# Tool: read

Reads the contents of a file with comprehensive metadata, including line numbers and truncation for long lines.

## Arguments
- `path` (str): The path to the file to read. Supports `~` expansion and relative paths.
- `encoding` (str, optional): The character encoding. Defaults to `"utf-8"`.
- `offset` (int, optional): The starting line number (1-indexed). Defaults to `1`.
- `limit` (int, optional): The maximum number of lines to read. Defaults to `2000`.

## Returns
A dictionary containing:
- `path`: Absolute resolved path.
- `content`: Formatted content with line numbers (e.g., `  42 | line content`).
- `start_line`: First line number returned.
- `end_line`: Last line number returned.
- `lines_returned`: Count of lines in response.
- `total_lines`: Total lines in the file.
- `has_more`: Boolean indicating if more lines exist.
- `file_size_bytes`: File size in bytes.

## Example
```python
read(path="main.py", offset=1, limit=100)
```
