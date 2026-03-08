# Tool: ls

Lists the contents of a directory, either as a flat list with metadata or as a visual tree.

## Arguments
- `path` (str, optional): The path to the directory. Defaults to `"."`.
- `max_results` (int, optional): Maximum number of results for flat listing. Defaults to `100`.
- `recurssive` (bool, optional): Whether to generate a visual tree. Defaults to `False`.

## Returns
- If `recurssive=True`: A string representing the directory tree.
- If `recurssive=False`: A dictionary with `entries` (name, type, size) and `is_truncated`.

## Example
```python
# List files
ls(path="src", recurssive=False)

# Show tree
ls(path=".", recurssive=True)
```
