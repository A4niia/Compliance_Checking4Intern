#!/usr/bin/env python3
"""
FOL to SHACL Translation v4
============================
Uses fol_formalization_v4_results.json as input.

Usage:
    python scripts/fol_to_shacl_v4.py
"""

import json
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"
SHACL_DIR = PROJECT_ROOT / "shacl"

# Domain entity mapping - maps keywords to proper ontology classes
ENTITY_MAPPING = {
    # Student-related
    "student": "Student",
    "postgraduate": "PostgraduateStudent",
    "pg student": "PostgraduateStudent",
    "master": "PostgraduateStudent",
    "doctoral": "PostgraduateStudent",
    "candidate": "PostgraduateStudent",
    
    # Faculty-related
    "advisor": "Advisor",
    "faculty": "Faculty",
    "instructor": "Instructor",
    "professor": "Faculty",
    "committee": "Committee",
    
    # Administrative
    "registrar": "Registrar",
    "department": "Department",
    "school": "School",
    "program": "Program",
    
    # Academic objects
    "thesis": "Thesis",
    "dissertation": "Dissertation",
    "proposal": "ThesisProposal",
    "examination": "Examination",
    "defense": "Defense",
    "course": "Course",
    "credit": "Credit",
    
    # Financial
    "fee": "Fee",
    "tuition": "TuitionFee",
    "scholarship": "Scholarship",
    "payment": "Payment",
    
    # Process
    "registration": "Registration",
    "enrollment": "Enrollment",
    "extension": "Extension",
    "leave": "LeaveOfAbsence",
    "withdrawal": "Withdrawal",
    "appeal": "Appeal",
    "grievance committee": "GrievanceCommittee",
    
    # Default
    "person": "Person",
}

# Prefixes for output
PREFIXES = """@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ait: <http://example.org/ait-policy#> .

"""

# Severity mapping
SEVERITY_MAP = {
    "obligation": "sh:Violation",
    "prohibition": "sh:Violation",
    "permission": "sh:Info"
}


def clean_text(text: str) -> str:
    """Clean text for use in SHACL comments."""
    text = text.replace('"', '\\"')
    text = re.sub(r'\s+', ' ', text)
    return text[:150]


def detect_target_class(rule_text: str, subject: str = None) -> str:
    """Detect the appropriate ontology class for a rule."""
    text_lower = rule_text.lower()
    
    # Check for specific matches
    for keyword, cls in ENTITY_MAPPING.items():
        if keyword in text_lower:
            return cls
    
    # Default to Student for academic policies
    return "Student"


def extract_properties(fol_formula: str) -> list:
    """Extract property predicates from FOL formula."""
    properties = []
    predicates = re.findall(r'(\w+)\s*\(', fol_formula)
    for pred in predicates:
        if pred.lower() not in ['forall', 'exists', 'implies', 'and', 'or', 'not', 'o', 'p', 'f']:
            properties.append(pred)
    return properties


def make_refined_shape(rule: dict, idx: int) -> str:
    """Generate a refined SHACL shape with proper target class."""
    fol = rule.get('fol_formalization', {})
    
    if not fol or 'error' in fol:
        return ""
    
    rule_id = rule.get('id', f'rule_{idx}')
    original_text = rule.get('original_text', '')
    dtype = fol.get('deontic_type', 'obligation')
    formula = fol.get('deontic_formula', fol.get('fol_formula', ''))
    subject = fol.get('subject', '')
    
    # Detect target class
    target_class = detect_target_class(original_text, subject)
    
    # Clean text for comment
    comment = clean_text(original_text)
    
    # Build shape
    severity = SEVERITY_MAP.get(dtype, "sh:Violation")
    shape_name = f"ait:{rule_id.replace('-', '_')}Shape"
    
    # Extract potential properties
    props = extract_properties(formula) if formula else ['hasRequirement']
    main_prop = props[0] if props else 'hasRequirement'
    
    shape = f"""# {rule_id}: {dtype.upper()}
{shape_name} a sh:NodeShape ;
    sh:targetClass ait:{target_class} ;
    rdfs:comment "{comment}" ;
    sh:severity {severity} ;
    sh:property [
        sh:path ait:{main_prop} ;
"""
    
    if dtype == "obligation":
        shape += "        sh:minCount 1 ;\n"
    elif dtype == "prohibition":
        shape += "        sh:maxCount 0 ;\n"
    else:  # permission
        shape += "        # Permission: no constraint, informational only\n"
    
    shape += f'        sh:message "{comment}" ;\n'
    shape += "    ] .\n\n"
    
    return shape


