from ..registry import register_tool
from utils.file_utils import (
    LsTruncatedResponse,
    validate_path,
    list_files,
    generate_tree
)

    

@register_tool
def ls(path: str = ".",max_results: int = 100,recurssive: bool = False) -> LsTruncatedResponse | str:
    """
    list directory tool used to list the contents of a directory.

    Args:
        path (str): The path to the directory to list.
        max_results (int): The maximum number of results to return.
        recurssive (bool): Whether to list the contents of the directory recursively.

    Returns:
        LsTruncatedResponse | str: A list of strings representing the contents of the directory.
        if recurssive is True, it will return a string representing the tree of the directory.
        if recurssive is False, it will return a list of strings representing the contents of the directory.
        if max_results is set, it will return a list of strings representing the contents of the directory by default it is 100.

        example:
        ls(".",recurssive=True) -> 

        .
        ├── file1
        ├── file2
        └── dir1/
            ├── file3
            └── file4

        ls(".",max_results=100,recurssive=False) -> 
        
        {"entries":[{"name":"file1","type":"file","size":100},{"name":"file2","type":"file","size":200}],"is_truncated":False}
    """
    if validate_path(path):
        if recurssive:
            return generate_tree(path)
        else:
            return list_files(path, max_results)
