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
from langgraph_agent.state import FOLItem, PipelineState, RuleItem

_cache = get_cache()
_llm = get_llm()

_FOL_PROMPT = """\
You are a formal logician specialising in deontic logic for institutional policy.

Convert the policy rule below into a First-Order Logic (FOL) formula using \
deontic operators:
  O(φ) — Obligation: the subject MUST perform φ
  P(φ) — Permission: the subject MAY perform φ
  F(φ) — Prohibition (Forbidden): the subject MUST NOT perform φ

Rule type: {rule_type}
Rule text: "{text}"

Output ONLY a JSON object (no markdown):
{{
  "deontic_type": "obligation"/"permission"/"prohibition",
  "deontic_formula": "O/P/F(predicate(subject))",
  "fol_expansion": "∀x (Subject(x) ∧ Condition(x) → O/P/F(Action(x)))",
  "predicates": {{"subject": "...", "action": "...", "condition": "..."}},
  "shacl_hint": "brief hint for SHACL translation"
}}"""


def _parse_fol(raw: str) -> dict | None:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group())
        # Validate minimum required fields
        if "deontic_formula" in data and "fol_expansion" in data:
            return data
        return None
    except json.JSONDecodeError:
        return None


def fol_node(state: PipelineState) -> PipelineState:
    rules: List[RuleItem] = state["rules"]
    model = DEFAULT_MODEL
    errors: List[str] = []

    fol_formulas: List[FOLItem] = []
    fol_failed: List[RuleItem] = []

    for rule in rules:
        text = rule["text"]
        rule_type = rule["rule_type"]

        # --- cache check ---
        cached = _cache.get(text, model, "fol_generation",
                            extra_params={"rule_type": rule_type})
        if cached:
            parsed = cached
        else:
            try:
                prompt = _FOL_PROMPT.format(text=text, rule_type=rule_type)
                response = _llm.invoke([HumanMessage(content=prompt)])
                parsed = _parse_fol(response.content)
                if parsed:
                    _cache.set(text, model, "fol_generation", parsed,
                               extra_params={"rule_type": rule_type})
            except Exception as exc:
                errors.append(f"fol[{rule['rule_id']}]: {exc}")
                parsed = None

        if parsed:
            fol_formulas.append(FOLItem(
                rule_id=rule["rule_id"],
                text=text,
                deontic_type=parsed.get("deontic_type", rule_type),
                deontic_formula=parsed.get("deontic_formula", ""),
                fol_expansion=parsed.get("fol_expansion", ""),
                parse_success=True,
            ))
        else:
            fol_failed.append(rule)

    return {
        **state,
        "fol_formulas": fol_formulas,
        "fol_failed": fol_failed,
        "current_step": "fol",
        "errors": errors,
    }
