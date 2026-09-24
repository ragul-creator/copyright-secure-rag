from __future__ import annotations
import hashlib
from src.config import settings
from src.rag.embeddings import embed_text, embed_texts


class QdrantVectorStore:
    def __init__(self):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError as exc:
            raise RuntimeError("VECTOR_BACKEND=qdrant requires requirements-infra.txt") from exc
        self._models = __import__("qdrant_client.models", fromlist=["models"])
        self.client = QdrantClient(url=settings.qdrant_url)
        collections = {c.name for c in self.client.get_collections().collections}
        if settings.qdrant_collection not in collections:
            self.client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
            )

    @staticmethod
    def _point_id(tenant_id: str, chunk_id: str) -> int:
        digest = hashlib.sha256(f"{tenant_id}:{chunk_id}".encode()).digest()
        return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)

    def upsert(self, tenant_id: str, chunks: list[dict]) -> None:
        if not chunks:
            return
        PointStruct = self._models.PointStruct
        vectors = embed_texts([c["text"] for c in chunks])
        points = [
            PointStruct(
                id=self._point_id(tenant_id, chunk["chunk_id"]),
                vector=vector,
                payload={**chunk, "tenant_id": tenant_id},
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        self.client.upsert(collection_name=settings.qdrant_collection, points=points, wait=True)

    def delete_document(self, tenant_id: str, document_id: str) -> None:
        models = self._models
        selector = models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id)),
                    models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id)),
                ]
            )
        )
        self.client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=selector,
            wait=True,
        )

    def search(self, tenant_id: str, text: str, limit: int) -> list[dict]:
        models = self._models
        hits = self.client.query_points(
            collection_name=settings.qdrant_collection,
            query=embed_text(text),
            query_filter=models.Filter(
                must=[models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id))]
            ),
            limit=limit,
            with_payload=True,
        ).points
        return [{**(h.payload or {}), "score": float(h.score)} for h in hits]

    def healthcheck(self) -> bool:
        self.client.get_collections()
        return True


def get_vector_store():
    if settings.vector_backend == "qdrant":
        return QdrantVectorStore()
    return None
