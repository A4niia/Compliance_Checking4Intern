from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.llm_cache import get_cache

from langchain_core.messages import HumanMessage

from langgraph_agent.llm import DEFAULT_MODEL, get_llm
from langgraph_agent.state import PipelineState, RuleItem, SentenceItem

_cache = get_cache()
_llm = get_llm()

CONFIDENCE_HIGH = 0.6
CONFIDENCE_LOW = 0.4

_CLASSIFY_PROMPT = """\
You are a legal policy analyst specialising in institutional policy documents.

Classify whether the sentence below is a POLICY RULE — a deontic statement that \
creates a binding obligation, grants a permission, or imposes a prohibition.

Context hints:
- Deontic strength: {deontic_strength}
- Speech act: {speech_act}
- Section: {section}

Sentence:
"{text}"

Respond with ONLY a JSON object (no markdown, no explanation):
{{"is_rule": true/false, \
"rule_type": "obligation"/"permission"/"prohibition"/"none", \
"confidence": 0.0-1.0, \
"reasoning": "one concise sentence"}}"""


def _build_prompt(item: SentenceItem, hint: dict) -> str:
    return _CLASSIFY_PROMPT.format(
        text=item["text"],
        deontic_strength=hint.get("deontic_strength", "unknown"),
        speech_act=hint.get("speech_act", "unknown"),
        section=hint.get("section_context", "unknown"),
    )


def _parse_response(raw: str) -> dict:
    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if not match:
        return {"is_rule": False, "rule_type": "none", "confidence": 0.0,
                "reasoning": "parse_error"}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {"is_rule": False, "rule_type": "none", "confidence": 0.0,
                "reasoning": "json_decode_error"}


def classify_node(state: PipelineState) -> PipelineState:
    candidates: List[SentenceItem] = state["candidates"]
    model = DEFAULT_MODEL
    errors: List[str] = []

    rules: List[RuleItem] = []
    uncertain: List[RuleItem] = []

    # Gather prefilter hints if available (prefilter stores them in candidates)
    # If not available, use empty dict — classify still works without hints
    for i, item in enumerate(candidates):
        text = item["text"]
        hint = {}  # prefilter hints (populated if attached to item)

        # --- cache check ---
        cached = _cache.get(text, model, "classification")
        if cached:
            result = cached
        else:
            try:
                prompt = _build_prompt(item, hint)
                response = _llm.invoke([HumanMessage(content=prompt)])
                result = _parse_response(response.content)
                _cache.set(text, model, "classification", result)
            except Exception as exc:
                errors.append(f"classify[{i}]: {exc}")
                result = {"is_rule": False, "rule_type": "none",
                          "confidence": 0.0, "reasoning": str(exc)}

        if not result.get("is_rule"):
            continue

        confidence = float(result.get("confidence", 0.5))
        rule_id = f"AIT-{i:04d}"

        rule = RuleItem(
            rule_id=rule_id,
            text=text,
            source_document=item["source"],
            rule_type=result.get("rule_type", "obligation"),
            confidence=confidence,
            prefilter_strength=hint.get("deontic_strength", "unknown"),
            section_context=hint.get("section_context", ""),
        )

        if confidence >= CONFIDENCE_HIGH:
            rules.append(rule)
        elif confidence >= CONFIDENCE_LOW:
            uncertain.append(rule)
        # below CONFIDENCE_LOW → discard

    return {
        **state,
        "rules": rules,
        "uncertain_rules": uncertain,
        "current_step": "classify",
        "errors": errors,
    }