def generate_refined_shapes():
    """Generate refined SHACL shapes from FOL v4 results."""
    print("=" * 60)
    print("FOL TO SHACL - V4 VERSION")
    print("=" * 60)
    
    SHACL_DIR.mkdir(exist_ok=True)
    
    # Load FOL v4 results
    fol_file = RESEARCH_DIR / "fol_formalization_v4_results.json"
    
    if not fol_file.exists():
        print(f"❌ FOL v4 results not found: {fol_file}")
        print("   Run generate_fol_v4.py first.")
        return
    
    with open(fol_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    rules = data.get('formalized_rules', [])
    print(f"📋 Loaded {len(rules)} formalized rules from v4")
    
    # Generate shapes
    output = PREFIXES
    
    # Add ontology declaration
    output += "ait:PolicyShapesGraphV4 a owl:Ontology ;\n"
    output += f'    rdfs:comment "Generated: {datetime.now().isoformat()} from v4 gold standard" .\n\n'
    
    stats = {"obligation": 0, "permission": 0, "prohibition": 0, "skipped": 0}
    target_classes_used = {}
    
    for i, rule in enumerate(rules, 1):
        fol = rule.get('fol_formalization', {})
        
        if not fol or 'error' in fol:
            stats["skipped"] += 1
            continue
        
        dtype = fol.get('deontic_type', 'obligation')
        if dtype in stats:
            stats[dtype] += 1
        
        # Track target classes
        target = detect_target_class(
            rule.get('original_text', ''),
            fol.get('subject', '')
        )
        target_classes_used[target] = target_classes_used.get(target, 0) + 1
        
        output += make_refined_shape(rule, i)
    
    # Save output
    output_file = SHACL_DIR / "ait_policy_shapes_v4.ttl"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    total_shapes = stats['obligation'] + stats['prohibition'] + stats['permission']
    print(f"\n✅ Saved v4 shapes: {output_file}")
    print(f"\n📊 Statistics:")
    print(f"   Obligations: {stats['obligation']} shapes")
    print(f"   Permissions: {stats['permission']} shapes")
    print(f"   Prohibitions: {stats['prohibition']} shapes")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Total shapes generated: {total_shapes}")
    
    print(f"\n📊 Target Classes Used:")
    for cls, count in sorted(target_classes_used.items(), key=lambda x: -x[1]):
        print(f"   ait:{cls}: {count}")
    
    # Generate report
    report = f"""# SHACL Translation Report v4

**Generated:** {datetime.now().isoformat()}
**Input:** {fol_file.name}
**Output:** {output_file.name}

## Statistics

| Deontic Type | Count |
|--------------|-------|
| Obligation | {stats['obligation']} |
| Permission | {stats['permission']} |
| Prohibition | {stats['prohibition']} |
| Skipped | {stats['skipped']} |
| **Total** | **{total_shapes}** |

## Target Classes Used

| Class | Count |
|-------|-------|
"""
    for cls, count in sorted(target_classes_used.items(), key=lambda x: -x[1]):
        report += f"| ait:{cls} | {count} |\n"
    
    report_file = RESEARCH_DIR / "shacl_translation_v4_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📝 Report saved: {report_file}")


if __name__ == "__main__":
    generate_refined_shapes()
