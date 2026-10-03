import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimit:
    """Sliding-window limit per client IP, kept in memory (one worker)."""

    def __init__(self, limit: int, window_s: int):
        self.limit = limit
        self.window_s = window_s
        self.hits: dict[str, deque] = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        # behind a proxy the first x-forwarded-for entry is the real client
        fwd = request.headers.get("x-forwarded-for")
        ip = fwd.split(",")[0].strip() if fwd else request.client.host
        now = time.monotonic()
        q = self.hits[ip]
        while q and now - q[0] > self.window_s:
            q.popleft()
        if len(q) >= self.limit:
            raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
        q.append(now)


index_limit = RateLimit(limit=10, window_s=3600)  # new repos per IP per hour
chat_limit = RateLimit(limit=20, window_s=600)    # questions per IP per 10 minutes