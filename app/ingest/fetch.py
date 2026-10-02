import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from app.config import settings

GITHUB_URL = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


def parse_repo_url(url: str) -> tuple[str, str]:
    m = GITHUB_URL.match(url.strip())
    if not m:
        raise ValueError("Only https://github.com/{owner}/{repo} URLs are allowed")
    return m.group(1), m.group(2)


def clone_repo(url: str) -> Path:
    owner, repo = parse_repo_url(url)
    dest = Path(tempfile.mkdtemp(prefix="repochat_")) / repo
    subprocess.run(
        ["git", "clone", "--depth", "1", f"https://github.com/{owner}/{repo}.git", str(dest)],
        check=True,
        capture_output=True,
        timeout=settings.clone_timeout_s,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    return dest


def _make_writable(func, path, _exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def cleanup(path: Path) -> None:
    shutil.rmtree(path.parent, onexc=_make_writable)