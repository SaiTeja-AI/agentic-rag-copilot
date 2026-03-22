"""Service-layer helpers for backend endpoints."""

from __future__ import annotations

from pydantic import BaseModel

from app.config import get_settings
from app.context.builder import build_chat_context, render_prompt_context
from app.memory.store import conversation_store
from app.services.llm_service import generate_grounded_answer
from app.services.prompt_service import load_prompt_bundle
from app.services.retrieval_service import retrieve_knowledge_base_chunks


class HealthStatus(BaseModel):
    """Structured response returned by the health endpoint."""

    status: str
    service: str


def get_health_status() -> HealthStatus:
    """Build the backend health response."""
    return HealthStatus(status="ok", service="agentic-rag-copilot-backend")


class ChatRequest(BaseModel):
    """User input for a grounded chat request."""

    question: str
    conversation_id: str = "default"
    debug: bool = False


class Citation(BaseModel):
    """Citation returned alongside the grounded answer."""

    chunk_id: str
    source: str
    document_hash: str
    page_number: int


class ChatResponse(BaseModel):
    """Grounded answer response built from retrieved knowledge-base chunks."""

    answer: str
    citations: list[Citation]
    context: str | None = None
    provider: str
    model: str
    used_fallback: bool


def answer_question(request: ChatRequest) -> ChatResponse:
    """Retrieve supporting chunks, build context, and return a grounded answer."""
    settings = get_settings()
    question = request.question.strip()
    if not question:
        raise ValueError("question must not be empty")

    prompts = load_prompt_bundle(settings.prompt_dir)
    memory_turns = conversation_store.get_recent_turns(
        request.conversation_id,
        turn_limit=settings.memory_turn_limit,
    )
    retrieved_chunks = retrieve_knowledge_base_chunks(question, top_k=settings.retrieval_top_k)
    context_block = build_chat_context(
        question=question,
        chunks=retrieved_chunks,
        prompts=prompts,
        memory_turns=memory_turns,
    )
    rendered_context = render_prompt_context(context_block)
    generation = generate_grounded_answer(
        provider=settings.llm_provider,
        model_name=settings.llm_model_name,
        question=question,
        context=rendered_context,
        chunks=retrieved_chunks,
        max_output_tokens=settings.llm_max_output_tokens,
    )

    citations = [
        Citation(
            chunk_id=chunk.chunk_id,
            source=chunk.source,
            document_hash=chunk.document_hash,
            page_number=chunk.page_number,
        )
        for chunk in retrieved_chunks
    ]
    conversation_store.append_turn(request.conversation_id, role="user", content=question)
    conversation_store.append_turn(
        request.conversation_id,
        role="assistant",
        content=generation.answer,
    )
    return ChatResponse(
        answer=generation.answer,
        citations=citations,
        context=rendered_context if request.debug else None,
        provider=generation.provider,
        model=generation.model,
        used_fallback=generation.used_fallback,
    )
