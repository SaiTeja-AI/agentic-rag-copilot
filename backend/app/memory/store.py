"""In-memory conversation store for prototype chat history."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryTurn:
    """A single chat turn kept in conversation memory."""

    role: str
    content: str


class InMemoryConversationStore:
    """Store bounded chat history in process memory."""

    def __init__(self) -> None:
        self._store: dict[str, list[MemoryTurn]] = {}

    def get_recent_turns(self, conversation_id: str, turn_limit: int) -> list[MemoryTurn]:
        """Return the most recent bounded turns for a conversation."""
        turns = self._store.get(conversation_id, [])
        if turn_limit <= 0:
            return []
        return turns[-(turn_limit * 2) :]

    def append_turn(self, conversation_id: str, role: str, content: str) -> None:
        """Append a user or assistant turn to the conversation."""
        self._store.setdefault(conversation_id, []).append(MemoryTurn(role=role, content=content))


conversation_store = InMemoryConversationStore()
