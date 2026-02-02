#!/usr/bin/env python3
"""
Human Annotation Template Generator
====================================
Creates a clean template for a second human annotator.

Usage:
    python scripts/create_annotation_template.py
    
Output:
    - research/human_annotation_template.json (for second annotator)
    - research/annotation_codebook.md (guidelines)
"""

import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"


def create_annotation_template():
    """Create a blank template for second human annotator."""
    
    # Load gold standard
    gs_file = RESEARCH_DIR / "gold_standard_template.json"
    with open(gs_file, "r", encoding="utf-8") as f:
        gold_standard = json.load(f)
    
    print(f"📋 Loaded {len(gold_standard)} rules from gold standard")
    
    # Create template with original text only (no annotations visible)
    template = []
    
    for rule in gold_standard:
        template.append({
            "id": rule["id"],
            "rule_id": rule.get("rule_id", ""),
            "source_document": rule.get("source_document", ""),
            "page_number": rule.get("page_number", 0),
            "original_text": rule["original_text"],
            # Blank annotation fields for annotator to fill
            "annotation": {
                "is_rule": None,  # true/false
                "rule_type": None,  # obligation/permission/prohibition
                "deontic_marker": None,  # must/shall/may/etc.
                "subject": None,  # who this applies to
                "action": None,  # what must/may/cannot be done
                "condition": None,  # when/if clause
                "confidence": None,  # 1-5
                "notes": ""
            },
            "annotator": "",  # Annotator name
            "annotation_date": ""  # Will be filled automatically
        })
    
    # Shuffle to prevent order bias
    random.shuffle(template)
    
    # Save template
    output_file = RESEARCH_DIR / "human_annotation_template.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created annotation template: {output_file}")
    print(f"   Total items: {len(template)}")
    print("\n📝 Instructions for annotator:")
    print("   1. Read annotation_codebook.md first")
    print("   2. Fill in 'annotation' fields for each item")
    print("   3. Add your name in 'annotator' field")
    print("   4. Save as human_annotation_filled.json")
    
    return output_file


def create_sample_set(n: int = 50):
    """Create a smaller sample set for quick annotation."""
    
    gs_file = RESEARCH_DIR / "gold_standard_template.json"
    with open(gs_file, "r", encoding="utf-8") as f:
        gold_standard = json.load(f)
    
    # Stratified sampling: include examples of each type
    sample = []
    
    # Get some of each type based on human annotation
    by_type = {"obligation": [], "permission": [], "prohibition": [], "not_rule": []}
    
    for rule in gold_standard:
        human_ann = rule.get("human_annotation", {})
        if human_ann.get("is_rule"):
            rule_type = human_ann.get("rule_type", "obligation")
            if rule_type in by_type:
                by_type[rule_type].append(rule)
        else:
            by_type["not_rule"].append(rule)
    
    # Take proportional samples
    for type_name, rules in by_type.items():
        sample_size = min(len(rules), n // 4)
        sample.extend(random.sample(rules, sample_size))
    
    # Fill remaining with random
    remaining = n - len(sample)
    remaining_rules = [r for r in gold_standard if r not in sample]
    if remaining > 0 and remaining_rules:
        sample.extend(random.sample(remaining_rules, min(remaining, len(remaining_rules))))
    
    # Create template
    template = []
    for rule in sample:
        template.append({
            "id": rule["id"],
            "original_text": rule["original_text"],
            "annotation": {
                "is_rule": None,
                "rule_type": None,
                "deontic_marker": None,
                "confidence": None,
                "notes": ""
            }
        })
    
    random.shuffle(template)
    
    output_file = RESEARCH_DIR / f"annotation_sample_{n}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created sample template: {output_file}")
    print(f"   Sample size: {len(template)}")
    
    return output_file


if __name__ == "__main__":
    import sys
    
    if "--sample" in sys.argv:
        n = 50
        for arg in sys.argv:
            if arg.startswith("--n="):
                n = int(arg.split("=")[1])
        create_sample_set(n)
    else:
        create_annotation_template()
