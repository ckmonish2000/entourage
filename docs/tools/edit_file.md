# Tool: edit_file

Performs surgical text replacement within a file using exact literal matching.

## Arguments
- `path` (str): Path to the target file (absolute or relative).
- `old_string` (str): The exact literal text to be replaced.
- `new_string` (str): The replacement text.
- `replace_all` (bool, optional): If `true`, replaces all occurrences of `old_string`. Default is `false`.
- `working_dir` (str, optional): Base directory for resolving relative paths. Defaults to current working directory.

## Constraints
- By default, `old_string` must exist exactly once in the file to ensure precision.
- Recommended to use after a `read` operation to verify context and indentation.

## Example
```python
# Single surgical edit (Default)
edit_file(
    path="config.py",
    old_string='DEBUG = False',
    new_string='DEBUG = True'
)

# Global replacement
edit_file(
    path="utils.py",
    old_string='v1',
    new_string='v2',
    replace_all=True
)

# Working with relative paths and specific working directory
edit_file(
    path="src/config.py",  # Relative path
    old_string='PORT = 3000',
    new_string='PORT = 8080',
    working_dir="/projects/my-app"  # Resolves to /projects/my-app/src/config.py
)

# Creating a new file in nested directories (auto-creates parent dirs)
edit_file(
    path="src/components/auth/LoginForm.tsx",  # Parent dirs created automatically
    old_string='',  # Empty for new file
    new_string='export const LoginForm = () => { ... }'
)
```

---

## Implementation Discussion & Guidance

### 1. Inspiration: Claude Code vs. Goose

Both Claude Code and Goose prioritize **precision over convenience**.

*   **Claude Code (`str_replace_editor`)**: Its core strength is its strictness. It requires the `old_string` to be a unique match. If there are two identical lines, it will refuse to guess and instead force the LLM to provide more context (more lines before/after) to make the match unique. This prevents accidental, widespread "corruptions" of the codebase.
*   **Goose**: Focuses on the developer experience. It often integrates with tools like `grep` or `read` to ensure the LLM has seen the file content before attempting an edit.

**Recommendation**: Adopt the Claude Code "Unique Literal Match" strategy. It is the safest way for an LLM to interact with files.

### 2. Key Considerations for Implementation

*   **Uniqueness**: Your Python code should first count the occurrences of `old_string`. If `count != 1` and `replace_all` is `false`, return an error message explaining whether it was 0 (not found) or >1 (ambiguous).
*   **Atomicity**: Always try to read the whole file, perform the replacement in memory, and then write it back. This ensures that if the script crashes mid-way, you don't end up with a half-written file.
*   **Path Safety**: Never trust the `path` argument directly. Use `pathlib` to ensure the path is inside your project directory and hasn't been "hacked" using `../` (directory traversal).
*   **Encoding**: Always specify `encoding="utf-8"` when reading/writing to avoid issues with special characters.
*   **Working Directory Context**: Support both absolute and relative paths. Resolve relative paths against a configurable working directory for multi-project scenarios.
*   **Automatic Directory Creation**: When writing files, automatically create parent directories if they don't exist. This prevents errors and improves UX.
*   **Differentiated Feedback**: Provide different success messages for "Created" (new file) vs "Edited" (existing file) so the LLM understands what action occurred.

### 3. Python Guidance for Junior Developers

#### Use `TypedDict` for Argument Validation
In Python, you can use `TypedDict` from the `typing` module to define the structure of your tool's arguments.

```python
from typing import TypedDict, Optional

class EditFileArguments(TypedDict):
    path: str
    old_string: str
    new_string: str
    replace_all: Optional[bool]
```

#### Use `pathlib` over `os.path`
`pathlib` is the modern way to handle paths in Python. It's object-oriented and much cleaner.
```python
from pathlib import Path
file_path = Path("your/file.py").resolve()
```

