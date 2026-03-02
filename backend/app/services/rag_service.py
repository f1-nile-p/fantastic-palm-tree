import logging
import uuid
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)

_VECTOR_SIZE = 384
_ITEMS_COLLECTION = "items"
_UOMS_COLLECTION = "uoms"

_encoder: SentenceTransformer | None = None


def _get_encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
    return _encoder


def _get_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url)


def init_collections() -> None:
    """Create Qdrant collections if they don't already exist."""
    client = _get_client()
    for name in (_ITEMS_COLLECTION, _UOMS_COLLECTION):
        existing = [c.name for c in client.get_collections().collections]
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=qmodels.VectorParams(
                    size=_VECTOR_SIZE,
                    distance=qmodels.Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s", name)
        else:
            logger.info("Qdrant collection already exists: %s", name)


def index_items(items: list) -> None:
    """Encode item descriptions and upsert into the items collection."""
    if not items:
        return
    encoder = _get_encoder()
    client = _get_client()

    descriptions = [item.description for item in items]
    vectors = encoder.encode(descriptions, show_progress_bar=False).tolist()

    points = [
        qmodels.PointStruct(
            id=str(item.id),
            vector=vec,
            payload={
                "code": item.code,
                "description": item.description,
                "unit_of_measure": item.unit_of_measure,
                "unit_price": item.unit_price,
                "category": item.category,
            },
        )
        for item, vec in zip(items, vectors)
    ]
    client.upsert(collection_name=_ITEMS_COLLECTION, points=points)
    logger.info("Indexed %d items in Qdrant", len(points))


def index_uoms(uoms: list) -> None:
    """Encode UOM descriptions/aliases and upsert into the uoms collection."""
    if not uoms:
        return
    encoder = _get_encoder()
    client = _get_client()

    texts = []
    for uom in uoms:
        aliases = uom.aliases or []
        combined = " ".join([uom.description] + aliases)
        texts.append(combined)

    vectors = encoder.encode(texts, show_progress_bar=False).tolist()

    points = [
        qmodels.PointStruct(
            id=str(uom.id),
            vector=vec,
            payload={
                "code": uom.code,
                "description": uom.description,
                "aliases": uom.aliases or [],
            },
        )
        for uom, vec in zip(uoms, vectors)
    ]
    client.upsert(collection_name=_UOMS_COLLECTION, points=points)
    logger.info("Indexed %d UOMs in Qdrant", len(points))


def match_item(description: str, limit: int = 3) -> list[dict]:
    """Search Qdrant for items similar to the given description."""
    encoder = _get_encoder()
    client = _get_client()

    vector = encoder.encode([description], show_progress_bar=False)[0].tolist()
    results = client.search(
        collection_name=_ITEMS_COLLECTION,
        query_vector=vector,
        limit=limit,
    )
    return [
        {
            "id": hit.id,
            "code": hit.payload.get("code"),
            "description": hit.payload.get("description"),
            "score": hit.score,
        }
        for hit in results
    ]


def match_uom(uom_raw: str, limit: int = 3) -> list[dict]:
    """Search Qdrant for UOMs similar to the given raw string."""
    encoder = _get_encoder()
    client = _get_client()

    vector = encoder.encode([uom_raw], show_progress_bar=False)[0].tolist()
    results = client.search(
        collection_name=_UOMS_COLLECTION,
        query_vector=vector,
        limit=limit,
    )
    return [
        {
            "id": hit.id,
            "code": hit.payload.get("code"),
            "description": hit.payload.get("description"),
            "score": hit.score,
        }
        for hit in results
    ]
