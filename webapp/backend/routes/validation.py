"""
Validation API Routes
Provides endpoints for extraction validation metrics and results.
"""

from flask import Blueprint, jsonify
import json
from pathlib import Path

validation_bp = Blueprint('validation', __name__)

# Path to research directory
RESEARCH_DIR = Path(__file__).parent.parent.parent.parent / "research"


@validation_bp.route('/api/validation/metrics', methods=['GET'])
def get_validation_metrics():
    """Get extraction validation metrics."""
    metrics_file = RESEARCH_DIR / "extraction_metrics.json"
    
    if not metrics_file.exists():
        return jsonify({
            "error": "Metrics not found. Run validate_extraction.py first.",
            "metrics": None,
            "results": []
        }), 404
    
    with open(metrics_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return jsonify(data)


@validation_bp.route('/api/validation/pipeline-steps', methods=['GET'])
def get_pipeline_steps():
    """Get pipeline step information."""
    steps = [
        {
            "id": 1,
            "name": "PDF Upload",
            "description": "Upload policy documents",
            "icon": "📄",
            "status": "complete",
            "details": "Supports PDF documents up to 50MB"
        },
        {
            "id": 2,
            "name": "OCR Extraction",
            "description": "Extract text from PDFs",
            "icon": "🔍",
            "status": "complete",
            "details": "Using DeepSeek-OCR for high accuracy"
        },
        {
            "id": 3,
            "name": "Segmentation",
            "description": "Split into sentences",
            "icon": "✂️",
            "status": "complete",
            "details": "NLTK-based sentence boundary detection"
        },
        {
            "id": 4,
            "name": "Classification",
            "description": "LLM identifies rules",
            "icon": "🤖",
            "status": "complete",
            "details": "Mistral 7B with 95.88% validated accuracy (κ=0.8503)"
        },
        {
            "id": 5,
            "name": "Simplification",
            "description": "Simplify complex rules",
            "icon": "📝",
            "status": "complete",
            "details": "LLM-based text simplification"
        },
        {
            "id": 6,
            "name": "FOL Formalization",
            "description": "Convert to first-order logic",
            "icon": "🧮",
            "status": "complete",
            "details": "100% formalization success rate"
        },
        {
            "id": 7,
            "name": "SHACL Translation",
            "description": "Generate SHACL shapes",
            "icon": "🔷",
            "status": "complete",
            "details": "96 shapes, 1309 triples generated"
        },
        {
            "id": 8,
            "name": "Validation",
            "description": "Validate against data",
            "icon": "✅",
            "status": "complete",
            "details": "PySHACL-based constraint checking"
        }
    ]
    
    return jsonify({"steps": steps})


@validation_bp.route('/api/validation/rules/<rule_id>/source', methods=['GET'])
def get_rule_source(rule_id):
    """Get source information for a specific rule."""
    gs_file = RESEARCH_DIR / "gold_standard_template.json"
    
    if not gs_file.exists():
        return jsonify({"error": "Gold standard not found"}), 404
    
    with open(gs_file, 'r', encoding='utf-8') as f:
        rules = json.load(f)
    
    for rule in rules:
        if rule.get('id') == rule_id:
            return jsonify({
                "id": rule_id,
                "source_document": rule.get('source_document', 'Unknown'),
                "page_number": rule.get('page_number', 0),
                "original_text": rule.get('original_text', ''),
                "rule_id": rule.get('rule_id', '')
            })
    
    return jsonify({"error": f"Rule {rule_id} not found"}), 404
