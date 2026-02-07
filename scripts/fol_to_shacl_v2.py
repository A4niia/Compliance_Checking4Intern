#!/usr/bin/env python3
"""
Improved FOL to SHACL Translation with Proper Target Classes
=============================================================
Uses domain ontology to map rules to correct target classes.

Usage:
    python scripts/fol_to_shacl_v2.py

Output:
    - shacl/ait_policy_shapes_refined.ttl
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
    "diploma": "PostgraduateStudent",
    "exchange": "ExchangeStudent",
    "graduating": "Student",
    
    # Employee-related
    "employee": "Employee",
    "staff": "Staff",
    "faculty": "Faculty",
    "instructor": "Faculty",
    "invigilator": "Faculty",
    
    # Financial
    "fee": "Fee",
    "tuition": "TuitionFee",
    "registration": "RegistrationFee",
    "account": "Account",
    "overdue": "OverdueAccount",
    "invoice": "Invoice",
    "sponsor": "Sponsor",
    "payment": "Fee",
    
    # Accommodation
    "accommodation": "Accommodation",
    "dormitory": "Dormitory",
    "housing": "Accommodation",
    "resident": "Accommodation",
    "room": "Accommodation",
    
    # Academic
    "course": "Course",
    "research": "Research",
    "contracted research": "ContractedResearch",
    "publication": "ResearchPublication",
    "examination": "Examination",
    "exam": "Examination",
    "semester": "Semester",
    
    # Process
    "grievance": "Grievance",
    "appeal": "Appeal",
    "committee": "Committee",
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
@prefix deontic: <http://example.org/deontic#> .

# Import ontology
# owl:imports <ait_policy_ontology.ttl> .

"""

SEVERITY_MAP = {
    "obligation": "sh:Violation",
    "prohibition": "sh:Violation", 
    "permission": "sh:Info"          # Permission shape itself is informational
}

# Permission-as-Exception: default restriction severity
DEFAULT_RESTRICTION_SEVERITY = "sh:Warning"  # Default restriction for unpermitted actions


def clean_text(text: str) -> str:
    """Clean text for use in SHACL comments."""
    if not text:
        return ""
    text = str(text).replace('\n', ' ').replace('\r', ' ')
    text = text.replace('"', "'").replace('\\', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:150]


def detect_target_class(rule_text: str, subject: str = None) -> str:
    """
    Detect the appropriate ontology class for a rule based on its text.
    Returns the most specific matching class.
    """
    text_lower = rule_text.lower()
    
    # Check subject first if provided
    if subject:
        subject_lower = subject.lower()
        for keyword, entity_class in ENTITY_MAPPING.items():
            if keyword in subject_lower:
                return entity_class
    
    # Priority matching - check longer phrases first
    priority_keywords = sorted(ENTITY_MAPPING.keys(), key=len, reverse=True)
    
    for keyword in priority_keywords:
        if keyword in text_lower:
            return ENTITY_MAPPING[keyword]
    
    # Default to Person if no match
    return "Person"


def extract_properties(fol_formula: str) -> list:
    """Extract property predicates from FOL formula."""
    if not fol_formula:
        return []
    
    # Find all predicate names
    matches = re.findall(r'([A-Za-z][A-Za-z0-9_]*)\\s*\\(', str(fol_formula))
    
    # Skip logical operators and deontic operators
    skip = {'forall', 'exists', 'O', 'P', 'F', 'implies', 'and', 'or', 'not', 
            'if', 'then', 'Within', 'Before', 'After', 'Student', 'Employee',
            'Person', 'Fee', 'Account'}
    
    # Return first 3 valid predicates as properties
    properties = []
    for m in matches:
        if m not in skip and m not in properties:
            properties.append(m)
            if len(properties) >= 3:
                break
    
    return properties


