import asyncio
from ..registry import register_tool
from ..types import ShellResponse

async def run_shell_command(command: str, cwd: str = None, timeout_seconds: int = 300) -> ShellResponse:
    """Execute a shell command asynchronously with timeout and error handling.

    Runs arbitrary shell commands in a subprocess with configurable working directory
    and timeout controls. Captures both stdout and stderr streams, returning structured
    response with execution status and output.

    Args:
        command: Shell command string to execute. Required, cannot be empty.
                 Can include pipes, redirects, and other shell operators.
        cwd: Working directory path for command execution. Optional.
             If None, uses the current process working directory.
        timeout_seconds: Maximum execution time in seconds. Defaults to 300 (5 minutes).
                        Command is forcefully terminated if timeout is exceeded.

    Returns:
        ShellResponse: Dictionary containing:
            - type: "success" if returncode == 0, else "error"
            - command: The executed command string (echo)
            - stdout: Standard output captured, truncated to 2000 chars
            - stderr: Standard error captured, truncated to 2000 chars
            - returncode: Process exit code (0 = success, -1 = internal error)

    Behavior:
        - Empty command returns immediate error without execution
        - Output streams are UTF-8 decoded and truncated to 2000 characters
        - Timeout triggers process kill and returns error with timeout message
        - Any subprocess exceptions return error response with exception details
        - Non-zero exit codes are captured and returned as "error" type

    Examples:
        >>> await run_shell_command("ls -la", cwd="/tmp")
        {'type': 'success', 'stdout': 'file1\nfile2\n', 'stderr': '', 'returncode': 0}

        >>> await run_shell_command("invalid_cmd")
        {'type': 'error', 'stdout': '', 'stderr': 'command not found', 'returncode': 127}

        >>> await run_shell_command("sleep 10", timeout_seconds=2)
        {'type': 'error', 'stderr': 'Command timed out after 2 seconds', 'returncode': -1}

    Security Notes:
        - Executes commands with full shell interpretation (shell=True)
        - No input sanitization - caller must validate command safety
        - Inherits environment variables from parent process
        - Should not be exposed to untrusted input without validation
    """
    try:
        if not command:
            return {
                "type": "error",
                "command": command,
                "stdout": "",
                "stderr": "Command is required",
            "returncode": 1
        }

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout_seconds
        )
        

        type = "success" if process.returncode == 0 else "error"

        return {
            "type": type,
            "command": command,
            "stdout": stdout.decode()[:2000],
            "stderr": stderr.decode()[:2000],
            "returncode": process.returncode
        }

    except asyncio.TimeoutError:
            process.kill()
            await process.communicate()

            return {
                "type": "error",
                "command": command,
                "stdout": "",
                "stderr": f"Command timed out after {timeout_seconds} seconds",
                "returncode": -1
            }
    except Exception as e:
        return {
            "type": "error",
            "command": command,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }