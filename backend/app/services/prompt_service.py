"""Prompt-loading helpers for context assembly."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptBundle:
    """Prompt texts used during answer generation."""

    system: str
    rules: str
    fewshots: str


def load_prompt_bundle(prompt_dir: Path) -> PromptBundle:
    """Load prompt files from disk with empty-string fallback."""
    return PromptBundle(
        system=_read_text(prompt_dir / "system.md"),
        rules=_read_text(prompt_dir / "rules.md"),
        fewshots=_read_text(prompt_dir / "fewshots.md"),
    )


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()
