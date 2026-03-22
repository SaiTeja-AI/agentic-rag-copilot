"""LLM service boundary and deterministic fallback generation."""

from __future__ import annotations

from dataclasses import dataclass
import time

from app.rag.retrieval import RetrievedChunk


@dataclass(frozen=True)
class LLMGenerationResult:
    """Result returned from the answer generation boundary."""

    answer: str
    provider: str
    model: str
    used_fallback: bool
    latency_ms: int


def generate_grounded_answer(
    *,
    provider: str,
    model_name: str,
    question: str,
    context: str,
    chunks: list[RetrievedChunk],
    max_output_tokens: int,
) -> LLMGenerationResult:
    """Generate a grounded answer through the configured model boundary.

    The prototype uses a deterministic fallback generator. This keeps the API
    contract stable while the provider integration remains optional.
    """
    started = time.perf_counter()
    answer = _build_fallback_answer(question=question, chunks=chunks, max_chars=max_output_tokens * 4)
    latency_ms = int((time.perf_counter() - started) * 1000)
    return LLMGenerationResult(
        answer=answer,
        provider=provider,
        model=model_name,
        used_fallback=True,
        latency_ms=latency_ms,
    )


def _build_fallback_answer(
    *,
    question: str,
    chunks: list[RetrievedChunk],
    max_chars: int,
) -> str:
    """Compose a grounded answer directly from retrieved evidence."""
    if not chunks:
        return (
            "I could not find enough supporting evidence in the knowledge base to answer "
            f"the question: {question}"
        )

    lines = [f"Answer to: {question}", ""]
    lines.append("Based on the retrieved knowledge base content:")
    for index, chunk in enumerate(chunks[:3], start=1):
        excerpt = " ".join(chunk.text.split())
        if len(excerpt) > 280:
            excerpt = f"{excerpt[:277].rstrip()}..."
        lines.append(f"{index}. {excerpt} [{chunk.source}, page {chunk.page_number}]")

    answer = "\n".join(lines)
    if len(answer) <= max_chars:
        return answer
    return f"{answer[: max_chars - 3].rstrip()}..."
