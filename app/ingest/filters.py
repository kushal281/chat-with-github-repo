import os
from pathlib import Path

from app.config import settings

ALLOWED_EXT = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp",
    ".h", ".sh", ".md", ".json", ".yaml", ".yml", ".toml",
}
IGNORED_DIRS = {
    ".git", "node_modules", "dist", "build", "venv", ".venv",
    "__pycache__", ".next", "target",
}
IGNORED_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Cargo.lock",
}


def iter_code_files(root: Path):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_symlink() or name in IGNORED_FILES:
                continue
            if path.suffix.lower() not in ALLOWED_EXT:
                continue
            if path.stat().st_size > settings.max_file_kb * 1024:
                continue
            yield path
            count += 1
            if count >= settings.max_files:
                return