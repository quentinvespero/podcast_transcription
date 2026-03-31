from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.config import EMBEDDING_DIMENSION, QDRANT_COLLECTION, QDRANT_HOST, QDRANT_PORT


def _get_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def _ensure_collection(client: QdrantClient) -> None:
    """Create the Qdrant collection if it doesn't exist yet."""
    existing = {c.name for c in client.get_collections().collections}
    if QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )


def insert_segments(
    segment_ids: list[int],
    vectors: list[list[float]],
    payloads: list[dict],
) -> None:
    """
    Upsert segment embeddings into Qdrant.

    Each point uses the SQLite segment id as its Qdrant id so the two stores
    stay linked without needing a separate mapping table.

    Args:
        segment_ids: SQLite segment row IDs (used as Qdrant point IDs).
        vectors:     Embedding vectors, one per segment.
        payloads:    Metadata dicts stored alongside each vector
                     (source title, URL, timestamps, text).
    """
    client = _get_client()
    _ensure_collection(client)

    points = [
        PointStruct(id=seg_id, vector=vector, payload=payload)
        for seg_id, vector, payload in zip(segment_ids, vectors, payloads)
    ]
    client.upsert(collection_name=QDRANT_COLLECTION, points=points)


def search_semantic(query_vector: list[float], limit: int = 10) -> list[dict]:
    """
    Semantic similarity search: find the segments closest to the query vector.

    Returns a list of result dicts, each containing:
      - score (float): cosine similarity (higher = more similar)
      - all payload fields: source_title, source_url, start_time, end_time, text
    """
    client = _get_client()
    hits = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=limit,
    )
    return [{"score": hit.score, **hit.payload} for hit in hits]
