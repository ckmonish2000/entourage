# Tool: edit_file (Proposed)

Performs surgical text replacement within a file. Part of EIP-1.

## Arguments
- `path` (str): Path to the target file.
- `old_string` (str, optional): The exact literal text to be replaced.
- `new_string` (str, optional): The new text to insert.
- `replacements` (list, optional): A list of objects containing `old_string` and `new_string` for batch updates.
- `allow_multiple` (bool, optional): If true, replaces all occurrences of `old_string`. Default is `false`.

## Constraints
- By default, `old_string` must exist exactly once in the file to ensure precision.
- If `replacements` is used, each individual `old_string` must be unique unless `allow_multiple` is set.
- Recommended to use after a `read` operation to verify context.

## Example
```python
# Single edit
edit_file(
    path="config.py",
    old_string='DEBUG = False',
    new_string='DEBUG = True'
)

# Batch edit
edit_file(
    path="config.py",
    replacements=[
        {"old_string": "PORT = 8000", "new_string": "PORT = 8080"},
        {"old_string": "TIMEOUT = 30", "new_string": "TIMEOUT = 60"}
    ]
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

*   **Uniqueness**: Your Python code should first count the occurrences of `old_string`. If `count != 1`, return an error message explaining whether it was 0 (not found) or >1 (ambiguous).
*   **Atomicity**: Always try to read the whole file, perform the replacement in memory, and then write it back. This ensures that if the script crashes mid-way, you don't end up with a half-written file.
*   **Path Safety**: Never trust the `path` argument directly. Use `pathlib` to ensure the path is inside your project directory and hasn't been "hacked" using `../` (directory traversal).
*   **Encoding**: Always specify `encoding="utf-8"` when reading/writing to avoid issues with special characters.

### 3. Python Guidance for Junior Developers

#### Use `TypedDict` for Argument Validation
In Python, you can use `TypedDict` from the `typing` module to define the structure of your tool's arguments. This helps with editor autocompletion and static analysis (like `mypy`).

```python
from typing import TypedDict, List, Optional

class Replacement(TypedDict):
    old_string: str
    new_string: str

class EditFileArguments(TypedDict):
    path: str
    old_string: Optional[str]
    new_string: Optional[str]
    replacements: Optional[List[Replacement]]
    allow_multiple: Optional[bool]
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

#### The "Surgical" Logic
Here is the conceptual flow for your Python tool:
1.  **Resolve** the path and check if it exists.
2.  **Read** the entire file content.
3.  **Check** `content.count(old_string)`.
    *   If `0`: Return "String not found. Did you check the file content first?"
    *   If `>1`: Return "Multiple matches found. Please provide more context to make the match unique."
4.  **Replace**: `new_content = content.replace(old_string, new_string, 1)`.
5.  **Write**: `file_path.write_text(new_content, encoding="utf-8")`.
6.  **Return** a success message (maybe even a small diff).

### 4. Why not line numbers?
Line numbers are "brittle." If another process (or your previous tool call) added a line at the top of the file, every line number below it is now wrong. Literal string matching with context (before/after lines) is much more robust against "drift."

### 5. Handling Large Files (The "10GB Log" Problem)

In reality, an LLM should **never** be performing surgical edits on a 10GB log file. That's a job for stream processors like `sed`, `awk`, or specialized logging tools. However, for "large-ish" source files (several MBs), here is how to stay efficient:

*   **Chunking (Advanced)**: You can read the file in chunks (e.g., 64KB at a time). To handle the case where `old_string` is split between two chunks, you overlap the chunks by the length of `old_string`.
*   **Memory Mapping (`mmap`)**: Python's `mmap` module allows you to "map" a file into the process's virtual memory. The OS then handles loading only the parts you are actually reading. This is extremely fast and memory-efficient for large files.
*   **Tool Scope**: In your implementation, you might want to add a safeguard:
    ```python
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
    if file_path.stat().st_size > MAX_FILE_SIZE:
        return "Error: File too large for surgical edit. Use specialized tools."
    ```

### 6. Solving Ambiguity: The "Context" Strategy

You asked: *If there are multiple occurrences, how does the tool decide?*

