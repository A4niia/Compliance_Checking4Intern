#!/usr/bin/env python3
"""
PolicyChecker - LangGraph Pipeline CLI

Usage:
    python -m langgraph_agent.run --source ait
    python -m langgraph_agent.run --source ait --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from langgraph_agent.graph import build_graph
from langgraph_agent.state import PipelineState

SOURCES = {
    "ait": {
        "name": "AIT - Asian Institute of Technology",
        "pdf_dir": str(PROJECT_ROOT / "institutional_policy" / "AIT"),
    },
}


def _initial_state(source: str) -> PipelineState:
    cfg = SOURCES[source]
    return PipelineState(
        source=source,
        pdf_dir=cfg["pdf_dir"],
        extracted_sentences=[],
        total_sentences=0,
        candidates=[],
        rules=[],
        uncertain_rules=[],
        fol_formulas=[],
        fol_failed=[],
        shacl_shapes=[],
        shacl_output_path="",
        validation_results={},
        conforms=False,
        report={},
        current_step="init",
        errors=[],
    )


def run(source: str, verbose: bool = False) -> dict:
    graph = build_graph()
    state = _initial_state(source)

    print(f"\n{'='*60}")
    print(f"PolicyChecker - {SOURCES[source]['name']}")
    print(f"{'='*60}\n")

    for step in graph.stream(state):
        node_name = list(step.keys())[0]
        node_state = step[node_name]
        current = node_state.get("current_step", node_name)

        STEP_LABELS = {
            "extract":      "Step 1 - PDF Extraction",
            "prefilter":    "Step 2a - Heuristic Pre-filter",
            "classify":     "Step 2b - LLM Classification",
            "reclassify":   "Step 2c - Second-Opinion Reclassification",
            "fol":          "Step 3 - FOL Formalization",
            "shacl":        "Step 4a - SHACL Generation (FOL-mediated)",
            "direct_shacl": "Step 4b - SHACL Generation (Direct NL fallback)",
            "validate":     "Step 5 - SHACL Validation",
            "report":       "Step 6 - Report",
        }
        label = STEP_LABELS.get(current, current)
        print(f"  >> {label}")

        if verbose:
            # Show lightweight per-step stats
            stats = {
                "sentences":  len(node_state.get("extracted_sentences", [])),
                "candidates": len(node_state.get("candidates", [])),
                "rules":      len(node_state.get("rules", [])),
                "uncertain":  len(node_state.get("uncertain_rules", [])),
                "fol_ok":     len(node_state.get("fol_formulas", [])),
                "fol_fail":   len(node_state.get("fol_failed", [])),
                "shapes":     len(node_state.get("shacl_shapes", [])),
                "errors":     len(node_state.get("errors", [])),
            }
            # Only show non-zero entries
            active = {k: v for k, v in stats.items() if v}
            if active:
                print(f"     {active}")

        if node_state.get("errors"):
            for err in node_state["errors"]:
                print(f"  [WARN] {err}", file=sys.stderr)

    # Grab final state from last step
    final_state = node_state  # noqa: F821
    report = final_state.get("report", {})

    output_dir = PROJECT_ROOT / "output" / source
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "pipeline_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"[DONE]  Pipeline complete - report: {report_path}")
    print(f"{'='*60}\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PolicyChecker LangGraph Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source", choices=list(SOURCES.keys()), default="ait",
        help="Institution to process (default: ait)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print per-step statistics",
    )
    args = parser.parse_args()
    run(args.source, verbose=args.verbose)


if __name__ == "__main__":
    main()
