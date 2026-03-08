# Tool: run_shell_command

Executes a shell command in the local environment and returns its output.

## Arguments
- `command` (str): The shell command to execute (e.g., `"npm test"`, `"ls -la"`).

## Returns
A dictionary containing:
- `type`: `"success"` or `"error"`.
- `command`: The command that was executed.
- `stdout`: Standard output.
- `stderr`: Standard error.
- `returncode`: The process exit code.

## Example
```python
run_shell_command(command="pytest tests/test_agent.py")
```
