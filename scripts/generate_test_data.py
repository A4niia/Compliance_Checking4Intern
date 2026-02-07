#!/usr/bin/env python3
"""
Test Data Generator for SHACL TDD
===================================
Auto-generates test RDF data from gold standard rules for TDD validation.

For each formalized rule, generates:
- 1 positive test entity (conforming → should pass)
- 1 negative test entity (violating → should fail)

Usage:
    python scripts/generate_test_data.py
    python scripts/generate_test_data.py --output shacl/tdd_test_data.ttl
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"
SHACL_DIR = PROJECT_ROOT / "shacl"


# =============================================================================
# ENTITY TEMPLATES
# =============================================================================

# Map subject types to RDF type and default properties
ENTITY_TEMPLATES = {
    "Student": {
        "rdf_type": "ait:Student",
        "default_positive": {
            "ait:paid": "true",
            "ait:enrolled": "true",
            "ait:residesoncampus": "true",
        },
        "default_negative": {
            "ait:paid": "false",
            "ait:enrolled": "true",
        },
    },
    "PostgraduateStudent": {
        "rdf_type": "ait:PostgraduateStudent",
        "default_positive": {
            "ait:paid": "true",
            "ait:enrolled": "true",
            "ait:hasAdvisor": "true",
        },
        "default_negative": {
            "ait:paid": "false",
            "ait:enrolled": "true",
        },
    },
    "Graduate": {
        "rdf_type": "ait:Graduate",
        "default_positive": {
            "ait:livingbeyondfivedays": "false",
            "ait:approvalfromofamdirector": "true",
        },
        "default_negative": {
            "ait:livingbeyondfivedays": "true",
            "ait:approvalfromofamdirector": "false",
        },
    },
    "Employee": {
        "rdf_type": "ait:Employee",
        "default_positive": {
            "ait:acceptedgift": "false",
            "ait:reported": "true",
        },
        "default_negative": {
            "ait:acceptedgift": "true",
            "ait:giftvalue": "50000",
            "ait:reported": "false",
        },
    },
    "Faculty": {
        "rdf_type": "ait:Faculty",
        "default_positive": {
            "ait:employed": "true",
        },
        "default_negative": {
            "ait:employed": "false",
        },
    },
    "Sponsor": {
        "rdf_type": "ait:Sponsor",
        "default_positive": {
            "ait:invoice": "true",
            "ait:outstandingdues": "false",
        },
        "default_negative": {
            "ait:invoice": "false",
            "ait:outstandingdues": "true",
        },
    },
    "Resident": {
        "rdf_type": "ait:Resident",
        "default_positive": {
            "ait:residesoncampus": "true",
            "ait:paid": "true",
        },
        "default_negative": {
            "ait:residesoncampus": "true",
            "ait:paid": "false",
        },
    },
    "Person": {
        "rdf_type": "ait:Person",
        "default_positive": {},
        "default_negative": {},
    },
}


# Map keywords to entity types
SUBJECT_KEYWORDS = {
    "student": "Student",
    "students": "Student",
    "postgraduate": "PostgraduateStudent",
    "graduate": "Graduate",
    "alumni": "Graduate",
    "employee": "Employee",
    "employees": "Employee",
    "staff": "Employee",
    "faculty": "Faculty",
    "faculties": "Faculty",
    "sponsor": "Sponsor",
    "sponsors": "Sponsor",
    "resident": "Resident",
    "residents": "Resident",
    "person": "Person",
    "individual": "Person",
    "member": "Person",
}


def detect_entity_type(rule: dict) -> str:
    """Detect the entity type from rule text and FOL formalization."""
    fol = rule.get("fol_formalization", {})
    subject = fol.get("subject", "").lower()
    text = rule.get("original_text", "").lower()
    
    # Check rule subject first
    for keyword, entity_type in SUBJECT_KEYWORDS.items():
        if keyword in subject:
            return entity_type
    
    # Check original text
    for keyword, entity_type in SUBJECT_KEYWORDS.items():
        if keyword in text:
            return entity_type
    
    return "Person"  # Default


def generate_entity_ttl(entity_id: str, entity_type: str, 
                        properties: dict, label: str) -> str:
    """Generate a Turtle entity with given properties."""
    template = ENTITY_TEMPLATES.get(entity_type, ENTITY_TEMPLATES["Person"])
    rdf_type = template["rdf_type"]
    
    ttl = f"\n# {label}\n"
    ttl += f"ait:{entity_id} a {rdf_type} ;\n"
    ttl += f'    rdfs:label "{label}" ;\n'
    
    # Add properties
    prop_lines = []
    for prop, value in properties.items():
        # Determine if boolean, integer, or string
        if value.lower() in ("true", "false"):
            prop_lines.append(f'    {prop} {value}')
        elif value.isdigit():
            prop_lines.append(f'    {prop} {value}')
        else:
            prop_lines.append(f'    {prop} "{value}"')
    
    if prop_lines:
        ttl += " ;\n".join(prop_lines)
    
    ttl += " .\n"
    return ttl


def generate_test_data(output_path: Path = None):
    """
    Generate TDD test data from gold standard + FOL formalizations.
    
    For each successfully formalized rule, creates:
    - 1 positive test entity (should conform)
    - 1 negative test entity (should trigger violation/warning)
    """
    # Load FOL results
    fol_file = RESEARCH_DIR / "fol_formalization_v2_results.json"
    if not fol_file.exists():
        fol_file = RESEARCH_DIR / "fol_formalization_results.json"
    
    if not fol_file.exists():
        print(f"❌ FOL results not found: {fol_file}")
        return
    
    with open(fol_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    rules = data.get("formalized_rules", [])
    print(f"📋 Loaded {len(rules)} formalized rules")
    
    if output_path is None:
        output_path = SHACL_DIR / "tdd_test_data.ttl"
    
    # Turtle header
    ttl = """@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ait: <http://example.org/ait-policy#> .
