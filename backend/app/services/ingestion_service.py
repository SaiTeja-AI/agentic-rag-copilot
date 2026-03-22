"""Service-layer entry point for RAG knowledge-base ingestion."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel

from app.config import get_settings
from app.rag.ingestion import IngestionSummary, ingest_knowledge_base
from app.services.state_service import runtime_state


class IngestRequest(BaseModel):
    """Request body for ingestion."""

    force: bool = False


class IngestResponse(BaseModel):
    """Response returned when ingestion completes."""

    status: str
    job_id: str
    message: str
    documents_processed: int
    chunks_created: int
    skipped_documents: int
    deleted_chunks: int


class IngestStatusResponse(BaseModel):
    """Current or last ingestion status."""

    status: str
    job_id: str
    documents_processed: int
    chunks_created: int
    skipped_documents: int
    deleted_chunks: int
    started_at: str | None
    finished_at: str | None
    message: str | None


def run_knowledge_base_ingestion(force: bool = False) -> IngestResponse:
    """Ingest PDF documents from the local knowledge base into Chroma."""
    settings = get_settings()
    job_id = runtime_state.start_ingestion()
    try:
        summary = ingest_knowledge_base(
            knowledge_base_dir=settings.knowledge_base_dir,
            persist_directory=settings.chroma_dir,
            embedding_model_name=settings.embedding_model_name,
            collection_name=settings.collection_name,
            tenant_id=settings.default_tenant_id,
            force=force,
        )
        runtime_state.ingestion.status = "completed"
        runtime_state.ingestion.documents_processed = summary.documents_processed
        runtime_state.ingestion.chunks_created = summary.chunks_created
        runtime_state.ingestion.skipped_documents = summary.skipped_documents
        runtime_state.ingestion.deleted_chunks = summary.deleted_chunks
        runtime_state.ingestion.finished_at = datetime.utcnow()
        runtime_state.ingestion.message = "Knowledge base ingestion completed."
        return _build_response(job_id=job_id, summary=summary)
    except Exception:
        runtime_state.ingestion.status = "failed"
        runtime_state.ingestion.finished_at = datetime.utcnow()
        raise


def get_ingestion_status() -> IngestStatusResponse:
    """Return the current or last ingestion state."""
    state = runtime_state.ingestion
    return IngestStatusResponse(
        status=state.status,
        job_id=state.job_id,
        documents_processed=state.documents_processed,
        chunks_created=state.chunks_created,
        skipped_documents=state.skipped_documents,
        deleted_chunks=state.deleted_chunks,
        started_at=state.started_at.isoformat() if state.started_at else None,
        finished_at=state.finished_at.isoformat() if state.finished_at else None,
        message=state.message,
    )


def _build_response(job_id: str, summary: IngestionSummary) -> IngestResponse:
    return IngestResponse(
        status="completed",
        job_id=job_id,
        message="Knowledge base ingestion completed.",
        documents_processed=summary.documents_processed,
        chunks_created=summary.chunks_created,
        skipped_documents=summary.skipped_documents,
        deleted_chunks=summary.deleted_chunks,
    )
