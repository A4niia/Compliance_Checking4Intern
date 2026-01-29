"""
Agent API Routes
Exposes PolicyAgent functionality via REST API with metrics tracking.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import sys
from pathlib import Path

# Add agent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.core import PolicyAgent, create_agent

agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')

# Global agent instance
_agent = None

def get_agent() -> PolicyAgent:
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


@agent_bp.route('/status', methods=['GET'])
def agent_status():
    """Get agent status and capabilities."""
    agent = get_agent()
    return jsonify({
        "status": "active",
        "tools": agent.tools.list_tools(),
        "action_history": len(agent.memory.actions),
        "timestamp": datetime.now().isoformat()
    })


@agent_bp.route('/run', methods=['POST'])
def run_agent():
    """Execute agent with a goal."""
    data = request.json or {}
    goal = data.get('goal', 'Extract and formalize policy rules')
    
    agent = get_agent()
    result = agent.run(goal)
    
    return jsonify(result)


@agent_bp.route('/tools', methods=['GET'])
def list_tools():
    """List available agent tools."""
    agent = get_agent()
    return jsonify({
        "tools": agent.tools.list_tools()
    })


@agent_bp.route('/execute/<tool_name>', methods=['POST'])
def execute_tool(tool_name):
    """Execute a specific tool."""
    data = request.json or {}
    agent = get_agent()
    
    result = agent._execute_tool(tool_name, **data)
    
    return jsonify({
        "tool": tool_name,
        "result": result,
        "metrics": agent.metrics.get_summary()
    })


@agent_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get all agent metrics aligned to research questions."""
    agent = get_agent()
    return jsonify(agent.metrics.get_summary())


@agent_bp.route('/metrics/rq/<rq_id>', methods=['GET'])
def get_rq_metrics(rq_id):
    """Get metrics for specific research question (RQ1, RQ2, RQ3)."""
    agent = get_agent()
    summary = agent.metrics.get_summary()
    
    rq_map = {
        "1": "RQ1_LLM_Classification",
        "2": "RQ2_FOL_Formalization", 
        "3": "RQ3_SHACL_Translation"
    }
    
    rq_key = rq_map.get(rq_id)
    if not rq_key:
        return jsonify({"error": "Invalid RQ ID. Use 1, 2, or 3"}), 400
    
    return jsonify({
        "research_question": rq_key,
        "metrics": summary["metrics_by_rq"].get(rq_key, [])
    })


@agent_bp.route('/memory', methods=['GET'])
def get_memory():
    """Get agent action memory."""
    agent = get_agent()
    return jsonify({
        "action_chain": agent.memory.get_action_chain(),
        "decisions": agent.memory.decisions[-10:],  # Last 10 decisions
        "success_rate": agent.memory.get_success_rate()
    })


@agent_bp.route('/reset', methods=['POST'])
def reset_agent():
    """Reset agent state."""
    global _agent
    _agent = create_agent()
    return jsonify({"status": "reset", "message": "Agent reset successfully"})


# ============================================
# AUTONOMOUS COMPLIANCE CHECK
# ============================================

@agent_bp.route('/autonomous/check', methods=['POST'])
def autonomous_check():
    """Run autonomous compliance check on entities."""
    data = request.json or {}
    entities = data.get('entities', [])
    
    agent = get_agent()
    results = []
    
    for entity in entities:
        # Use agent's compliance tool
        result = agent._execute_tool('check_compliance', entity_data=entity)
        results.append({
            "entity_id": entity.get("id"),
            "result": result
        })
    
    return jsonify({
        "total_checked": len(results),
        "results": results,
        "metrics": agent.metrics.get_summary()
    })


@agent_bp.route('/pipeline/full', methods=['POST'])
def run_full_pipeline():
    """
    Run full agentic pipeline:
    1. Extract rules (RQ1)
    2. Classify rules (RQ1)
    3. Formalize to FOL (RQ2)
    4. Translate to SHACL (RQ3)
    5. Check compliance (RQ3)
    """
    agent = get_agent()
    
    pipeline_results = {
        "stages": [],
        "start_time": datetime.now().isoformat()
    }
    
    # Stage 1: Extract
    extract_result = agent._execute_tool('extract_rules', document_path="policy.pdf")
    pipeline_results["stages"].append({
        "stage": "RQ1-Extract",
        "result": extract_result
    })
    
    # Stage 2: Classify
    classify_result = agent._execute_tool('classify_rule', rule_text="Students must pay all fees before registration")
    pipeline_results["stages"].append({
        "stage": "RQ1-Classify",
        "result": classify_result
    })
    
    # Stage 3: Formalize FOL
    fol_result = agent._execute_tool('formalize_fol', 
                                     rule_text="Students must pay all fees before registration",
                                     rule_type=classify_result.get("rule_type", "obligation"))
    pipeline_results["stages"].append({
        "stage": "RQ2-Formalize",
        "result": fol_result
    })
    
    # Stage 4: Translate SHACL
    shacl_result = agent._execute_tool('translate_shacl',
                                       fol_formula=fol_result.get("deontic_formula", ""),
                                       rule_id="FB-R002")
    pipeline_results["stages"].append({
        "stage": "RQ3-Translate",
        "result": shacl_result
    })
    
    # Stage 5: Check Compliance
    compliance_result = agent._execute_tool('check_compliance',
                                            entity_data={"id": "STU001", "fees_paid": False, "status": "enrolled"})
    pipeline_results["stages"].append({
        "stage": "RQ3-Validate",
        "result": compliance_result
    })
    
    pipeline_results["end_time"] = datetime.now().isoformat()
    pipeline_results["metrics"] = agent.metrics.get_summary()
    
    return jsonify(pipeline_results)
