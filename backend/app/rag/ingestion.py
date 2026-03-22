"""Knowledge-base ingestion pipeline for PDF documents."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
DEFAULT_COLLECTION_NAME = "knowledge_base"


@dataclass(frozen=True)
class DocumentChunk:
    """A chunk of text extracted from a source document."""

    chunk_id: str
    source: str
    document_hash: str
    page_number: int
    chunk_index: int
    tenant_id: str
    text: str


@dataclass(frozen=True)
class IngestionSummary:
    """Summary returned after ingesting the local knowledge base."""

    documents_processed: int
    chunks_created: int
    skipped_documents: int
    deleted_chunks: int
    collection_name: str
    persist_directory: str


class PDFKnowledgeBaseIngestor:
    """Load PDFs from disk, chunk them, embed them, and store them in Chroma."""

    def __init__(
        self,
        knowledge_base_dir: Path,
        persist_directory: Path,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        collection_name: str = DEFAULT_COLLECTION_NAME,
        tenant_id: str = "local",
        force: bool = False,
    ) -> None:
        self.knowledge_base_dir = knowledge_base_dir
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model_name
        self.collection_name = collection_name
        self.tenant_id = tenant_id
        self.force = force
        self._embedding_model: SentenceTransformer | None = None

    def ingest(self) -> IngestionSummary:
        """Run the full ingestion pipeline for all PDFs in the knowledge base."""
        pdf_paths = sorted(self.knowledge_base_dir.rglob("*.pdf"))
        collection = self._get_collection()
        existing_sources = _load_existing_sources(collection, tenant_id=self.tenant_id)

        all_chunks: list[DocumentChunk] = []
        skipped_documents = 0
        for pdf_path in pdf_paths:
            source = str(pdf_path.relative_to(self.knowledge_base_dir))
            document_hash = compute_file_hash(pdf_path)
            if not self.force and existing_sources.get(source) == document_hash:
                skipped_documents += 1
                continue
            if source in existing_sources:
                collection.delete(
                    where={"$and": [{"source": source}, {"tenant_id": self.tenant_id}]}
                )
            all_chunks.extend(self._load_pdf_chunks(pdf_path=pdf_path, document_hash=document_hash))

        deleted_chunks = _cleanup_stale_sources(
            collection=collection,
            active_sources={str(path.relative_to(self.knowledge_base_dir)) for path in pdf_paths},
            tenant_id=self.tenant_id,
        )

        if all_chunks:
            embeddings = self._embed_chunks(all_chunks)
            collection.upsert(
                ids=[chunk.chunk_id for chunk in all_chunks],
                documents=[chunk.text for chunk in all_chunks],
                embeddings=embeddings,
                metadatas=[
                    {
                        "source": chunk.source,
                        "document_hash": chunk.document_hash,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                        "tenant_id": chunk.tenant_id,
                    }
                    for chunk in all_chunks
                ],
            )

        return IngestionSummary(
            documents_processed=len(pdf_paths),
            chunks_created=len(all_chunks),
            skipped_documents=skipped_documents,
            deleted_chunks=deleted_chunks,
            collection_name=self.collection_name,
            persist_directory=str(self.persist_directory),
        )

    def _get_collection(self):
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(self.persist_directory))
        return client.get_or_create_collection(name=self.collection_name)

    def _load_pdf_chunks(self, pdf_path: Path, document_hash: str) -> list[DocumentChunk]:
        reader = PdfReader(str(pdf_path))
        chunks: list[DocumentChunk] = []
        source = str(pdf_path.relative_to(self.knowledge_base_dir))

        for page_index, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            for chunk_index, chunk_text in enumerate(chunk_text_content(page_text)):
                if not chunk_text.strip():
                    continue

                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document_hash}-{page_index}-{chunk_index}",
                        source=source,
                        document_hash=document_hash,
                        page_number=page_index,
                        chunk_index=chunk_index,
                        tenant_id=self.tenant_id,
                        text=chunk_text,
                    )
                )

        return chunks

    def _embed_chunks(self, chunks: list[DocumentChunk]) -> list[list[float]]:
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        model = self._embedding_model
        embeddings = model.encode([chunk.text for chunk in chunks], normalize_embeddings=True)
        return [embedding.tolist() for embedding in embeddings]


def chunk_text_content(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping character chunks."""
    normalized_text = " ".join(text.split())
    if not normalized_text:
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    step = chunk_size - chunk_overlap

    while start < len(normalized_text):
        end = min(start + chunk_size, len(normalized_text))
        chunks.append(normalized_text[start:end].strip())
        if end >= len(normalized_text):
            break
        start += step

    return chunks


def ingest_knowledge_base(
    knowledge_base_dir: Path,
    persist_directory: Path,
    embedding_model_name: str = "all-MiniLM-L6-v2",
    collection_name: str = DEFAULT_COLLECTION_NAME,
    tenant_id: str = "local",
    force: bool = False,
) -> IngestionSummary:
    """Convenience entry point for local knowledge-base ingestion."""
    ingestor = PDFKnowledgeBaseIngestor(
        knowledge_base_dir=knowledge_base_dir,
        persist_directory=persist_directory,
        embedding_model_name=embedding_model_name,
        collection_name=collection_name,
        tenant_id=tenant_id,
        force=force,
    )
    return ingestor.ingest()


def compute_file_hash(path: Path) -> str:
    """Compute a stable content hash for a source file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_existing_sources(collection: Any, tenant_id: str) -> dict[str, str]:
    results = collection.get(where={"tenant_id": tenant_id}, include=["metadatas"])
    existing_sources: dict[str, str] = {}
    for metadata in results.get("metadatas", []):
        source = str(metadata.get("source", ""))
        document_hash = str(metadata.get("document_hash", ""))
        if source:
            existing_sources[source] = document_hash
    return existing_sources


def _cleanup_stale_sources(collection: Any, active_sources: set[str], tenant_id: str) -> int:
    results = collection.get(where={"tenant_id": tenant_id}, include=["metadatas"])
    stale_ids: list[str] = []
    ids = results.get("ids", [])
    metadatas = results.get("metadatas", [])
    for index, metadata in enumerate(metadatas):
        source = str(metadata.get("source", ""))
        if source and source not in active_sources:
            stale_ids.append(ids[index])
    if stale_ids:
        collection.delete(ids=stale_ids)
    return len(stale_ids)
