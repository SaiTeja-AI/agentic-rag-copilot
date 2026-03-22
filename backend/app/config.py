"""Application settings for the Agentic RAG Copilot backend."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    project_root: Path
    knowledge_base_dir: Path
    chroma_dir: Path
    prompt_dir: Path
    collection_name: str
    embedding_model_name: str
    llm_provider: str
    llm_model_name: str
    llm_timeout_seconds: float
    llm_max_output_tokens: int
    retrieval_top_k: int
    memory_turn_limit: int
    default_tenant_id: str


def get_settings() -> Settings:
    """Build settings from environment variables with local-first defaults."""
    project_root = Path(__file__).resolve().parents[2]
    return Settings(
        project_root=project_root,
        knowledge_base_dir=project_root / "data" / "knowledge_base",
        chroma_dir=project_root / "data" / "chroma",
        prompt_dir=project_root / "prompts",
        collection_name=os.getenv("COLLECTION_NAME", "knowledge_base"),
        embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"),
        llm_provider=os.getenv("LLM_PROVIDER", "fallback"),
        llm_model_name=os.getenv("LLM_MODEL_NAME", "grounded-fallback"),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "20")),
        llm_max_output_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "512")),
        retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "5")),
        memory_turn_limit=int(os.getenv("MEMORY_TURN_LIMIT", "4")),
        default_tenant_id=os.getenv("DEFAULT_TENANT_ID", "local"),
    )
