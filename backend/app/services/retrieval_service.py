"""Service-layer entry point for document chunk retrieval."""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.rag.retrieval import RetrievedChunk, retrieve_document_chunks


def retrieve_knowledge_base_chunks(
    query: str,
    top_k: int | None = None,
    filters: dict[str, Any] | None = None,
) -> list[RetrievedChunk]:
    """Return the top matching knowledge-base chunks for a query."""
    settings = get_settings()
    return retrieve_document_chunks(
        query=query,
        persist_directory=settings.chroma_dir,
        top_k=top_k or settings.retrieval_top_k,
        embedding_model_name=settings.embedding_model_name,
        collection_name=settings.collection_name,
        tenant_id=settings.default_tenant_id,
        filters=filters,
    )
