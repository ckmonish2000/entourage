"""File system utility functions for agent tools."""
import mimetypes
from pathlib import Path
from typing import TypedDict


class LsResponse(TypedDict):
    """Response structure for individual file/directory entries."""
    name: str
    type: str
    size: int


class LsTruncatedResponse(TypedDict):
    """Response structure for list operations with truncation support."""
    entries: list[LsResponse]
    is_truncated: bool


def validate_path(path: str = ".") -> bool:
    """
    Validate that a path exists and is a directory.

    Args:
        path: Path to validate (defaults to current directory)

    Returns:
        True if path is valid

    Raises:
        FileNotFoundError: If path doesn't exist
        NotADirectoryError: If path is not a directory
    """
    path = Path(path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    return True


def list_files(path: str = ".", max_results: int = 100) -> LsTruncatedResponse:
    """
    List files recursively in a directory with result limit.

    Args:
        path: Directory path to list
        max_results: Maximum number of entries to return

    Returns:
        Dictionary with entries list and truncation flag
    """
    all_entries = []
    is_truncated = False

    for p in Path(path).rglob("*"):
        if len(all_entries) >= max_results:
            is_truncated = True
            break
        all_entries.append({
            "name": p.name,
            "type": "dir" if p.is_dir() else "file",
            "size": p.stat().st_size
        })

    return {"entries": all_entries, "is_truncated": is_truncated}


def generate_tree(path: str = ".", prefix: str = "") -> str:
    """
    Generate a tree representation of directory structure.

    Args:
        path: Directory path to generate tree for
        prefix: Prefix for tree formatting (used in recursion)

    Returns:
        String representation of directory tree
    """
    path = Path(path).expanduser().resolve()
    entries = sorted(
        path.iterdir(),
        key=lambda p: (not p.is_dir(), p.name.lower()),
        reverse=True
    )

    tree = ""

    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        tree += prefix + connector + entry.name

        if entry.is_dir():
            tree += "/\n"
            extension = "    " if index == len(entries) - 1 else "│   "
            tree += generate_tree(entry, prefix + extension)
        else:
            tree += "\n"

    return tree


def get_file_type(file_path: str) -> str:
    """
    Determine the type of a file (text, image, pdf, notebook, or unknown).

    Args:
        file_path: Path to the file

    Returns:
        String indicating the file type
    """
    print(mimetypes.guess_type(file_path))
    mime_type, _ = mimetypes.guess_type(file_path)

    if mime_type is None:
        # Check for Jupyter notebook based on file extension
        if file_path.endswith('.ipynb'):
            return 'notebook'
        return 'unknown'

    if mime_type.startswith('text/'):
        return 'text'
    elif mime_type.startswith('image/'):
        return 'image'
    elif mime_type.startswith('video/'):
        return 'video'
    elif mime_type.startswith('audio/'):
        return 'audio'
    elif mime_type == 'application/pdf':
        return 'pdf'
    elif mime_type == 'application/x-ipynb+json':
        return 'notebook'
    else:
        return 'unknown'
