# -*- coding: utf-8 -*-
import difflib
from typing import List, Optional
from pathlib import Path
import os
from ..registry import register_tool
from .write_file import mark_file_as_read


def resolve_path(path: str, working_dir: Optional[str] = None) -> Path:
    """
    Resolve a path to an absolute Path object.

    Args:
        path: File path (absolute or relative)
        working_dir: Optional base directory for relative paths

    Returns:
        Absolute Path object

    How it works:
    1. Convert string to Path object
    2. If already absolute, return as-is
    3. If relative, resolve against working_dir or current directory

    Why this matters:
    - LLMs often work with multiple projects simultaneously
    - Relative paths need context to be meaningful
    - Absolute paths are unambiguous and safe
    """
    path_obj = Path(path).expanduser()

    # If already absolute, return it
    if path_obj.is_absolute():
        return path_obj.resolve()

    # Otherwise, resolve against working_dir or current directory
    if working_dir:
        base = Path(working_dir).expanduser().resolve()
    else:
        base = Path.cwd()

    return (base / path_obj).resolve()


def get_line_numbers(content: str, substring: str) -> List[int]:
    """
    Find all line numbers (1-indexed) where a substring appears.

    This searches for the substring across the entire content, not just
    within individual lines. This is important for multi-line old_string values.

    Args:
        content: The full file content
        substring: The string to search for

    Returns:
        List of line numbers (1-indexed) where the substring starts
    """
    if not substring:
        return []

    lines = content.splitlines(keepends=True)
    matches = []
    current_pos = 0

    while True:
        idx = content.find(substring, current_pos)
        if idx == -1:
            break

        # Count which line this position is on
        line_num = content[:idx].count('\n') + 1
        matches.append(line_num)
        current_pos = idx + 1

    return matches


