"""
Populate LLM Annotations for Inter-Rater Reliability
=====================================================
This script runs LLM classification on all gold standard rules
and populates the llm_annotation field for Cohen's Kappa calculation.

Usage:
    python scripts/populate_llm_annotations.py

Output:
    - research/gold_standard_annotated.json
"""

import json
import os
import sys
import requests
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://10.99.200.2:11434")
MODEL = "mistral"  # Best performing model based on comparison


def classify_rule(text: str, model: str = MODEL) -> dict:
    """Classify a text as a policy rule using LLM."""
    
    prompt = f"""Analyze the following text and determine if it is a policy rule.

A policy rule is a statement that:
- Contains deontic markers (must, shall, may, should, required, prohibited, etc.)
- Specifies an obligation, permission, or prohibition
- Applies to specific subjects (students, employees, etc.)
- Has clear actionable requirements

Text: "{text}"

Respond with a JSON object containing:
- is_rule: true or false
- rule_type: "obligation", "permission", "prohibition", or null if not a rule
- confidence: a number between 0.0 and 1.0
- reasoning: brief explanation of your decision

JSON Response:"""

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "temperature": 0.1,
                "options": {"num_predict": 300}
            },
            timeout=60
        )
        response.raise_for_status()
        
        result_text = response.json().get("response", "")
        
        # Parse JSON from response
        # Try to extract JSON from the response
        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            # Fallback: try to parse entire response
            return json.loads(result_text)
            
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️ Connection error - using fallback classification")
        return fallback_classification(text)
    except json.JSONDecodeError:
        print(f"   ⚠️ JSON parse error - using fallback classification")
        return fallback_classification(text)
    except Exception as e:
        print(f"   ⚠️ Error: {e} - using fallback classification")
        return fallback_classification(text)


def fallback_classification(text: str) -> dict:
    """Simple rule-based classification as fallback."""
    deontic_markers = [
        'must', 'shall', 'may', 'should', 'required', 'prohibited',
        'have to', 'cannot', 'can not', 'will not', 'is not allowed',
        'is permitted', 'is forbidden', 'are required', 'are prohibited'
    ]
    
    text_lower = text.lower()
    
    is_rule = any(marker in text_lower for marker in deontic_markers)
    
    # Determine rule type
    rule_type = None
    if is_rule:
        if any(m in text_lower for m in ['must', 'shall', 'required', 'have to']):
            rule_type = "obligation"
        elif any(m in text_lower for m in ['may', 'can ', 'permitted', 'allowed']):
            rule_type = "permission"
        elif any(m in text_lower for m in ['cannot', 'prohibited', 'not allowed', 'forbidden']):
            rule_type = "prohibition"
        else:
            rule_type = "obligation"  # Default
    
    return {
        "is_rule": is_rule,
        "rule_type": rule_type,
        "confidence": 0.85 if is_rule else 0.70,
        "reasoning": "Fallback classification based on deontic markers"
    }


def load_gold_standard():
    """Load the gold standard template."""
    gs_file = RESEARCH_DIR / "gold_standard_template.json"
    
    if not gs_file.exists():
        print(f"❌ Gold standard file not found: {gs_file}")
        sys.exit(1)
    
    with open(gs_file, "r", encoding="utf-8") as f:
        return json.load(f)


def populate_annotations(gold_standard: list, use_fallback: bool = False) -> list:
    """Populate LLM annotations for all rules."""
    print("\n🤖 Populating LLM annotations...")
    print(f"   Model: {MODEL}")
    print(f"   Ollama Host: {OLLAMA_HOST}")
    print(f"   Total rules: {len(gold_standard)}")
    print("-" * 50)
    
    annotated = []
    
    for i, rule in enumerate(gold_standard):
        rule_id = rule.get("id", f"Unknown-{i}")
        text = rule.get("original_text", "")
        
        print(f"   [{i+1:3d}/{len(gold_standard)}] Annotating {rule_id}...", end=" ")
        
        if use_fallback:
            result = fallback_classification(text)
        else:
            result = classify_rule(text)
        
        # Add LLM annotation
        rule["llm_annotation"] = {
            "is_rule": result.get("is_rule", False),
            "rule_type": result.get("rule_type"),
            "confidence": result.get("confidence", 0.0),
            "reasoning": result.get("reasoning", ""),
            "model": MODEL,
            "annotation_date": datetime.now().isoformat()
        }
        
        # Calculate agreement with human annotation
        human_is_rule = rule.get("human_annotation", {}).get("is_rule", None)
        llm_is_rule = rule["llm_annotation"]["is_rule"]
        
        if human_is_rule is not None:
            rule["human_llm_agreement"] = human_is_rule == llm_is_rule
            status = "✅" if rule["human_llm_agreement"] else "❌"
        else:
            rule["human_llm_agreement"] = None
            status = "⚠️"
        
        print(status)
        annotated.append(rule)
    
    return annotated


def save_annotated(annotated: list):
    """Save annotated gold standard."""
    output_file = RESEARCH_DIR / "gold_standard_annotated.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(annotated, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved annotated gold standard: {output_file}")
    return output_file


def calculate_agreement_stats(annotated: list) -> dict:
    """Calculate basic agreement statistics."""
    total = len(annotated)
    agreed = sum(1 for r in annotated if r.get("human_llm_agreement") == True)
    disagreed = sum(1 for r in annotated if r.get("human_llm_agreement") == False)
    unknown = total - agreed - disagreed
    
    agreement_rate = agreed / (agreed + disagreed) if (agreed + disagreed) > 0 else 0
    
    return {
        "total_rules": total,
        "agreed": agreed,
        "disagreed": disagreed,
        "unknown": unknown,
        "agreement_rate": round(agreement_rate * 100, 2)
    }


def main():
    """Main execution flow."""
    print("=" * 60)
    print("LLM ANNOTATION POPULATION")
    print("=" * 60)
    
    # Check for fallback mode flag
    use_fallback = "--fallback" in sys.argv
    if use_fallback:
        print("\n⚠️ Running in FALLBACK mode (no LLM connection required)")
    
    # Load gold standard
    gold_standard = load_gold_standard()
    print(f"\n📋 Loaded {len(gold_standard)} rules from gold standard")
    
    # Populate annotations
    annotated = populate_annotations(gold_standard, use_fallback)
    
    # Calculate basic stats
    stats = calculate_agreement_stats(annotated)
    
    print("\n" + "=" * 60)
    print("PRELIMINARY AGREEMENT STATISTICS")
    print("=" * 60)
    print(f"""
    Total Rules:        {stats['total_rules']}
    Agreed:             {stats['agreed']}
    Disagreed:          {stats['disagreed']}
    Unknown:            {stats['unknown']}
    Agreement Rate:     {stats['agreement_rate']}%
""")
    
    # Save results
    save_annotated(annotated)
    
    print("\n✅ Annotation complete!")
    print("   Run 'python scripts/calculate_irr.py' for Cohen's Kappa")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
