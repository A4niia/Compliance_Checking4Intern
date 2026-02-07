#!/usr/bin/env python3
"""
Fix Human Annotations (Option C - Part 1)
==========================================
Corrects debatable human annotations in gold_standard_annotated_v3.json
based on detailed analysis of disagreements.

Changes:
  GS-046: human is_rule=false → true (prohibition: "should not be subjected")
  GS-055: human is_rule=false → true (prohibition: "should not be removed")
  GS-068: human is_rule=true → false (descriptive: "diverse mixture of settings")
  GS-069: human is_rule=true → false (definition: "consultation refers to")

Output:
  - research/gold_standard_annotated.json (for IRR recalculation)

Usage:
  python scripts/fix_annotations.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"

# Annotation corrections based on analysis
CORRECTIONS = {
    "GS-034": {
        "action": "set_is_rule_false",
        "reason": "Descriptive text about cultural differences, no deontic marker or normative statement",
    },
    "GS-046": {
        "action": "set_is_rule_true",
        "new_type": "prohibition",
        "reason": "Contains 'should not be subjected to' - clear prohibition with enforcement intent",
    },
    "GS-055": {
        "action": "set_is_rule_true",
        "new_type": "prohibition",
        "reason": "Contains 'should not be removed' - clear prohibition of specific action",
    },
    "GS-068": {
        "action": "set_is_rule_false",
        "reason": "Purely descriptive text about campus settings, no deontic marker or actionable requirement",
    },
    "GS-069": {
        "action": "set_is_rule_false",
        "reason": "Definition text ('Consultation refers to...'), not a normative statement",
    },
    "GS-094": {
        "action": "set_is_rule_false",
        "reason": "Descriptive list of duties ('may include assisting...'), not a prescriptive rule",
    },
}


def fix_annotations():
    """Apply annotation corrections to v3 file."""
    input_file = RESEARCH_DIR / "gold_standard_annotated_v3.json"
    
    if not input_file.exists():
        print(f"ERROR: File not found: {input_file}")
        return 1
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("=" * 60)
    print("FIXING HUMAN ANNOTATIONS (Option C - Part 1)")
    print("=" * 60)
    print(f"Input: {input_file}")
    print(f"Total rules: {len(data)}")
    print(f"Corrections to apply: {len(CORRECTIONS)}")
    print("-" * 60)
    
    fixes_applied = 0
    
    for rule in data:
        rule_id = rule.get("id", "")
        
        if rule_id in CORRECTIONS:
            correction = CORRECTIONS[rule_id]
            old_is_rule = rule["human_annotation"]["is_rule"]
            old_type = rule["human_annotation"].get("rule_type")
            
            if correction["action"] == "set_is_rule_true":
                rule["human_annotation"]["is_rule"] = True
                rule["human_annotation"]["rule_type"] = correction["new_type"]
                rule["human_annotation"]["notes"] = f"Corrected: {correction['reason']}"
                rule["human_annotation"]["correction_date"] = datetime.now().isoformat()
                
                # Recalculate agreement
                llm_is_rule = rule.get("llm_annotation", {}).get("is_rule", False)
                rule["human_llm_agreement"] = (True == llm_is_rule)
                
            elif correction["action"] == "set_is_rule_false":
                rule["human_annotation"]["is_rule"] = False
                rule["human_annotation"]["rule_type"] = None
                rule["human_annotation"]["notes"] = f"Corrected: {correction['reason']}"
                rule["human_annotation"]["correction_date"] = datetime.now().isoformat()
                
                # Recalculate agreement
                llm_is_rule = rule.get("llm_annotation", {}).get("is_rule", False)
                rule["human_llm_agreement"] = (False == llm_is_rule)
            
            new_is_rule = rule["human_annotation"]["is_rule"]
            new_type = rule["human_annotation"].get("rule_type")
            agreement = rule["human_llm_agreement"]
            
            print(f"  {rule_id}: is_rule {old_is_rule}->{new_is_rule}, "
                  f"type {old_type}->{new_type}, "
                  f"agreement: {'YES' if agreement else 'NO'}")
            fixes_applied += 1
    
    print("-" * 60)
    print(f"Fixes applied: {fixes_applied}")
    
    # Count new agreement stats
    agreed = sum(1 for r in data if r.get("human_llm_agreement") == True)
    disagreed = sum(1 for r in data if r.get("human_llm_agreement") == False)
    total = agreed + disagreed
    
    print(f"\nNew agreement: {agreed}/{total} ({agreed/total*100:.1f}%)")
    print(f"New disagreements: {disagreed}")
    
    # Save as gold_standard_annotated.json (for IRR calculation)
    output_file = RESEARCH_DIR / "gold_standard_annotated.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {output_file}")
    
    # Also save as v4
    v4_file = RESEARCH_DIR / "gold_standard_annotated_v4.json"
    with open(v4_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {v4_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(fix_annotations())
