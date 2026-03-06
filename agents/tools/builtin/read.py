from pathlib import Path
from itertools import islice
from utils.file_utils import validate_path
from agents.core.config import MAX_LINE_LENGTH
# from ..registry import register_tool



# @register_tool
def read(path: str, encoding: str = "utf-8", offset: int = 1, limit: int = 2000) -> str:
    """
    Read the contents of a file.

    Args:
        path (str): The path to the file to read.
        encoding (str): The encoding of the file.
        offset (int): The starting line number.
        limit (int): The maximum number of lines to read.

   Returns:
       str: The contents of the file.
   """
    if validate_path(path):
        # file_type = get_file_type(path)
        # print(file_type)
        with open(path, "r", encoding=encoding) as f:
            lines = []

            for _ in range(offset-1):
                next(f,None)
            
            for index, line in enumerate(islice(f,limit),start=offset):
                truncated_line = line[:MAX_LINE_LENGTH]
                if len(line) > MAX_LINE_LENGTH:
                    truncated_line += "..."
                lines.append(f"{index:4d} | {truncated_line}")
            return "\n".join(lines)
        
