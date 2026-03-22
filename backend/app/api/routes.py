"""Thin API routes for backend endpoints."""

from fastapi import APIRouter, HTTPException

from app.services.copilot_service import (
    ChatRequest,
    ChatResponse,
    HealthStatus,
    answer_question,
    get_health_status,
)
from app.services.ingestion_service import (
    IngestRequest,
    IngestResponse,
    IngestStatusResponse,
    get_ingestion_status,
    run_knowledge_base_ingestion,
)

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
def health_check() -> HealthStatus:
    """Return the current service health status."""
    return get_health_status()


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(request: ChatRequest) -> ChatResponse:
    """Answer a user question with retrieved context and citations."""
    try:
        return answer_question(request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/ingest", response_model=IngestResponse, tags=["ingest"])
def ingest(request: IngestRequest | None = None) -> IngestResponse:
    """Run knowledge base ingestion for local PDF files."""
    try:
        return run_knowledge_base_ingestion(force=request.force if request else False)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/ingest/status", response_model=IngestStatusResponse, tags=["ingest"])
def ingest_status() -> IngestStatusResponse:
    """Return the current or last ingestion status."""
    return get_ingestion_status()
