from dataclasses import dataclass
from pathlib import Path

CHUNK_LINES = 50
OVERLAP = 10


@dataclass
class Chunk:
    path: str
    start_line: int  # 1-indexed, inclusive
    end_line: int    # inclusive
    text: str

    @property
    def embed_text(self) -> str:
        # path carries semantic signal (e.g. "auth/login.py") the body may lack
        return f"{self.path}\n{self.text}"


def chunk_text(path: str, content: str, size: int = CHUNK_LINES, overlap: int = OVERLAP) -> list[Chunk]:
    lines = content.splitlines()
    if not lines:
        return []
    step = size - overlap
    chunks = []
    for start in range(0, len(lines), step):
        end = min(start + size, len(lines))
        chunks.append(Chunk(path, start + 1, end, "\n".join(lines[start:end])))
        if end == len(lines):
            break
    return chunks


def chunk_file(root: Path, file: Path) -> list[Chunk]:
    content = file.read_text(encoding="utf-8", errors="ignore")
    rel = file.relative_to(root).as_posix()  # forward slashes, needed for GitHub links later
    return chunk_text(rel, content)