def make_refined_shape(rule: dict, idx: int) -> str:
    """Generate a refined SHACL shape with proper target class."""
    fol = rule.get('fol_formalization', {})
    
    # Skip if no formalization or error
    if not fol or 'error' in str(fol).lower():
        return ""
    
    rule_id = rule.get('id', f'R{idx}')
    original_text = rule.get('original_text', '')
    dtype = fol.get('deontic_type', 'obligation')
    formula = fol.get('deontic_formula', '') + ' ' + fol.get('fol_expansion', '')
    
    # Get subject from formalization if available
    subject = fol.get('subject', '')
    
    # Detect appropriate target class
    target_class = detect_target_class(original_text, subject)
    
    # --- Permission-as-Exception Pattern ---
    # For permissions: generate PAIRED shapes (default restriction + exception)
    # Based on Governatori & Rotolo (2010) — Defeasible Deontic Logic
    if dtype == 'permission':
        return make_permission_exception_shape(rule, idx, target_class, formula, subject)
    
    # For obligations and prohibitions: standard shape
    severity = SEVERITY_MAP.get(dtype, 'sh:Warning')
    comment = clean_text(original_text)
    shape_name = re.sub(r'[^A-Za-z0-9]', '', rule_id).capitalize()
    
    shape = f"\n# Rule: {rule_id} ({dtype})\n"
    shape += f"ait:{shape_name}Shape a sh:NodeShape ;\n"
    shape += f"    sh:targetClass ait:{target_class} ;\n"
    shape += f'    rdfs:label "{rule_id}" ;\n'
    shape += f"    deontic:type deontic:{dtype} ;\n"
    shape += f"    sh:severity {severity} ;\n"
    shape += f'    rdfs:comment "{comment}" .\n'
    
    return shape


def make_permission_exception_shape(rule: dict, idx: int, 
                                    target_class: str,
                                    formula: str,
                                    subject: str) -> str:
    """
    Generate Permission-as-Exception pattern (paired SHACL shapes).
    
    Based on Governatori & Rotolo (2010) — Defeasible Deontic Logic:
    - Shape 1: DEFAULT RESTRICTION — the action is restricted by default
    - Shape 2: PERMISSION EXCEPTION — documents the explicit grant
    
    This makes permissions enforceable: the default restriction catches
    violations when someone acts without having the permission grant,
    while the permission shape documents the exception.
    
    Example:
        Rule: "Students may request a leave of absence"
        → Default: Requesting leave without permission = Warning
        → Permission: Documents that students ARE permitted to request
    """
    fol = rule.get('fol_formalization', {})
    rule_id = rule.get('id', f'R{idx}')
    original_text = rule.get('original_text', '')
    comment = clean_text(original_text)
    shape_name = re.sub(r'[^A-Za-z0-9]', '', rule_id).capitalize()
    
    # Extract the action from the FOL formula for better annotation
    action = extract_action_from_formula(formula)
    
    output = ""
    
    # --- Shape 1: Default Restriction ---
    output += f"\n# Rule: {rule_id} — DEFAULT RESTRICTION (permission-as-exception)\n"
    output += f"# Under closed-world assumption: action restricted unless explicitly permitted\n"
    output += f"ait:{shape_name}DefaultShape a sh:NodeShape ;\n"
    output += f"    sh:targetClass ait:{target_class} ;\n"
    output += f'    rdfs:label "{rule_id} Default Restriction" ;\n'
    output += f"    deontic:type deontic:prohibition ;\n"
    output += f"    deontic:defaultRestriction true ;\n"
    output += f"    sh:severity {DEFAULT_RESTRICTION_SEVERITY} ;\n"
    output += f'    rdfs:comment "Default: {action} is restricted unless permission is granted. '
    output += f'Source: {comment}" .\n'
    
    # --- Shape 2: Permission Exception ---
    output += f"\n# Rule: {rule_id} — PERMISSION EXCEPTION\n"
    output += f"# Grants explicit permission, overriding the default restriction\n"
    output += f"ait:{shape_name}PermissionShape a sh:NodeShape ;\n"
    output += f"    sh:targetClass ait:{target_class} ;\n"
    output += f'    rdfs:label "{rule_id} Permission" ;\n'
    output += f"    deontic:type deontic:permission ;\n"
    output += f"    deontic:permissionScope \"explicit\" ;\n"
    output += f"    deontic:overrides ait:{shape_name}DefaultShape ;\n"
    output += f"    sh:severity sh:Info ;\n"
    output += f'    rdfs:comment "Permission: {comment}" .\n'
    
    return output


