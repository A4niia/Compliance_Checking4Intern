from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from langgraph_agent.state import PipelineState

PROJECT_ROOT = Path(__file__).parent.parent.parent


def report_node(state: PipelineState) -> PipelineState:
    source = state["source"]
    output_dir = PROJECT_ROOT / "output" / source
    output_dir.mkdir(parents=True, exist_ok=True)

    val = state.get("validation_results", {})
    shapes = state.get("shacl_shapes", [])

    report = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "pipeline_version": "2.0-langgraph",
        "summary": {
            "sentences_extracted":  state.get("total_sentences", 0),
            "candidates_prefiltered": len(state.get("candidates", [])),
            "rules_classified":     len(state.get("rules", [])),
            "fol_formulas_ok":      len(state.get("fol_formulas", [])),
            "fol_formulas_failed":  len(state.get("fol_failed", [])),
            "shacl_shapes_total":   len(shapes),
            "shacl_shapes_valid":   sum(1 for s in shapes if s["syntax_valid"]),
            "shacl_shapes_fol_mediated": sum(1 for s in shapes if s["generation_method"] == "fol_mediated"),
            "shacl_shapes_direct_nl":    sum(1 for s in shapes if s["generation_method"] == "direct_nl"),
            "validation_conforms":  state.get("conforms", False),
            "violations":           val.get("violation_count", 0),
            "total_errors":         len(state.get("errors", [])),
        },
        "rule_type_distribution": _count_by_type(state.get("rules", [])),
        "errors": state.get("errors", []),
    }

    # Save main report
    report_path = output_dir / "pipeline_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # Save intermediate outputs
    _save(output_dir / "classified_rules.json",  state.get("rules", []))
    _save(output_dir / "fol_formulas.json",       state.get("fol_formulas", []))

    # Print summary to console
    s = report["summary"]
    print(f"\n{'='*60}")
    print(f"  PIPELINE SUMMARY — {source.upper()}")
    print(f"{'='*60}")
    print(f"  Sentences extracted    : {s['sentences_extracted']}")
    print(f"  Pre-filter candidates  : {s['candidates_prefiltered']}")
    print(f"  Rules classified       : {s['rules_classified']}")
    print(f"  FOL formulas ok/fail   : {s['fol_formulas_ok']} / {s['fol_formulas_failed']}")
    print(f"  SHACL shapes generated : {s['shacl_shapes_total']} ({s['shacl_shapes_valid']} valid)")
    print(f"    - FOL-mediated       : {s['shacl_shapes_fol_mediated']}")
    print(f"    - Direct NL fallback : {s['shacl_shapes_direct_nl']}")
    print(f"  Validation conforms    : {s['validation_conforms']}")
    print(f"  Violations found       : {s['violations']}")
    if s["total_errors"]:
        print(f"  Pipeline errors        : {s['total_errors']}")
    print(f"{'='*60}")
    print(f"  Output dir: {output_dir}")
    print(f"{'='*60}\n")

    return {
        **state,
        "report": report,
        "current_step": "report",
    }


def _save(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _count_by_type(rules: list) -> dict:
    dist: dict[str, int] = {}
    for r in rules:
        t = r.get("rule_type", "unknown")
        dist[t] = dist.get(t, 0) + 1
    return dist
