import asyncio
from ..registry import register_tool
from ..types import ShellResponse

@register_tool
async def run_shell_command(command: str) -> ShellResponse:
    """
    This function call is used execute shell command and return the output.
    
    Args:
        command (str): The command to run example: "docker ps" or "ls -la"
    
    Returns:
        ShellResponse: A dictionary containing the output of the command.
        the response might look like this: 
        {
            "type": "success",
            "stdout": "Hello World",
            "stderr": "",
            "returncode": 0
        }
    """
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    type = "success" if process.returncode == 0 else "error"

    print({
        "type": type,
        "command": command,
        "stdout": stdout.decode(),
        "stderr": stderr.decode(),
        "returncode": process.returncode
    })
    return {
        "type": type,
        "command": command,
        "stdout": stdout.decode(),
        "stderr": stderr.decode(),
        "returncode": process.returncode
    }