@register_tool
def edit_file(
    path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
    working_dir: Optional[str] = None
) -> str:
    """
    Perform surgical text replacement in a file using exact literal matching.

    This tool provides precision editing by requiring exact string matches. By default,
    it enforces uniqueness to prevent accidental widespread changes. The tool follows
    the same safety patterns as write_file and integrates with the read-before-write
    mechanism.

    Args:
        path: Target file path (absolute or relative)
        old_string: Exact text to replace (must match including whitespace/indentation)
        new_string: Replacement text
        replace_all: If True, replace all occurrences. If False (default), requires
                    exactly one match to ensure precision
        working_dir: Base directory for resolving relative paths (defaults to cwd)

    Returns:
        Success message with diff, or detailed error message

    Success Format:
        - New file: "Created /path/to/file.py (N lines)"
        - Single edit: "Edited /path/to/file.py (old_lines  new_lines)\n\nDiff:\n..."
        - Multiple edits: "Edited /path/to/file.py (replaced N occurrences)\n\nDiff:\n..."

    Error Format:
        - Not found: "Error: The string to replace was not found in {path}..."
        - Ambiguous: "Error: Multiple matches (N) found at lines: [...]..."
        - Read error: "Error reading file: {details}"
        - Write error: "Error writing file: {details}"

    Behavior:
        - Empty old_string creates a new file (like write_file)
        - Requires unique match by default (Claude Code pattern)
        - Automatically creates parent directories if needed
        - Returns unified diff for visual confirmation
        - Integrates with read-before-write safety for existing files

    Examples:
        Single surgical edit (default):
        >>> edit_file(
        ...     path="config.py",
        ...     old_string='DEBUG = False',
        ...     new_string='DEBUG = True'
        ... )
        ' Edited config.py (1 lines � 1 lines)\\n\\nDiff:\\n...'

        Global replacement:
        >>> edit_file(
        ...     path="utils.py",
        ...     old_string='v1',
        ...     new_string='v2',
        ...     replace_all=True
        ... )
        ' Edited utils.py (replaced 5 occurrences)\\n\\nDiff:\\n...'

        Creating new file:
        >>> edit_file(
        ...     path="src/components/LoginForm.tsx",
        ...     old_string='',
        ...     new_string='export const LoginForm = () => { ... }'
        ... )
        ' Created src/components/LoginForm.tsx (10 lines)'

        With working directory context:
        >>> edit_file(
        ...     path="src/config.py",
        ...     old_string='PORT = 3000',
        ...     new_string='PORT = 8080',
        ...     working_dir="/projects/my-app"
        ... )
        ' Edited src/config.py (1 lines � 1 lines)\\n\\nDiff:\\n...'

    When to Use:
        - Surgical edits to specific code sections
        - Renaming variables/functions across a file (with replace_all=True)
        - Targeted configuration changes
        - Refactoring specific patterns

    When NOT to Use:
        - Complete file rewrites (use write_file)
        - Multiple different edits (use multiple calls or write_file)
        - Line-number based editing (this uses literal string matching)

    Security & Safety:
        - Supports both absolute and relative paths
        - Creates parent directories automatically
        - No backup created (atomic write from memory)
        - UTF-8 encoding hardcoded
        - Uniqueness enforcement prevents accidental corruption
    """
    # Resolve the path considering working_dir
    file_path = resolve_path(path, working_dir)

    # Check if this is a new file (for differentiated feedback)
    is_new_file = not file_path.exists()

    # Handle new file creation (empty old_string case)
    if not old_string and is_new_file:
        # Creating a new file - use write_file pattern
        try:
            parent_dir = file_path.parent
            if parent_dir and not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)

            file_path.write_text(new_string, encoding="utf-8")

            line_count = len(new_string.splitlines()) if new_string else 0
            return f" Created {path} ({line_count} lines)"

        except Exception as e:
            return f"Error creating file: {str(e)}"

    # If editing existing file, read and validate
    if not is_new_file:
        try:
            original_content = file_path.read_text(encoding="utf-8")

            # Mark as read for write_file safety integration
            mark_file_as_read(str(file_path))

            # Check for existence and uniqueness
            count = original_content.count(old_string)

            if count == 0:
                return f"Error: The string to replace was not found in {path}.\n" \
                       "Please ensure exact spelling, case, and indentation match the file content."

            if count > 1 and not replace_all:
                lines = get_line_numbers(original_content, old_string)
                return f"Error: Multiple matches ({count}) found for the provided string in {path} at lines: {lines}.\n" \
                       "Please provide more surrounding context to make the match unique, or set replace_all=True."

            # Perform replacement
            if replace_all:
                new_content = original_content.replace(old_string, new_string)
            else:
                # Replace only first occurrence
                new_content = original_content.replace(old_string, new_string, 1)

        except Exception as e:
            return f"Error reading file: {str(e)}"
    else:
        # Trying to edit non-existent file with non-empty old_string
        return f"Error: File {path} does not exist. To create it, use old_string='' or write_file tool."

    # Create parent directories if needed
    try:
        parent_dir = file_path.parent
        if parent_dir and not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"Error creating directory {parent_dir}: {str(e)}"

    # Write the file atomically
    try:
        file_path.write_text(new_content, encoding="utf-8")
    except Exception as e:
        return f"Error writing file: {str(e)}"

    # Generate diff for visual confirmation
    diff = difflib.unified_diff(
        original_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm=""
    )
    diff_text = "".join(list(diff))

    # Calculate line changes
    old_lines = old_string.count('\n') + 1 if old_string else 0
    new_lines = new_string.count('\n') + 1 if new_string else 0

    # Provide context-appropriate feedback
    if replace_all and count > 1:
        return f" Edited {path} (replaced {count} occurrences)\n\nDiff:\n```diff\n{diff_text}\n```"
    else:
        return f" Edited {path} ({old_lines} lines � {new_lines} lines)\n\nDiff:\n```diff\n{diff_text}\n```"
