from pathlib import Path
from ..registry import register_tool

@register_tool
def ls(path: str = ".") -> list[str]:
    """
    list directory tool used to list the contents of a directory.

    Args:
        path (str): The path to the directory to list.

    Returns:
        list[str]: A list of strings representing the contents of the directory.
    """
    path = Path(path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")
    
    return [str(p) for p in Path(path).iterdir()]
