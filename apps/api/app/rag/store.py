"""Replaceable vector store.

Two backends ship today and both implement the same protocol, so swapping in
Qdrant/Weaviate/pinecone later means adding one class and one registry entry.

- `portable`: embeddings are JSON in `document_chunks.embedding`; cosine similarity
  is computed in Python. Works on any database, including SQLite in tests.
- `pgvector`: the same rows, but similarity is computed inside PostgreSQL using the
  native `vector` column maintained by migration 0003. Requires the pgvector
  extension; falls back to `portable` when the extension is absent.
"""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentChunk


@dataclass(frozen=True, slots=True)
class Match:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    page: int
    content: str
    score: float


@runtime_checkable
class VectorStore(Protocol):
    name: str

    def add(self, db: Session, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None: ...

    def search(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        query_vector: list[float],
        limit: int,
        document_ids: list[uuid.UUID] | None = None,
    ) -> list[Match]: ...


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class PortableVectorStore:
    name = "portable"

    def add(self, db: Session, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        for chunk, vector in zip(chunks, vectors, strict=False):
            chunk.embedding = json.dumps(vector)
            db.add(chunk)

    def search(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        query_vector: list[float],
        limit: int,
        document_ids: list[uuid.UUID] | None = None,
    ) -> list[Match]:
        statement = (
            select(DocumentChunk, Document.title)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(DocumentChunk.user_id == user_id, DocumentChunk.embedding.is_not(None))
        )
        if document_ids:
            statement = statement.where(DocumentChunk.document_id.in_(document_ids))

        scored: list[Match] = []
        for chunk, title in db.execute(statement).all():
            try:
                vector = json.loads(chunk.embedding or "[]")
            except json.JSONDecodeError:
                continue
            scored.append(
                Match(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=title,
                    page=chunk.page,
                    content=chunk.content,
                    score=_cosine(query_vector, vector),
                )
            )
        scored.sort(key=lambda match: match.score, reverse=True)
        return scored[:limit]


class PgVectorStore:
    """PostgreSQL + pgvector. Degrades to the portable store when unavailable."""

    name = "pgvector"

    def __init__(self) -> None:
        self._fallback = PortableVectorStore()

    @staticmethod
    def _available(db: Session) -> bool:
        if db.bind is None or db.bind.dialect.name != "postgresql":
            return False
        try:
            return bool(
                db.execute(
                    text("select 1 from pg_extension where extname = 'vector'")
                ).scalar()
            )
        except Exception:  # noqa: BLE001 - any failure means "use the fallback"
            return False

    def add(self, db: Session, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        self._fallback.add(db, chunks, vectors)
        if not self._available(db):
            return
        db.flush()
        for chunk, vector in zip(chunks, vectors, strict=False):
            db.execute(
                text(
                    "update document_chunks set embedding_vec = cast(:vec as vector) "
                    "where id = :id"
                ),
                {"vec": json.dumps(vector), "id": str(chunk.id)},
            )

    def search(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        query_vector: list[float],
        limit: int,
        document_ids: list[uuid.UUID] | None = None,
    ) -> list[Match]:
        if not self._available(db):
            return self._fallback.search(
                db,
                user_id=user_id,
                query_vector=query_vector,
                limit=limit,
                document_ids=document_ids,
            )
        filter_sql = ""
        params: dict[str, object] = {
            "user_id": str(user_id),
            "vec": json.dumps(query_vector),
            "limit": limit,
        }
        if document_ids:
            filter_sql = " and c.document_id = any(cast(:doc_ids as uuid[]))"
            params["doc_ids"] = [str(value) for value in document_ids]

        rows = db.execute(
            text(
                "select c.id, c.document_id, d.title, c.page, c.content, "
                "1 - (c.embedding_vec <=> cast(:vec as vector)) as score "
                "from document_chunks c join documents d on d.id = c.document_id "
                "where c.user_id = cast(:user_id as uuid) and c.embedding_vec is not null"
                + filter_sql
                + " order by c.embedding_vec <=> cast(:vec as vector) limit :limit"
            ),
            params,
        ).all()
        return [
            Match(
                chunk_id=row[0],
                document_id=row[1],
                document_title=row[2],
                page=row[3],
                content=row[4],
                score=float(row[5]),
            )
            for row in rows
        ]


_BACKENDS: dict[str, type[VectorStore]] = {
    "portable": PortableVectorStore,
    "pgvector": PgVectorStore,
}


def get_vector_store() -> VectorStore:
    backend = settings.vector_backend.strip().lower()
    factory = _BACKENDS.get(backend, PortableVectorStore)
    return factory()
