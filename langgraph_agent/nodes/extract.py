from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pdfplumber

from langgraph_agent.state import PipelineState, SentenceItem

# Minimum / maximum token counts for a sentence to be worth keeping
_MIN_WORDS = 5
_MAX_WORDS = 250

# Patterns that indicate non-sentence noise (page numbers, headers, footers)
_NOISE = re.compile(
    r"^(page\s+\d+|\d+\s*$|www\.|http|©|\bait\b\s*\d{4}|_{3,}|-{3,})",
    re.IGNORECASE,
)


def _split_sentences(raw: str) -> List[str]:
    """Naive sentence splitter adequate for policy PDF text."""
    # Normalise whitespace
    raw = re.sub(r"[ \t]+", " ", raw)
    # Split on period / semicolon followed by whitespace + capital letter
    parts = re.split(r"(?<=[.;])\s+(?=[A-Z])", raw)
    return [p.strip() for p in parts if p.strip()]


def _is_noise(text: str) -> bool:
    words = text.split()
    if len(words) < _MIN_WORDS or len(words) > _MAX_WORDS:
        return True
    if _NOISE.match(text):
        return True
    if text.isupper() and len(words) < 8:   # likely a section header in all-caps
        return True
    return False


def extract_node(state: PipelineState) -> PipelineState:
    pdf_dir = Path(state["pdf_dir"])
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    sentences: List[SentenceItem] = []
    errors: List[str] = []

    for pdf_path in pdf_files:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    raw_text = page.extract_text() or ""
                    for sent in _split_sentences(raw_text):
                        if not _is_noise(sent):
                            sentences.append(
                                SentenceItem(
                                    text=sent,
                                    page=page_num,
                                    source=pdf_path.name,
                                )
                            )
        except Exception as exc:
            errors.append(f"extract: failed to read {pdf_path.name}: {exc}")

    return {
        **state,
        "extracted_sentences": sentences,
        "total_sentences": len(sentences),
        "current_step": "extract",
        "errors": errors,
    }