@prefix deontic: <http://example.org/deontic#> .

# =============================================================================
# TDD Test Data — Auto-generated from Gold Standard
# =============================================================================
# Generated: {timestamp}
# Source: {source}
#
# This file contains positive (conforming) and negative (violating) test
# entities for each formalized rule. Used by test_shacl_shapes.py for TDD.
# =============================================================================

""".format(timestamp=datetime.now().isoformat(), source=fol_file.name)
    
    positive_count = 0
    negative_count = 0
    skipped = 0
    
    # Track entity types for summary
    entities_by_type = {}
    
    for i, rule in enumerate(rules, 1):
        fol = rule.get("fol_formalization", {})
        
        if not fol or "error" in str(fol).lower():
            skipped += 1
            continue
        
        rule_id = rule.get("id", f"R{i:03d}")
        rule_id_clean = re.sub(r'[^A-Za-z0-9]', '', rule_id)
        dtype = fol.get("deontic_type", "obligation")
        original_text = rule.get("original_text", "")[:80]
        
        # Detect entity type
        entity_type = detect_entity_type(rule)
        template = ENTITY_TEMPLATES.get(entity_type, ENTITY_TEMPLATES["Person"])
        entities_by_type[entity_type] = entities_by_type.get(entity_type, 0) + 1
        
        ttl += f"\n# {'='*60}\n"
        ttl += f"# Rule {rule_id}: {dtype.upper()}\n"
        ttl += f"# {original_text}\n"
        ttl += f"# {'='*60}\n"
        
        # --- Positive test entity ---
        pos_id = f"Pos{rule_id_clean}"
        pos_label = f"Positive test for {rule_id} ({dtype})"
        ttl += generate_entity_ttl(
            pos_id, entity_type,
            template["default_positive"],
            pos_label
        )
        positive_count += 1
        
        # --- Negative test entity ---
        # Only for obligations and prohibitions (permissions don't have "negative")
        if dtype in ("obligation", "prohibition"):
            neg_id = f"Neg{rule_id_clean}"
            neg_label = f"Negative test for {rule_id} ({dtype})"
            ttl += generate_entity_ttl(
                neg_id, entity_type,
                template["default_negative"],
                neg_label
            )
            negative_count += 1
    
    # Add summary comment
    ttl += f"""
# =============================================================================
# SUMMARY
# =============================================================================
# Positive test entities (should conform): {positive_count}
# Negative test entities (should violate): {negative_count}
# Skipped (no formalization): {skipped}
# Total entities: {positive_count + negative_count}
#
# Entity types used:
"""
    for etype, count in sorted(entities_by_type.items(), key=lambda x: -x[1]):
        ttl += f"#   {etype}: {count}\n"
    
    ttl += "# =============================================================================\n"
    
    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ttl)
    
    print(f"\n✅ Generated TDD test data: {output_path}")
    print(f"   Positive entities: {positive_count}")
    print(f"   Negative entities: {negative_count}")
    print(f"   Skipped: {skipped}")
    print(f"   Total: {positive_count + negative_count}")
    
    return {
        "positive_count": positive_count,
        "negative_count": negative_count,
        "skipped": skipped,
        "entities_by_type": entities_by_type,
        "output_file": str(output_path),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate TDD test data")
    parser.add_argument("--output", "-o", type=Path, default=None,
                       help="Output path (default: shacl/tdd_test_data.ttl)")
    args = parser.parse_args()
    
    generate_test_data(args.output)
