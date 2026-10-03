FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

# CPU-only torch keeps the image far smaller than the default CUDA build
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY frontend ./frontend

# bake the embedding model into the image (no download at runtime)
RUN python -c "from app.retrieval.embedder import embed; embed(['warmup'])"

ENV CHROMA_DIR=/data/chroma DB_PATH=/data/repos.db REPO_TTL_HOURS=24 MAX_REPOS=20
VOLUME /data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]