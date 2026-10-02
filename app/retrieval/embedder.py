from sentence_transformers import SentenceTransformer

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts, batch_size=32, normalize_embeddings=True).tolist()