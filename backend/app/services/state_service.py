"""Shared in-process state for ingestion status and lightweight runtime info."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class IngestionState:
    """Track the current or last ingestion run status."""

    status: str = "idle"
    job_id: str = ""
    documents_processed: int = 0
    chunks_created: int = 0
    skipped_documents: int = 0
    deleted_chunks: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str | None = None


class RuntimeState:
    """Simple in-process runtime state store."""

    def __init__(self) -> None:
        self.ingestion = IngestionState()

    def start_ingestion(self) -> str:
        job_id = uuid.uuid4().hex
        self.ingestion = IngestionState(
            status="running",
            job_id=job_id,
            started_at=datetime.utcnow(),
            message="Knowledge base ingestion is running.",
        )
        return job_id


runtime_state = RuntimeState()
