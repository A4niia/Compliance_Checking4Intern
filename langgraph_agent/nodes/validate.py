from __future__ import annotations

from pathlib import Path
from typing import List

from pyshacl import validate
from rdflib import Graph, Namespace, RDF, SH

from langgraph_agent.state import PipelineState, SHACLShape

PROJECT_ROOT = Path(__file__).parent.parent.parent

SHACL_SHAPES_FILE  = PROJECT_ROOT / "shacl" / "shapes"   / "ait_policy_shapes.ttl"
SHACL_TEST_FILE    = PROJECT_ROOT / "shacl" / "test_data" / "tdd_test_data_fixed.ttl"
ONTOLOGY_FILE      = PROJECT_ROOT / "shacl" / "ontology"  / "ait_policy_ontology.ttl"

AIT = Namespace("http://example.org/ait-policy#")


def _merge_shapes(pipeline_shapes: List[SHACLShape]) -> Graph:
    """Merge authoritative shapes with pipeline-generated shapes into one graph."""
    g = Graph()

    # Load authoritative production shapes
    if SHACL_SHAPES_FILE.exists():
        g.parse(str(SHACL_SHAPES_FILE), format="turtle")

    # Append valid pipeline-generated shapes
    for shape in pipeline_shapes:
        if shape["syntax_valid"] and shape["turtle_text"]:
            try:
                g.parse(data=shape["turtle_text"], format="turtle")
            except Exception:
                pass  # skip malformed shapes silently

    return g


def validate_node(state: PipelineState) -> PipelineState:
    shapes: List[SHACLShape] = state.get("shacl_shapes", [])
    errors: List[str] = []

    if not SHACL_TEST_FILE.exists():
        return {
            **state,
            "validation_results": {"skipped": True, "reason": "test data not found"},
            "conforms": False,
            "current_step": "validate",
            "errors": [f"validate: test data not found at {SHACL_TEST_FILE}"],
        }

    # Build shapes graph
    shapes_graph = _merge_shapes(shapes)
    shape_count = len(list(shapes_graph.subjects(RDF.type, SH.NodeShape)))

    # Load test data
    data_graph = Graph()
    data_graph.parse(str(SHACL_TEST_FILE), format="turtle")
    entity_count = len(set(data_graph.subjects()))

    # Run validation
    try:
        conforms, results_graph, results_text = validate(
            data_graph,
            shacl_graph=shapes_graph,
            ont_graph=Graph().parse(str(ONTOLOGY_FILE)) if ONTOLOGY_FILE.exists() else None,
            inference="rdfs",
            abort_on_first=False,
            meta_shacl=False,
            advanced=True,
            debug=False,
        )
    except Exception as exc:
        errors.append(f"validate: pyshacl error: {exc}")
        return {
            **state,
            "validation_results": {"error": str(exc)},
            "conforms": False,
            "current_step": "validate",
            "errors": errors,
        }

    # Parse violations
    violations = []
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        violations.append({
            "focus_node":     str(results_graph.value(result, SH.focusNode)),
            "source_shape":   str(results_graph.value(result, SH.sourceShape)),
            "result_message": str(results_graph.value(result, SH.resultMessage)),
            "severity":       str(results_graph.value(result, SH.resultSeverity)),
        })

    validation_results = {
        "conforms":          conforms,
        "shape_count":       shape_count,
        "entity_count":      entity_count,
        "violation_count":   len(violations),
        "violations":        violations[:50],  # cap at 50 for JSON size
        "pipeline_shapes":   len(shapes),
        "valid_shapes":      sum(1 for s in shapes if s["syntax_valid"]),
    }

    # Save validation results
    output_dir = PROJECT_ROOT / "output" / state["source"]
    output_dir.mkdir(parents=True, exist_ok=True)
    import json
    (output_dir / "validation_results.json").write_text(
        json.dumps(validation_results, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return {
        **state,
        "validation_results": validation_results,
        "conforms": conforms,
        "current_step": "validate",
        "errors": errors,
    }
