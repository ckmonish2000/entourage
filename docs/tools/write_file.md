# Tool: write_file

Writes the entire content to a file, overwriting it if it already exists. This tool is optimized for creating new files or performing complete rewrites of small files.

## Arguments
- `file_path` (str): The **absolute** path to the target file.
- `content` (str): The complete content to write to the file.
- `working_dir` (str, optional): Base directory context for the operation. Note that `file_path` must still be absolute.

## Constraints
- **Absolute Paths Only**: The `file_path` must be an absolute path. Relative paths will result in an error.
- **Read-Before-Write**: For existing files, you **must** call `read_file` on the file before you can use `write_file` to overwrite it. This safety mechanism prevents accidental data loss.
- **Automatic Directory Creation**: If the parent directories for the `file_path` do not exist, they will be created automatically (equivalent to `mkdir -p`).
- **No Partial Edits**: This tool replaces the *entire* file. For targeted changes to existing files, use `edit_file`.

## Returns
A success message or an error message.

### Success Format
- New file: `✓ Created /absolute/path/to/file.py (42 lines)`
- Overwritten file: `✓ Successfully wrote to /absolute/path/to/file.py (42 lines)`

### Error Format
- Missing Read: `✗ Error: You must read the file before writing to it`
- Relative Path: `✗ Error: File path must be absolute, not relative`

## Example Usage

### Creating a New File
```python
write_file(
    file_path="/Users/monish/project/src/new_module.py",
    content="def main():\n    print('Hello World')"
)
```
*Note: Directories like `src/` will be created if they don't exist.*

### Overwriting an Existing File (After Read)
```python
# 1. First, read the file to gain context and satisfy safety requirements
read(path="/Users/monish/project/config.py")

# 2. Now perform the write
write_file(
    file_path="/Users/monish/project/config.py",
    content="DEBUG = True\nPORT = 8080\nHOST = 'localhost'"
)
```

## When to use Write vs Edit
- **Write**: Use for creating brand new files or completely replacing very small configuration files where a full rewrite is simpler than a surgical edit.
- **Edit**: **Always prefer `edit_file` for existing files** in the codebase. It is safer, provides diffs for verification, and respects the "ALWAYS prefer editing existing files" mandate.

---

## Draft Implementation (Technical Reference)

This draft demonstrates the core logic for the `write_file` tool, including path resolution, the read-before-write safety check, and automatic directory creation.

```python
import os
from pathlib import Path
from typing import Optional, Set

# In a real implementation, this state would likely be managed 
# by the Agent or a session manager to track which files have been read.
_READ_FILES_CACHE: Set[str] = set()

def write_file(
    file_path: str,
    content: str,
    working_dir: Optional[str] = None
) -> str:
    """
    Draft implementation of the write_file tool.
    
    Args:
        file_path: Absolute path to the file.
        content: Complete content to write.
        working_dir: Optional base directory (for logging/context).
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

    # 3. AUTOMATIC DIRECTORY CREATION (Goose-inspired)
    try:
        parent_dir = target_path.parent
        if parent_dir and not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
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
```