def extract_action_from_formula(formula: str) -> str:
    """
    Extract the action verb/predicate from a FOL formula.
    E.g., 'P(requestExtension(student))' → 'requestExtension'
    """
    # Try to match the innermost predicate
    match = re.search(r'[POF]\(([a-zA-Z]+)', formula)
    if match:
        action = match.group(1)
        # Convert camelCase to readable
        readable = re.sub(r'([A-Z])', r' \1', action).strip().lower()
        return readable
    
    # Fallback: first word
    words = formula.split()
    return words[0] if words else 'action'


def generate_refined_shapes():
    """Generate refined SHACL shapes from FOL results."""
    print("=" * 60)
    print("FOL TO SHACL - REFINED VERSION")
    print("=" * 60)
    
    SHACL_DIR.mkdir(exist_ok=True)
    
    # Load FOL results
    fol_file = RESEARCH_DIR / "fol_formalization_v2_results.json"
    if not fol_file.exists():
        fol_file = RESEARCH_DIR / "fol_formalization_results.json"
    
    if not fol_file.exists():
        print(f"❌ FOL results not found: {fol_file}")
        return
    
    with open(fol_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    rules = data.get('formalized_rules', [])
    print(f"📋 Loaded {len(rules)} formalized rules")
    
    # Generate shapes
    output = PREFIXES
    
    # Add ontology declaration
    output += "ait:PolicyShapesGraph a owl:Ontology ;\n"
    output += f'    rdfs:comment "Generated: {datetime.now().isoformat()}" .\n\n'
    
    stats = {"obligation": 0, "permission": 0, "prohibition": 0, "skipped": 0}
    permission_pairs = 0  # Track permission-as-exception pairs
    target_classes_used = {}
    
    for i, rule in enumerate(rules, 1):
        fol = rule.get('fol_formalization', {})
        
        if not fol or 'error' in str(fol).lower():
            stats["skipped"] += 1
            continue
        
        dtype = fol.get('deontic_type', 'obligation')
        if dtype in stats:
            stats[dtype] += 1
        if dtype == 'permission':
            permission_pairs += 1
        
        # Track target classes
        target = detect_target_class(
            rule.get('original_text', ''),
            fol.get('subject', '')
        )
        target_classes_used[target] = target_classes_used.get(target, 0) + 1
        
        output += make_refined_shape(rule, i)
    
    # Save output
    output_file = SHACL_DIR / "ait_policy_shapes_refined.ttl"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    total_shapes = stats['obligation'] + stats['prohibition'] + (permission_pairs * 2)
    print(f"\n✅ Saved refined shapes: {output_file}")
    print(f"\n📊 Statistics:")
    print(f"   Obligations: {stats['obligation']} shapes")
    print(f"   Permissions: {stats['permission']} → {permission_pairs * 2} shapes (paired default+exception)")
    print(f"   Prohibitions: {stats['prohibition']} shapes")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Total shapes generated: {total_shapes}")
    
    print(f"\n📊 Target Classes Used:")
    for cls, count in sorted(target_classes_used.items(), key=lambda x: -x[1]):
        print(f"   ait:{cls}: {count}")
    
    # Generate report
    report = f"""# SHACL Translation Report (Refined)

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
| **Total** | **{sum(stats.values())}** |

## Target Classes Used

| Class | Count |
|-------|-------|
"""
    for cls, count in sorted(target_classes_used.items(), key=lambda x: -x[1]):
        report += f"| ait:{cls} | {count} |\n"
    
    report += """
## Improvements Over v1

1. **Proper Target Classes**: Uses domain ontology classes instead of auto-generated
2. **Entity Detection**: Automatically maps rules to appropriate entities (Student, Fee, etc.)
3. **Better Comments**: Includes truncated original text in rdfs:comment
4. **Cleaner Output**: Consistent formatting and organization

## Next Steps

1. Validate shapes syntax with pyshacl
2. Create test data matching the ontology classes
3. Run validation to verify shapes work correctly
"""
    
    report_file = RESEARCH_DIR / "shacl_translation_refined_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📝 Report saved: {report_file}")


if __name__ == "__main__":
    generate_refined_shapes()
