"""
PolicyChecker Flask Backend
Main application entry point
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
import json
import sys
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Add agent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Register agent blueprint
from agent.routes import agent_bp
app.register_blueprint(agent_bp)

# Register pipeline blueprint
from backend.routes.pipeline import pipeline_bp
app.register_blueprint(pipeline_bp)

# Register validation blueprint
from backend.routes.validation import validation_bp
app.register_blueprint(validation_bp)

# Register live pipeline blueprint (real-time SSE)
from backend.routes.live_pipeline import live_pipeline_bp
app.register_blueprint(live_pipeline_bp)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"
SHACL_DIR = PROJECT_ROOT / "shacl"

# ============================================
# UTILITY FUNCTIONS
# ============================================

def load_rules():
    """Load gold standard rules with latest annotations."""
    # Use v2 file with LLM annotations (Jan 31, 2026)
    gs_file = RESEARCH_DIR / "gold_standard_annotated_v2.json"
    if gs_file.exists():
        with open(gs_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_rules(rules):
    """Save rules to file."""
    gs_file = RESEARCH_DIR / "gold_standard_annotated_v2.json"
    with open(gs_file, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)

def load_fol_results():
    """Load FOL formalization results."""
    fol_file = RESEARCH_DIR / "fol_formalization_v2_results.json"
    if fol_file.exists():
        with open(fol_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"formalized_rules": []}

# ============================================
# API ROUTES
# ============================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics."""
    rules = load_rules()
    fol = load_fol_results()
    
    annotated = sum(1 for r in rules if r.get('human_annotation', {}).get('is_rule') is not None)
    
    # Count rule types from FOL
    obligations = sum(1 for r in fol.get('formalized_rules', []) 
                     if r.get('fol_formalization', {}).get('deontic_type') == 'obligation')
    permissions = sum(1 for r in fol.get('formalized_rules', []) 
                     if r.get('fol_formalization', {}).get('deontic_type') == 'permission')
    prohibitions = sum(1 for r in fol.get('formalized_rules', []) 
                      if r.get('fol_formalization', {}).get('deontic_type') == 'prohibition')
    
    return jsonify({
        "total_rules": len(rules),
        "annotated": annotated,
        "pending_annotation": len(rules) - annotated,
        "formalized": len(fol.get('formalized_rules', [])),
        "obligations": obligations,
        "permissions": permissions,
        "prohibitions": prohibitions,
        "shacl_triples": 1309  # From validation
    })

