import os
from pathlib import Path
from typing import Optional, Set
from ..registry import register_tool

# Session-level cache to track which files have been read
# This prevents accidental overwrites without context
_READ_FILES_CACHE: Set[str] = set()


def mark_file_as_read(file_path: str) -> None:
    """Mark a file as having been read during this session.

    This function should be called by the read tool to enable write safety.

    Args:
        file_path: Absolute path to the file that was read.
    """
    normalized_path = str(Path(file_path).resolve())
    _READ_FILES_CACHE.add(normalized_path)


def clear_read_cache() -> None:
    """Clear the read files cache.

    This should be called when starting a new session or when explicitly
    resetting the safety mechanism.
    """
    _READ_FILES_CACHE.clear()


@register_tool
def write_file(
    file_path: str,
    content: str,
    working_dir: Optional[str] = None
) -> str:
    """Write complete content to a file, overwriting if it exists.

    This tool is optimized for creating new files or performing complete rewrites
    of small files. For targeted changes to existing files, use edit_file instead.

    Safety Features:
        - Enforces absolute paths to prevent ambiguity
        - Requires read-before-write for existing files to prevent data loss
        - Automatically creates parent directories as needed
        - Provides clear feedback on success/failure

    Args:
        file_path: The absolute path to the target file. Relative paths are rejected.
        content: The complete content to write to the file.
        working_dir: Optional base directory context for logging. The file_path
                    must still be absolute.

    Returns:
        Success message with line count, or error message explaining the failure.

    Success Format:
        - New file: "✓ Created /absolute/path/to/file.py (42 lines)"
        - Overwritten: "✓ Successfully wrote to /absolute/path/to/file.py (42 lines)"

    Error Format:
        - Missing read: "✗ Error: You must read the file before writing to it"
        - Relative path: "✗ Error: File path must be absolute, not relative"
        - Permission/IO: "✗ Error: Failed to write to file: {exception details}"

    Behavior:
        - Empty command returns immediate error without execution
        - Parent directories are created automatically (mkdir -p behavior)
        - Existing files require prior read operation to enable write
        - File is written with UTF-8 encoding
        - Line count is calculated from content for feedback

    Examples:
        Creating a new file:
        >>> write_file(
        ...     file_path="/Users/monish/project/src/new_module.py",
        ...     content="def main():\\n    print('Hello World')"
        ... )
        '✓ Created /Users/monish/project/src/new_module.py (2 lines)'

        Overwriting after read:
        >>> read(path="/Users/monish/project/config.py")  # Required first
        >>> write_file(
        ...     file_path="/Users/monish/project/config.py",
        ...     content="DEBUG = True\\nPORT = 8080"
        ... )
        '✓ Successfully wrote to /Users/monish/project/config.py (2 lines)'

        Relative path rejection:
        >>> write_file(file_path="config.py", content="test")
        '✗ Error: File path must be absolute, not relative...'

    When to Use:
        - Creating brand new files in a project
        - Complete replacement of small configuration files
        - Writing generated code or documentation

    When NOT to Use:
        - Editing existing code files (use edit_file for surgical changes)
        - Large files where partial edits are more efficient
        - Files where you need to preserve specific sections

    Security Notes:
        - No path traversal validation beyond absolute path requirement
        - Creates directories with default permissions
        - Overwrites files without backup
        - UTF-8 encoding is hardcoded
    """

    # 1. ENFORCE ABSOLUTE PATHS
    if not os.path.isabs(file_path):
        return "✗ Error: File path must be absolute, not relative. " \
               "Please provide the full path starting from the root."

    target_path = Path(file_path)
    is_existing = target_path.exists()

    # 2. ENFORCE READ-BEFORE-WRITE SAFETY
    if is_existing:
        normalized_path = str(target_path.resolve())
        if normalized_path not in _READ_FILES_CACHE:
            return f"✗ Error: You must read the file before writing to it. " \
                   f"Use read(path='{file_path}') first to verify content."

    # 3. AUTOMATIC DIRECTORY CREATION
    try:
        parent_dir = target_path.parent
        if parent_dir and not parent_dir.exists():
            parent_dir.mkdir(parents=True, m=True)
    except Exception as e:
        return f"✗ Error: Failed to create parent directories: {e}"

    # 4. PERFORM THE WRITE
    try:
        target_path.write_text(content, encoding="utf-8")
    except Exception as e:
        return f"✗ Error: Failed to write to file: {e}"

    # 5. DIFFERENTIATED FEEDBACK
    line_count = len(content.splitlines()) if content else 0

    if not is_existing:
        return f"✓ Created {file_path} ({line_count} lines)"
    else:
        return f"✓ Successfully wrote to {file_path} ({line_count} lines)"