#### Error Handling (The `try...except` block)
File operations can fail for many reasons (file doesn't exist, no permissions, disk full). Wrap your logic:
```python
try:
    content = file_path.read_text(encoding="utf-8")
except FileNotFoundError:
    return "Error: File not found."
except Exception as e:
    return f"Error reading file: {e}"
```

### 4. Why not line numbers?
Line numbers are "brittle." If another process (or your previous tool call) added a line at the top of the file, every line number below it is now wrong. Literal string matching with context (before/after lines) is much more robust against "drift."

### 5. Solving Ambiguity: The "Context" Strategy

You asked: *If there are multiple occurrences, how does the tool decide?*

The answer is: **It doesn't.** Unless `replace_all` is `true`, it should fail and ask for help. This is exactly how Claude Code works.

#### The "Fail Fast" Pattern
If you find 5 occurrences of `x = 1`, your tool should return:
> "Error: Multiple occurrences found (5). Please provide more surrounding code in `old_string` to make the match unique."

#### How the LLM fixes it:
Instead of sending:
`old_string: "x = 1"`

The LLM will "zoom out" and send:
```python
old_string: """
def initialize_user():
    x = 1
"""
```

By including the function header, the match becomes unique even if `x = 1` appears in ten other functions. This is why we don't need line numbers—**surrounding code is the best "address" for an edit.**

### 6. Response Format: Providing Context to the LLM

The response should provide "visual" confirmation so the LLM knows its change was applied correctly.

#### Success Response
Provide a unified diff showing exactly what changed. This provides the LLM with immediate visual confirmation of its work.

#### Error Response
If it fails, be extremely specific. Don't just say "Error."

*   **Not Found**: "Error: `old_string` not found in `path`. Please ensure you have the exact indentation and spelling."
*   **Multiple Matches**: "Error: Found 3 matches for `old_string`. Ambiguous edit. Please provide more context lines to make the match unique, or use `replace_all=true`."

---

## Draft Implementation (Blueprint)

This is a professional, Goose-inspired Python implementation with **working directory context**, **automatic directory creation**, and **differentiated feedback**.

```python
import difflib
from typing import List, Optional
from pathlib import Path
import os

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
    path_obj = Path(path)

    # If already absolute, return it
    if path_obj.is_absolute():
        return path_obj

    # Otherwise, resolve against working_dir or current directory
    if working_dir:
        base = Path(working_dir)
    else:
        base = Path.cwd()  # Current working directory

    return (base / path_obj).resolve()

def get_line_numbers(content: str, substring: str) -> List[int]:
    """Finds all line numbers (1-indexed) where a substring starts."""
    lines = content.splitlines()
    matches = []
    for i, line in enumerate(lines):
        if substring in line:
            matches.append(i + 1)
    return matches

def edit_file(
    path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
    working_dir: Optional[str] = None
) -> str:
    """
    Perform surgical text replacement in a file.

    Args:
        path: Target file path (absolute or relative)
        old_string: Exact text to replace
        new_string: Replacement text
        replace_all: Replace all occurrences (default: False)
        working_dir: Base directory for relative paths (default: current dir)

    Returns:
        Success message with diff or error message
    """
    # FEATURE 1: Working Directory Context
    # Resolve the path considering working_dir
    file_path = resolve_path(path, working_dir)

    # Check if this is a new file (for differentiated feedback later)
    is_new_file = not file_path.exists()

    # If editing existing file, read and validate
    if not is_new_file:
        try:
            original_content = file_path.read_text(encoding="utf-8")

            # Check for existence and uniqueness
            count = original_content.count(old_string)

            if count == 0:
                return f"Error: The string to replace was not found in {path}.\n" \
                       "Please ensure exact spelling, case, and indentation."

            if count > 1 and not replace_all:
                lines = get_line_numbers(original_content, old_string)
                return f"Error: Multiple matches ({count}) found for the provided string in {path} at lines: {lines}.\n" \
                       "Please provide more surrounding context to make the match unique, or set replace_all=true."

            # Perform replacement
            new_content = original_content.replace(old_string, new_string, -1 if replace_all else 1)

        except Exception as e:
            return f"Error reading file: {str(e)}"
    else:
        # New file: just use new_string as content
        original_content = ""
        new_content = new_string
        count = 1

    # FEATURE 2: Automatic Directory Creation
    # Create parent directories if they don't exist
    try:
        parent_dir = file_path.parent
        if parent_dir and not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
            # parents=True: Create all intermediate directories (like mkdir -p)
            # exist_ok=True: Don't error if directory already exists
    except Exception as e:
        return f"Error creating directory {parent_dir}: {str(e)}"

    # Write the file atomically
    try:
        file_path.write_text(new_content, encoding="utf-8")
    except Exception as e:
        return f"Error writing file: {str(e)}"

    # FEATURE 3: Differentiated Write Feedback
    # Provide different messages for new vs edited files
    if is_new_file:
        line_count = new_content.count('\n') + 1 if new_content else 0
        return f"Created {path} ({line_count} lines)"
    else:
        # Generate diff for edited files
        diff = difflib.unified_diff(
            original_content.splitlines(),
            new_content.splitlines(),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm=""
        )
        diff_text = "\n".join(list(diff))

        old_lines = old_string.count('\n') + 1
        new_lines = new_string.count('\n') + 1

        return f"Edited {path} ({old_lines} lines → {new_lines} lines)\n\nDiff:\n```diff\n{diff_text}\n```"
```

---

## Deep Dive for Junior Developers

### 1. Why `read_text()` instead of `open()` with a loop?

Great question! In many Python tutorials, you see this:
```python
with open("file.txt", "r") as f:
    for line in f:
        print(line)
```
This is **Streaming**. It's great for 10GB log files because you only keep one line in memory at a time. 

**However**, for a surgical edit tool, we use `read_text()` (which reads the whole file into one big string) for three reasons:
1.  **Complexity**: We need to count occurrences across the *entire* file to ensure uniqueness. If your `old_string` spans multiple lines, a line-by-line loop would miss it!
2.  **Size**: Source code files (like `.py`, `.js`, `.md`) are usually very small (a few KB or MB). Your computer has GBs of RAM, so loading a 1MB file as a string is perfectly safe and much faster.
3.  **Cleanliness**: `read_text()` is a `pathlib` method that handles opening and closing the file for you in one line. It's the modern, "Pythonic" way.

### 2. Mini-Tutorial: `difflib.unified_diff`

`difflib` is a built-in Python library for comparing sequences. `unified_diff` specifically creates the "Standard Diff" format used by Git.

#### How it works:
It takes two **lists of strings** (lines) and compares them.

```python
import difflib

list_a = ["Line 1", "Line 2", "Line 3"]
list_b = ["Line 1", "Line Changed", "Line 3"]

# Generate the diff
diff = difflib.unified_diff(list_a, list_b, fromfile="before.txt", tofile="after.txt")

# unified_diff returns a 'generator', so we join it into a string to see it
print("\n".join(list(diff)))
```

#### Understanding the Output:
*   `---`: The original file.
*   `+++`: The new file.
*   `@@ -1,3 +1,3 @@`: This is the "Hunk Header." It tells you where the change happened (start line, number of lines).
*   ` ` (space): Unchanged line (context).
*   `-`: Line removed from the original.
*   `+`: Line added to the new version.

In our tool, we use `.splitlines()` on our file strings to turn them into the lists that `difflib` needs.

---

## Deep Dive: The Three Key Features

### Feature 1: Working Directory Context

#### What is it?
The ability to resolve file paths relative to a configurable "working directory" instead of always using the current directory.

#### Why do we need it?

**Problem Scenario:**
Imagine an LLM working with multiple projects in a single session:
```
/home/user/
├── project-a/
│   └── src/config.py
└── project-b/
    └── src/config.py
```

If the LLM says `edit_file(path="src/config.py", ...)`, which config.py do we edit? Without working directory context, we'd always edit based on the current working directory, which might be `/home/user/`. This is ambiguous and error-prone.

**Solution:**
```python
# Explicitly specify which project
edit_file(
    path="src/config.py",
    old_string='PORT = 3000',
    new_string='PORT = 8080',
    working_dir="/home/user/project-a"  # Unambiguous!
)
```

#### How is it implemented?

The `resolve_path()` function handles this:

```python
def resolve_path(path: str, working_dir: Optional[str] = None) -> Path:
    path_obj = Path(path)

    # Step 1: Check if already absolute
    if path_obj.is_absolute():
        return path_obj  # e.g., "/home/user/file.py" → use as-is

    # Step 2: Resolve relative paths
    if working_dir:
        base = Path(working_dir)  # Use specified working dir
    else:
        base = Path.cwd()  # Fallback to current working directory

    return (base / path_obj).resolve()
```

**Key decisions:**
1. **Absolute paths are untouched**: If you pass `/home/user/file.py`, we use it exactly as-is, regardless of `working_dir`. This makes sense because absolute paths are already unambiguous.

2. **Relative paths are resolved**: If you pass `src/config.py`, we resolve it against:
   - `working_dir` if provided (explicit context)
   - Current working directory otherwise (fallback)

3. **`.resolve()` normalizes the path**: This:
   - Converts `../` and `./` to actual paths
   - Follows symlinks
   - Returns an absolute path

   Example: `Path("/home/user/project/../other").resolve()` → `/home/user/other`

#### Why this matters for LLMs:

LLMs often operate in **multi-project contexts**. A single conversation might involve:
- Reading from project A
- Writing to project B
- Comparing implementations between C and D

Without working directory context, the LLM would need to:
1. Track the current working directory mentally
2. Always use absolute paths (verbose and error-prone)
3. Use shell commands like `cd` before every file operation (inefficient)

With working directory context:
- The LLM can work with natural relative paths (`src/utils.py`)
- Each operation can specify its context explicitly
- No need for state management or directory changing

---

### Feature 2: Automatic Directory Creation

#### What is it?
When writing a file, automatically create any missing parent directories instead of throwing an error.

#### Why do we need it?

**Problem Scenario:**
An LLM wants to create a new React component:
```python
edit_file(
    path="src/components/auth/LoginForm.tsx",
    old_string='',
    new_string='export const LoginForm = ...'
)
```

If `src/components/auth/` doesn't exist, the file write will fail with:
```
FileNotFoundError: [Errno 2] No such file or directory: 'src/components/auth/LoginForm.tsx'
```

**The traditional approach:**
The LLM would need to:
1. Check if directories exist
2. Create them manually with `mkdir` commands
3. Then create the file

This requires **3 separate tool calls** and **mental state tracking**.

**The automatic approach:**
```python
# Just create the file - directories are created automatically!
edit_file(
    path="src/components/auth/LoginForm.tsx",
    old_string='',
    new_string='export const LoginForm = ...'
)
# → Automatically creates: src/ → src/components/ → src/components/auth/
```

This is **1 tool call** and **zero cognitive overhead**.

#### How is it implemented?

```python
# Get the parent directory of the target file
parent_dir = file_path.parent  # e.g., /project/src/components/auth

# Create it if it doesn't exist
if parent_dir and not parent_dir.exists():
    parent_dir.mkdir(parents=True, exist_ok=True)
    # parents=True: Create all intermediate directories (like 'mkdir -p')
    # exist_ok=True: Don't error if directory already exists (race condition safety)
```

**Key decisions:**

1. **`parents=True`**: This is like `mkdir -p` in Unix. It creates the entire directory chain.
   ```python
   # Without parents=True, you'd need to create each level separately:
   Path("src").mkdir()
   Path("src/components").mkdir()
   Path("src/components/auth").mkdir()

   # With parents=True, one call creates everything:
   Path("src/components/auth").mkdir(parents=True)
   ```

2. **`exist_ok=True`**: Prevents errors if the directory already exists. This is important because:
   - Another process might create the directory between our check and creation (race condition)
   - Idempotency: running the same operation twice doesn't error

3. **Only create if needed**: We check `not parent_dir.exists()` first to avoid unnecessary system calls.

#### Why this matters for LLMs:

**Reduces tool calls:** Instead of:
```python
# Without automatic creation (3 tool calls):
shell("mkdir -p src/components/auth")  # Tool call 1
read("src/components/auth")            # Tool call 2 (verify)
edit_file("src/components/auth/LoginForm.tsx", ...)  # Tool call 3
```

We get:
```python
# With automatic creation (1 tool call):
edit_file("src/components/auth/LoginForm.tsx", ...)  # Done!
```

**Reduces cognitive load:** The LLM doesn't need to:
- Remember to check directory existence
- Know the `mkdir -p` command
- Handle error recovery if directories are missing

**Better developer experience:** Matches human intuition - when you create a file in a nested path, you expect the tool to "just handle it."

---

### Feature 3: Differentiated Write Feedback

#### What is it?
Providing different success messages for **creating new files** vs **editing existing files**.

#### Why do we need it?

**Problem: LLMs need context awareness**

Consider these two scenarios:

**Scenario A:**
```python
edit_file(path="src/config.py", old_string='DEBUG = False', new_string='DEBUG = True')
# Response: "Success: Replaced 1 occurrence(s) in src/config.py"
```

**Scenario B:**
```python
edit_file(path="src/new-feature.py", old_string='', new_string='def new_feature(): ...')
# Response: "Success: Replaced 1 occurrence(s) in src/new-feature.py"  ❌ Confusing!
```

In Scenario B, we didn't "replace" anything - we **created** a new file! The same message for both actions is misleading and makes it harder for the LLM to track its actions.

#### How is it implemented?

```python
# Check if file exists BEFORE we start editing
is_new_file = not file_path.exists()

# ... perform the edit ...

# AFTER writing, provide context-appropriate feedback
if is_new_file:
    line_count = new_content.count('\n') + 1 if new_content else 0
    return f"Created {path} ({line_count} lines)"
else:
    # For edits, show the transformation
    old_lines = old_string.count('\n') + 1
    new_lines = new_string.count('\n') + 1
    return f"Edited {path} ({old_lines} lines → {new_lines} lines)\n\nDiff:\n{diff}"
```

**Key decisions:**

1. **Check existence early:** We determine `is_new_file` at the start, not the end. This is important because:
   - We know the intent from the beginning
   - We can skip unnecessary operations for new files (like reading content)
   - It's more efficient

2. **Different information for different actions:**
   - **Created files**: Show total line count (gives sense of file size)
   - **Edited files**: Show transformation (old lines → new lines) + diff

3. **No diff for new files:** Showing a diff for a brand new file is redundant - the entire content is "new". Just report the creation and line count.

#### Example outputs:

**Creating a new file:**
```
Created src/components/Button.tsx (45 lines)
```
Clear, concise, informative. The LLM knows:
- A new file was created (not edited)
- Where it was created
- How large it is

**Editing an existing file:**
```
Edited src/config.py (1 lines → 1 lines)

Diff:
```diff
--- a/src/config.py
+++ b/src/config.py
@@ -1,1 +1,1 @@
-DEBUG = False
+DEBUG = True
```
```

Rich feedback. The LLM knows:
- An existing file was modified (not created)
- What changed (the diff)
- The scope of the change (1 line → 1 line)

#### Why this matters for LLMs:

**Mental model alignment:** LLMs build internal representations of the codebase state. Differentiated feedback helps them:
- Track which files exist vs which are new
- Understand the scope of their changes
- Verify their intentions were executed correctly

**Error detection:** If an LLM intends to create a new file but gets "Edited" feedback, it immediately knows something went wrong (maybe the file already exists from a previous operation).

**Audit trail:** In long conversations, the LLM can look back at its tool call history and quickly understand:
- "Created config.py" → I made this file
- "Edited config.py" → I modified an existing file

**Better prompting:** The LLM can make smarter decisions:
```python
# If it sees "Created auth.py" earlier, it knows to use edit_file() next time
# If it never saw "Created db.py", it knows to create it first
```

---

## Summary: Why These Features Matter Together

These three features form a **cohesive developer experience**:

1. **Working Directory Context** → Enables multi-project workflows
2. **Automatic Directory Creation** → Reduces friction and tool calls
3. **Differentiated Feedback** → Provides clear state awareness

Together, they transform the edit tool from a simple file modifier into an **intelligent coding assistant** that:
- Understands project context
- Handles filesystem complexity automatically
- Communicates clearly about what actions were taken

This is the difference between a tool that requires **constant supervision** and one that enables **autonomous LLM coding**.
