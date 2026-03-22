"""Helpers for assembling grounded chat context from prompts, memory, and retrieval."""

from __future__ import annotations

from dataclasses import dataclass

from app.memory.store import MemoryTurn
from app.rag.retrieval import RetrievedChunk
from app.services.prompt_service import PromptBundle


@dataclass(frozen=True)
class ContextBlock:
    """Structured context payload assembled from retrieved documents."""

    question: str
    system_prompt: str
    rules_prompt: str
    fewshots_prompt: str
    memory_text: str
    context_text: str
    citations: list[str]


def build_chat_context(
    *,
    question: str,
    chunks: list[RetrievedChunk],
    prompts: PromptBundle,
    memory_turns: list[MemoryTurn],
) -> ContextBlock:
    """Combine prompts, memory, and retrieved chunks into a chat context."""
    context_sections: list[str] = []
    citations: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        citation = _format_citation(chunk.source, chunk.page_number)
        citations.append(citation)
        context_sections.append(
            f"[{index}] Source: {citation}\n"
            f"Chunk ID: {chunk.chunk_id}\n"
            f"Content: {chunk.text}"
        )

    return ContextBlock(
        question=question.strip(),
        system_prompt=prompts.system,
        rules_prompt=prompts.rules,
        fewshots_prompt=prompts.fewshots,
        memory_text=_format_memory(memory_turns),
        context_text="\n\n".join(context_sections),
        citations=citations,
    )


def _format_citation(source: str, page_number: int) -> str:
    """Format a user-facing citation label."""
    return f"{source} (page {page_number})"


def render_prompt_context(context_block: ContextBlock) -> str:
    """Render the final prompt context in a fixed, auditable order."""
    parts = [
        "System Prompt:",
        context_block.system_prompt or "(empty)",
        "",
        "Rules Prompt:",
        context_block.rules_prompt or "(empty)",
        "",
        "Few-Shot Examples:",
        context_block.fewshots_prompt or "(empty)",
        "",
        "Conversation Memory:",
        context_block.memory_text or "(empty)",
        "",
        "Retrieved Context:",
        context_block.context_text or "(empty)",
        "",
        "Current Question:",
        context_block.question,
    ]
    return "\n".join(parts).strip()


def _format_memory(memory_turns: list[MemoryTurn]) -> str:
    if not memory_turns:
        return ""
    return "\n".join(f"{turn.role}: {turn.content}" for turn in memory_turns)
