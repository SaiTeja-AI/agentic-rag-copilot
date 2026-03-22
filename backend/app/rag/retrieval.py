"""Retrieval workflows for querying Chroma-backed document chunks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from app.rag.ingestion import DEFAULT_COLLECTION_NAME

DEFAULT_TOP_K = 5


@dataclass(frozen=True)
class RetrievedChunk:
    """A document chunk returned from the vector store."""

    chunk_id: str
    text: str
    source: str
    document_hash: str
    page_number: int
    distance: float


class ChromaRetriever:
    """Embed a query and retrieve the nearest chunks from Chroma."""

    def __init__(
        self,
        persist_directory: Path,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        collection_name: str = DEFAULT_COLLECTION_NAME,
        tenant_id: str = "local",
    ) -> None:
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model_name
        self.collection_name = collection_name
        self.tenant_id = tenant_id
        self._embedding_model: SentenceTransformer | None = None

    def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        """Return the top matching chunks for a query."""
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")

        collection = self._get_collection()
        query_embedding = self._embed_query(normalized_query)
        where = _build_where_clause(tenant_id=self.tenant_id, filters=filters)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
            where=where,
        )
        return _build_retrieved_chunks(results)

    def _get_collection(self):
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(self.persist_directory))
        return client.get_or_create_collection(name=self.collection_name)

    def _embed_query(self, query: str) -> list[float]:
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        model = self._embedding_model
        embedding = model.encode(query, normalize_embeddings=True)
        return embedding.tolist()


def _build_retrieved_chunks(results: dict[str, Any]) -> list[RetrievedChunk]:
    ids = results.get("ids", [[]])
    documents = results.get("documents", [[]])
    metadatas = results.get("metadatas", [[]])
    distances = results.get("distances", [[]])

    retrieved_chunks: list[RetrievedChunk] = []
    for index, chunk_id in enumerate(ids[0] if ids else []):
        metadata = metadatas[0][index] if metadatas and metadatas[0] else {}
        retrieved_chunks.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                text=documents[0][index],
                source=str(metadata.get("source", "")),
                document_hash=str(metadata.get("document_hash", "")),
                page_number=int(metadata.get("page_number", 0)),
                distance=float(distances[0][index]),
            )
        )

    return retrieved_chunks


def retrieve_document_chunks(
    query: str,
    persist_directory: Path,
    top_k: int = DEFAULT_TOP_K,
    embedding_model_name: str = "all-MiniLM-L6-v2",
    collection_name: str = DEFAULT_COLLECTION_NAME,
    tenant_id: str = "local",
    filters: dict[str, Any] | None = None,
) -> list[RetrievedChunk]:
    """Convenience entry point for local Chroma retrieval."""
    retriever = ChromaRetriever(
        persist_directory=persist_directory,
        embedding_model_name=embedding_model_name,
        collection_name=collection_name,
        tenant_id=tenant_id,
    )
    return retriever.retrieve(query=query, top_k=top_k, filters=filters)


def _build_where_clause(tenant_id: str, filters: dict[str, Any] | None) -> dict[str, Any]:
    clauses: list[dict[str, Any]] = [{"tenant_id": tenant_id}]
    for key, value in (filters or {}).items():
        if value is None or value == "":
            continue
        clauses.append({key: value})
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}
