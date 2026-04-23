from pathlib import Path

def develop_journal_home() -> Path:
    p = Path.cwd() / ".broad"
    
    if not p.exists() or not p.is_dir():
        _create_folder_recur(p)
    
    return p

def _create_folder_recur(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def ensure_folder(path: Path):
    if not path.exists() or not path.is_dir():
        _create_folder_recur(path)