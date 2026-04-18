from langgraph_agent.state import PipelineState

FOL_FAIL_THRESHOLD = 0.5  # if > 50% of rules failed FOL, still route to validate


def route_fol(state: PipelineState) -> str:
    """Route after fol_node: use direct_shacl fallback only for partially failed batches."""
    failed = state.get("fol_failed", [])
    total = len(state.get("fol_formulas", [])) + len(failed)

    if not failed:
        return "shacl"

    fail_rate = len(failed) / max(total, 1)
    if fail_rate >= FOL_FAIL_THRESHOLD:
        # Majority failed — skip direct fallback, still proceed to shacl with what we have
        return "shacl"
    return "direct_shacl"
