from __future__ import annotations

import re
from pathlib import Path
from typing import List

from langgraph_agent.state import FOLItem, PipelineState, SHACLShape

PROJECT_ROOT = Path(__file__).parent.parent.parent

_TTL_PREFIXES = """\
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh:     <http://www.w3.org/ns/shacl#> .
@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .
@prefix ait:    <http://example.org/ait-policy#> .
@prefix deontic: <http://example.org/deontic#> .

"""

# ── Subject → target class inference ───────────────────────────────────────
_SUBJECT_MAP = [
    (r"postgraduate|doctoral|phd|master", "PostgraduateStudent"),
    (r"graduate|alumni",                  "Graduate"),
    (r"resident|tenant",                  "Resident"),
    (r"sponsor",                          "Sponsor"),
    (r"advisor|adviser|supervisor",       "Faculty"),
    (r"faculty|professor|instructor|lecturer|invigilator", "Faculty"),
    (r"employee|staff",                   "Employee"),
    (r"student|learner",                  "Student"),
    (r"committee|board|tribunal",         "Committee"),
    (r"director|dean|registrar",          "Administrator"),
]


def _infer_target_class(text: str) -> str:
    t = text.lower()
    for pattern, cls in _SUBJECT_MAP:
        if re.search(pattern, t):
            return cls
    return "Person"


def _slugify(text: str, max_words: int = 4) -> str:
    """Turn rule text into a camelCase property-path slug."""
    words = re.sub(r"[^a-zA-Z0-9 ]", "", text).split()
    return "".join(w.capitalize() for w in words[:max_words])


def _property_path(fol: FOLItem) -> str:
    """Derive a SHACL property path from the FOL formula."""
    # Try to extract predicate name from deontic_formula e.g. O(payFee(x))
    m = re.search(r"[OPF]\(([a-zA-Z_]+)", fol["deontic_formula"])
    if m:
        raw = m.group(1)
        # Convert snake_case or PascalCase to camelCase
        parts = re.sub(r"([A-Z])", r" \1", raw).strip().split()
        return parts[0][0].lower() + parts[0][1:] + "".join(p.capitalize() for p in parts[1:])
    # Fallback: slug from rule text
    return _slugify(fol["text"])


_DEONTIC_CONSTRAINT = {
    "obligation":  ("sh:minCount 1 ;", "sh:Violation"),
    "prohibition": ("sh:maxCount 0 ;", "sh:Violation"),
    "permission":  ("sh:minCount 0 ;", "sh:Info"),
}


def _fol_to_turtle(fol: FOLItem) -> tuple[str, str, bool]:
    """
    Returns (turtle_text, target_class, syntax_valid).
    """
    shape_id = fol["rule_id"].replace("-", "_") + "Shape"
    target_class = _infer_target_class(fol["text"])
    deontic_type = fol["deontic_type"]
    constraint, severity = _DEONTIC_CONSTRAINT.get(
        deontic_type, ("sh:minCount 1 ;", "sh:Violation")
    )
    prop_path = _property_path(fol)
    message = fol["text"].replace('"', "'")[:200]

    turtle = (
        f"# Rule: {fol['rule_id']} | {deontic_type.upper()}\n"
        f"# FOL: {fol['deontic_formula']}\n"
        f"ait:{shape_id} a sh:NodeShape ;\n"
        f"    sh:targetClass ait:{target_class} ;\n"
        f"    sh:severity {severity} ;\n"
        f"    sh:property [\n"
        f"        sh:path ait:{prop_path} ;\n"
        f"        {constraint}\n"
        f"        sh:message \"{message}\" ;\n"
        f"    ] .\n"
    )
    return turtle, target_class, True


def shacl_node(state: PipelineState) -> PipelineState:
    fol_formulas: List[FOLItem] = state["fol_formulas"]
    existing_shapes: List[SHACLShape] = list(state.get("shacl_shapes", []))
    errors: List[str] = []

    new_shapes: List[SHACLShape] = []
    ttl_blocks: List[str] = [_TTL_PREFIXES]

    for fol in fol_formulas:
        try:
            turtle, target_class, valid = _fol_to_turtle(fol)
            ttl_blocks.append(turtle + "\n")
            new_shapes.append(SHACLShape(
                rule_id=fol["rule_id"],
                turtle_text=turtle,
                target_class=target_class,
                deontic_type=fol["deontic_type"],
                syntax_valid=valid,
                generation_method="fol_mediated",
            ))
        except Exception as exc:
            errors.append(f"shacl[{fol['rule_id']}]: {exc}")

    # Write combined TTL to output/
    output_dir = PROJECT_ROOT / "output" / state["source"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "shapes_generated.ttl")
    Path(output_path).write_text("".join(ttl_blocks), encoding="utf-8")

    return {
        **state,
        "shacl_shapes": existing_shapes + new_shapes,
        "shacl_output_path": output_path,
        "current_step": "shacl",
        "errors": errors,
    }
