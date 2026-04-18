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
from langgraph_agent.state import PipelineState, RuleItem, SHACLShape

_cache = get_cache()
_llm = get_llm()

_SHACL_PREFIXES = """\
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix ait:  <http://example.org/ait-policy#> .
"""

_DIRECT_PROMPT = """\
Translate this policy rule DIRECTLY into a valid SHACL NodeShape in Turtle syntax.

Rule type: {rule_type}
Rule text: "{text}"

Requirements:
- Use these prefixes: ait: <http://example.org/ait-policy#>  sh: <http://www.w3.org/ns/shacl#>
- The shape MUST be a sh:NodeShape with sh:targetClass, sh:severity, sh:property
- Obligations  → sh:minCount 1  and sh:severity sh:Violation
- Prohibitions → sh:maxCount 0  and sh:severity sh:Violation
- Permissions  → sh:severity sh:Info

Shape name: ait:{shape_id}Shape

Return ONLY the Turtle block for this shape. No explanations, no markdown fences."""


def _validate_turtle(text: str) -> bool:
    try:
        from rdflib import Graph
        g = Graph()
        g.parse(data=_SHACL_PREFIXES + "\n" + text, format="turtle")
        return True
    except Exception:
        return False


def direct_shacl_node(state: PipelineState) -> PipelineState:
    failed_rules: List[RuleItem] = state.get("fol_failed", [])
    existing_shapes: List[SHACLShape] = list(state.get("shacl_shapes", []))
    model = DEFAULT_MODEL
    errors: List[str] = []

    new_shapes: List[SHACLShape] = []

    for rule in failed_rules:
        text = rule["text"]
        shape_id = rule["rule_id"].replace("-", "_")

        cached = _cache.get(text, model, "direct_shacl")
        if cached:
            turtle = cached.get("turtle", "")
            valid = cached.get("valid", False)
        else:
            try:
                prompt = _DIRECT_PROMPT.format(
                    text=text,
                    rule_type=rule["rule_type"],
                    shape_id=shape_id,
                )
                response = _llm.invoke([HumanMessage(content=prompt)])
                turtle = response.content.strip()
                # Strip markdown fences if model wrapped them
                turtle = re.sub(r"^```[a-z]*\n?", "", turtle, flags=re.MULTILINE)
                turtle = re.sub(r"```$", "", turtle, flags=re.MULTILINE).strip()
                valid = _validate_turtle(turtle)
                _cache.set(text, model, "direct_shacl", {"turtle": turtle, "valid": valid})
            except Exception as exc:
                errors.append(f"direct_shacl[{rule['rule_id']}]: {exc}")
                turtle = ""
                valid = False

        if turtle:
            new_shapes.append(SHACLShape(
                rule_id=rule["rule_id"],
                turtle_text=turtle,
                target_class="Unknown",  # harder to infer from raw LLM output
                deontic_type=rule["rule_type"],
                syntax_valid=valid,
                generation_method="direct_nl",
            ))

    return {
        **state,
        "shacl_shapes": existing_shapes + new_shapes,
        "current_step": "direct_shacl",
        "errors": errors,
    }
