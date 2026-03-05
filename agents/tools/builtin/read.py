from pathlib import Path
# from ..registry import register_tool

# @register_tool
def read(path: str, encoding: str = "utf-8", start_line: int = 1, max_lines: int = 10) -> str:
    """
    Read the contents of a file.

    Args:
        path (str): The path to the file to read.
        encoding (str): The encoding of the file.
        start_line (int): The starting line number.
        max_lines (int): The maximum number of lines to read.

   Returns:
       str: The contents of the file.
   """
    path = Path(path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if not path.is_file():
        raise IsADirectoryError(f"Path is not a file: {path}")
    
    with open(path, "r", encoding=encoding) as f:
        lines = []
        for index, line in enumerate(f,start=1):
            if index >= start_line and index < start_line + max_lines:
                lines.append(f"{index:4d} | {line}")
        return "\n".join(lines)
        

if __name__ == "__main__":
    print(read('./read.py',encoding='utf-8'))