The answer is: **It doesn't.** It should fail and ask for help. This is exactly how Claude Code works.

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

### 7. Response Format: Providing Context to the LLM

The response should not just say "Success." It needs to provide "visual" confirmation so the LLM knows its change was applied correctly within the file's structure.

#### Success Response
Provide a small snippet showing the new code with 2-3 lines of surrounding context. This acts as a "mini-read" and saves the LLM from having to call `read` again.

**Example:**
```text
Successfully replaced 1 occurrence in 'config.py'.

Context:
---
    PORT = 8080
    DEBUG = True  # <--- Changed this line
    LOG_LEVEL = "INFO"
---
```

#### Error Response
If it fails, be extremely specific. Don't just say "Error."

*   **Not Found**: "Error: `old_string` not found in `path`. Please ensure you have the exact indentation and spelling. Tip: Use `read` to see the current file state."
*   **Multiple Matches**: "Error: Found 3 matches for `old_string`. Ambiguous edit. Please provide more context lines to make the match unique."
*   **File Issues**: "Error: File is too large (15MB). Surgical edits are limited to 10MB."

By giving the LLM the "Why," you enable it to self-correct in the next turn.

### 8. Batching & Bulk Updates

You asked: *What if the model has to perform 20 updates? Should it call the tool 20 times?*

There are two ways to handle this:

#### A. The "Batch List" Approach (Recommended for Different Edits)
Instead of 20 tool calls (which is slow and expensive), the tool should accept a `replacements` list.
*   **Logic**: Your Python code should iterate through the list, verify each `old_string` is unique, and apply them one by one in memory before writing the file once.
*   **Failure**: If *any* of the 20 strings are missing or ambiguous, the **entire batch should fail**. This prevents the file from being left in a "half-edited" state.

#### B. The `allow_multiple` Flag (For Identical Occurrences)
If you need to change `v1` to `v2` in 20 places where the code is identical:
*   Add an `allow_multiple: bool` parameter.
*   If `true`, use `content.replace(old, new)` (without the limit of 1).
*   **Warning**: This is dangerous! If the LLM didn't realize `v1` was also part of a sensitive variable name elsewhere, it will break the code. Usually, it is better for the LLM to use the "Batch List" with unique context for each location.

### 9. Why Batching is Efficient
1.  **Reduced Latency**: Only one network round-trip between the LLM and your tool.
2.  **Atomicity**: You read the file once, apply all changes, and write once. This reduces the chance of another process interfering.
3.  **Cost**: LLM providers charge per tool call (in terms of overhead/tokens). Batching 20 edits into 1 call is significantly cheaper.

---

## Draft Implementation (Blueprint)

This is a conceptual Python implementation for you to follow.

```python
from typing import List, Optional, TypedDict
from pathlib import Path

class Replacement(TypedDict):
    old_string: str
    new_string: str

def edit_file(
    path: str,
    old_string: Optional[str] = None,
    new_string: Optional[str] = None,
    replacements: Optional[List[Replacement]] = None,
    allow_multiple: bool = False
) -> str:
    # 1. Path Safety
    file_path = Path(path).resolve()
    if not file_path.exists():
        return f"Error: File '{path}' not found."

    # 2. Normalize inputs into a single batch
    work_list: List[Replacement] = replacements or []
    if old_string and new_string:
        work_list.append({"old_string": old_string, "new_string": new_string})

    if not work_list:
        return "Error: No replacements provided."

    try:
        # 3. Read content
        content = file_path.read_text(encoding="utf-8")
        new_content = content

        # 4. Process Batch (All-or-Nothing)
        for item in work_list:
            old = item["old_string"]
            new = item["new_string"]
            
            count = content.count(old)
            
            if count == 0:
                return f"Error: '{old}' not found. Batch aborted."
            if count > 1 and not allow_multiple:
                return f"Error: '{old}' found {count} times. Need more context. Batch aborted."

            new_content = new_content.replace(old, new, -1 if allow_multiple else 1)

        # 5. Atomic Write
        file_path.write_text(new_content, encoding="utf-8")
        
        return f"Success: Applied {len(work_list)} replacements to {path}."

    except Exception as e:
        return f"System Error: {str(e)}"
```