@app.route('/api/rules', methods=['GET'])
def get_rules():
    """Get all rules with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    filter_type = request.args.get('type', None)
    
    rules = load_rules()
    fol = load_fol_results()
    
    # Merge FOL data with rules
    fol_map = {r['id']: r.get('fol_formalization', {}) for r in fol.get('formalized_rules', [])}
    
    for rule in rules:
        rule['fol'] = fol_map.get(rule['id'], {})
    
    # Filter by type if specified
    if filter_type:
        rules = [r for r in rules if r.get('fol', {}).get('deontic_type') == filter_type]
    
    # Paginate
    total = len(rules)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = rules[start:end]
    
    return jsonify({
        "rules": paginated,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    })

@app.route('/api/rules/<rule_id>', methods=['GET'])
def get_rule(rule_id):
    """Get single rule by ID."""
    rules = load_rules()
    fol = load_fol_results()
    
    fol_map = {r['id']: r.get('fol_formalization', {}) for r in fol.get('formalized_rules', [])}
    
    for rule in rules:
        if rule['id'] == rule_id:
            rule['fol'] = fol_map.get(rule_id, {})
            return jsonify(rule)
    
    return jsonify({"error": "Rule not found"}), 404

@app.route('/api/rules/<rule_id>/annotate', methods=['PUT'])
def annotate_rule(rule_id):
    """Update human annotation for a rule."""
    data = request.json
    rules = load_rules()
    
    for rule in rules:
        if rule['id'] == rule_id:
            rule['human_annotation'] = {
                "is_rule": data.get('is_rule'),
                "rule_type": data.get('rule_type'),
                "subject": data.get('subject'),
                "condition": data.get('condition'),
                "action": data.get('action'),
                "deontic_marker": data.get('deontic_marker'),
                "annotator": data.get('annotator', 'Web User'),
                "annotation_date": datetime.now().isoformat(),
                "confidence": data.get('confidence'),
                "notes": data.get('notes', '')
            }
            save_rules(rules)
            return jsonify({"success": True, "rule": rule})
    
    return jsonify({"error": "Rule not found"}), 404

@app.route('/api/fol', methods=['GET'])
def get_fol():
    """Get all FOL formalizations."""
    fol = load_fol_results()
    return jsonify(fol)

@app.route('/api/shacl', methods=['GET'])
def get_shacl():
    """Get SHACL shapes info."""
    shacl_file = SHACL_DIR / "ait_policy_shapes.ttl"
    
    if not shacl_file.exists():
        return jsonify({"error": "SHACL file not found"}), 404
    
    with open(shacl_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return jsonify({
        "file": str(shacl_file),
        "size": len(content),
        "shapes": content.count('sh:NodeShape'),
        "content": content[:5000] + "..." if len(content) > 5000 else content
    })

@app.route('/api/export/<format>', methods=['GET'])
def export_data(format):
    """Export data in various formats."""
    if format == 'json':
        rules = load_rules()
        return jsonify(rules)
    elif format == 'fol':
        fol = load_fol_results()
        return jsonify(fol)
    elif format == 'shacl':
        shacl_file = SHACL_DIR / "ait_policy_shapes.ttl"
        if shacl_file.exists():
            with open(shacl_file, 'r', encoding='utf-8') as f:
                return f.read(), 200, {'Content-Type': 'text/turtle'}
    
    return jsonify({"error": "Invalid format"}), 400

# ============================================
# DEMO USE CASE - Student Compliance Checking
# ============================================

SAMPLE_STUDENTS = [
    {"id": "STU001", "name": "John Doe", "program": "Master of CS", "status": "enrolled", 
     "fees_paid": True, "visa_valid": True, "gpa": 3.5, "accommodation": "on_campus"},
    {"id": "STU002", "name": "Jane Smith", "program": "PhD Data Science", "status": "enrolled",
     "fees_paid": False, "visa_valid": True, "gpa": 3.8, "accommodation": "on_campus"},
    {"id": "STU003", "name": "Bob Wilson", "program": "Master of Eng", "status": "graduated",
     "fees_paid": True, "visa_valid": False, "gpa": 3.2, "accommodation": "on_campus", "days_after_graduation": 10},
    {"id": "STU004", "name": "Alice Brown", "program": "Diploma in AI", "status": "suspended",
     "fees_paid": True, "visa_valid": True, "gpa": 1.8, "accommodation": "on_campus"}
]

POLICY_RULES = [
    {"id": "FB-R002", "type": "obligation", "description": "Students must pay fees before registration",
     "check": lambda s: s.get("fees_paid") or s.get("status") != "enrolled", "msg": "Outstanding fees"},
    {"id": "FS-R048", "type": "prohibition", "description": "Graduated students cannot stay >5 days",
     "check": lambda s: not (s.get("status") == "graduated" and s.get("days_after_graduation", 0) > 5), "msg": "Overstaying"},
    {"id": "DOC-R058", "type": "prohibition", "description": "Suspended students cannot use accommodation",
     "check": lambda s: not (s.get("status") == "suspended" and s.get("accommodation") == "on_campus"), "msg": "Suspended in dorm"},
    {"id": "GPA-MIN", "type": "obligation", "description": "Minimum GPA of 2.0 required",
     "check": lambda s: s.get("gpa", 0) >= 2.0 or s.get("status") != "enrolled", "msg": "GPA below minimum"},
    {"id": "VISA", "type": "obligation", "description": "Valid visa required",
     "check": lambda s: s.get("visa_valid"), "msg": "Invalid visa"}
]

def check_compliance(student):
    violations, passed = [], []
    for rule in POLICY_RULES:
        try:
            if rule["check"](student):
                passed.append({"rule_id": rule["id"], "type": rule["type"], "description": rule["description"]})
            else:
                violations.append({"rule_id": rule["id"], "type": rule["type"], "description": rule["description"], "msg": rule["msg"]})
        except: pass
    return {
        "student_id": student["id"], "student_name": student["name"],
        "passed": len(passed), "violations": len(violations),
        "compliance_rate": round(len(passed) / len(POLICY_RULES) * 100, 1),
        "is_compliant": len(violations) == 0,
        "passed_rules": passed, "violation_details": violations
    }

@app.route('/api/demo/students', methods=['GET'])
def get_students():
    return jsonify(SAMPLE_STUDENTS)

@app.route('/api/demo/check/<student_id>', methods=['GET'])
def check_student(student_id):
    student = next((s for s in SAMPLE_STUDENTS if s["id"] == student_id), None)
    if not student: return jsonify({"error": "Not found"}), 404
    return jsonify(check_compliance(student))

@app.route('/api/demo/check-all', methods=['GET'])
def check_all():
    results = [check_compliance(s) for s in SAMPLE_STUDENTS]
    return jsonify({
        "total_students": len(SAMPLE_STUDENTS),
        "compliant_students": sum(1 for r in results if r["is_compliant"]),
        "non_compliant_students": sum(1 for r in results if not r["is_compliant"]),
        "total_violations": sum(r["violations"] for r in results),
        "student_results": results,
        "summary": {"status": "ATTENTION REQUIRED" if any(not r["is_compliant"] for r in results) else "ALL COMPLIANT"}
    })

@app.route('/api/demo/rules', methods=['GET'])
def get_demo_rules():
    return jsonify([{"id": r["id"], "type": r["type"], "description": r["description"]} for r in POLICY_RULES])

# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("PolicyChecker Backend Server")
    print("=" * 60)
    print(f"Research Dir: {RESEARCH_DIR}")
    print(f"SHACL Dir: {SHACL_DIR}")
    print("Starting server on http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
