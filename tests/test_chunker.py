from app.ingest.chunker import chunk_text


def make(n):
    return "\n".join(f"line {i}" for i in range(1, n + 1))


def test_empty_file_gives_no_chunks():
    assert chunk_text("a.py", "") == []


def test_small_file_single_chunk():
    chunks = chunk_text("a.py", make(30))
    assert len(chunks) == 1
    assert (chunks[0].start_line, chunks[0].end_line) == (1, 30)


def test_overlap_between_chunks():
    chunks = chunk_text("a.py", make(120))
    assert [(c.start_line, c.end_line) for c in chunks] == [(1, 50), (41, 90), (81, 120)]


def test_no_gaps_full_coverage():
    n = 137
    covered = set()
    for c in chunk_text("a.py", make(n)):
        covered.update(range(c.start_line, c.end_line + 1))
    assert covered == set(range(1, n + 1))


def test_text_matches_line_range():
    chunks = chunk_text("a.py", make(120))
    assert chunks[1].text.splitlines()[0] == "line 41"


def test_embed_text_prepends_path():
    c = chunk_text("src/auth.py", "x = 1")[0]
    assert c.embed_text.startswith("src/auth.py\n")