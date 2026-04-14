"""Retrieve file from give path"""

import os
from pathlib import Path

def list_files(root: Path) -> dict:
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        for file in filenames:
            result.append(os.path.join(dirpath, file))
    return result

