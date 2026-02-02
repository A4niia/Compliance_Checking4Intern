#!/usr/bin/env python3
"""
Permission Classification Experiments
======================================
Test different prompts and methods to improve permission classification
from current 36% to target 70%+.

Usage:
    python scripts/permission_experiments.py --experiment E1 --verbose
    python scripts/permission_experiments.py --all
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import argparse

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://10.99.200.2:11434")
MODEL = "mistral"

# ====================
# PROMPT VARIATIONS
# ====================

PROMPTS = {
    "E0_baseline": """Analyze the following text from an academic policy document.

TASK: Determine if this is a policy RULE or not.

DEFINITION of a Policy Rule:
- Contains a DEONTIC operator (must, shall, may, should, required, prohibited, cannot)
- Specifies an OBLIGATION (what must be done), PERMISSION (what may be done), or PROHIBITION (what cannot be done)
- Has a clear SUBJECT (who the rule applies to)
- Has actionable REQUIREMENTS (specific actions)

IMPORTANT: "Should" statements are OFTEN recommendations, not binding rules. Only classify as rule if there's clear mandatory intent.

Text to analyze:
"{text}"

Respond with ONLY a JSON object (no explanation before or after):
{{
    "is_rule": true or false,
    "rule_type": "obligation" | "permission" | "prohibition" | null,
    "confidence": 0.0 to 1.0,
    "reasoning": "one sentence explanation"
}}

JSON:""",

    "E1_explicit_permission": """Analyze this text from an academic policy document.

PERMISSION RULES - Critical Distinction:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NORMATIVE PERMISSION (IS a rule):
• "may" grants institutional rights/allowances
• Example: "Students may submit extensions" ✓
• Example: "Faculty may request sabbatical" ✓

FACTUAL DESCRIPTION (NOT a rule):  
• "may" describes possibilities/contingencies
• Example: "It may rain tomorrow" ✗
• Example: "The system may experience delays" ✗

KEY INDICATOR: Institutional subject (students, faculty, staff, employees)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Text: "{text}"

Respond with JSON only:
{{
    "is_rule": true/false,
    "rule_type": "permission"/"obligation"/"prohibition"/null,
    "confidence": 0.0-1.0,
    "reasoning": "explain permission vs description distinction"
}}

JSON:""",

    "E2_context_aware": """Analyze this policy text by answering these context questions:

1. WHO has the permission/obligation? (identify subject)
2. WHAT action can they take / must they take?
3. Is this GRANTING RIGHTS or DESCRIBING POSSIBILITIES?

GUIDELINE:
- If "may" + institutional subject + action verb → Permission (grants rights)
- If "may" + state/condition description → Description (states possibility)

Text: "{text}"

Based on your answers, respond with JSON:
{{
    "is_rule": true/false,
    "rule_type": "permission"/"obligation"/"prohibition"/null,
    "confidence": 0.0-1.0,
    "subject": "who",
    "action": "what",
    "reasoning": "rights vs possibilities"
}}

JSON:""",

    "E3_contrastive_examples": """Classify this text using these examples:

PERMISSION RULES (policy grants rights):
✓ "Students may access labs after hours"
✓ "Faculty may request sabbatical leave"
✓ "Researchers may publish findings externally"

NOT RULES (descriptions of possibilities):
✗ "The system may experience downtime"
✗ "Approval may take 2-3 weeks"
✗ "Results may vary by department"

Text to classify: "{text}"

JSON only:
{{
    "is_rule": true/false,
    "rule_type": "permission"/"obligation"/"prohibition"/null,
    "confidence": 0.0-1.0,
    "reasoning": "which example is this most similar to?"
}}

JSON:""",
}


def classify_with_prompt(text: str, prompt_template: str) -> Dict:
    """Classify text using specified prompt variation."""
    prompt = prompt_template.format(text=text)
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "temperature": 0.1,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        
        # Parse NDJSON or single JSON
        response_text = response.text.strip()
        try:
            result_json = json.loads(response_text)
            result_text = result_json.get("response", "")
        except json.JSONDecodeError:
            # Try NDJSON
            result_text = ""
            for line in response_text.split('\n'):
                if line.strip():
                    try:
                        result_text += json.loads(line).get("response", "")
                    except:
                        pass
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"error": f"No JSON found in: {result_text[:200]}"}
            
    except Exception as e:
        return {"error": str(e)}


def load_permission_test_set() -> List[Dict]:
    """Load permission examples from IRR disagreements."""
    irr_file = RESEARCH_DIR / "irr_metrics.json"
    
    with open(irr_file, "r", encoding="utf-8") as f:
        irr_data = json.load(f)
    
    # Get permission disagreements (human said permission, LLM said not-rule)
    permissions = [d for d in irr_data["disagreements"] 
                   if d.get("human_type") == "permission"]
    
    return permissions


def run_experiment(experiment_id: str, test_set: List[Dict], verbose: bool = False) -> Dict:
    """Run single experiment condition."""
    if experiment_id not in PROMPTS:
        raise ValueError(f"Unknown experiment: {experiment_id}")
    
    prompt_template = PROMPTS[experiment_id]
    results = []
    
    print(f"\n🧪 Running {experiment_id}...")
    print(f"   Test set size: {len(test_set)}")
    print("-" * 60)
    
    correct = 0
    for i, example in enumerate(test_set):
        text = example["text"]
        true_label = example["human"]  # True if permission
        
        if verbose:
            print(f"[{i+1}/{len(test_set)}] {example['rule_id']}...", end=" ", flush=True)
        
        # Classify
        result = classify_with_prompt(text, prompt_template)
        
        # Check correctness
        predicted_is_rule = result.get("is_rule", False)
        predicted_type = result.get("rule_type")
        
        is_correct = (predicted_is_rule == true_label and 
                     predicted_type == "permission")
        
        if is_correct:
            correct += 1
            if verbose:
                print("✅")
        else:
            if verbose:
                print(f"❌ (predicted: {predicted_type})")
        
        results.append({
            "rule_id": example["rule_id"],
            "text": text[:80],
            "true_label": true_label,
            "predicted_is_rule": predicted_is_rule,
            "predicted_type": predicted_type,
            "correct": is_correct,
            "reasoning": result.get("reasoning", "")
        })
    
    accuracy = correct / len(test_set) * 100
    print(f"\n   ✓ Correct: {correct}/{len(test_set)}")
    print(f"   📊 Accuracy: {accuracy:.1f}%")
    
    return {
        "experiment_id": experiment_id,
        "accuracy": accuracy,
        "correct": correct,
        "total": len(test_set),
        "results": results
    }


def calculate_metrics(results: List[Dict]) -> Dict:
    """Calculate precision, recall, F1."""
    TP = sum(1 for r in results if r["true_label"] and r["predicted_is_rule"] and r["predicted_type"] == "permission")
    FP = sum(1 for r in results if not r["true_label"] and r["predicted_is_rule"])
    FN = sum(1 for r in results if r["true_label"] and (not r["predicted_is_rule"] or r["predicted_type"] != "permission"))
    TN = sum(1 for r in results if not r["true_label"] and not r["predicted_is_rule"])
    
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "TP": TP,
        "FP": FP, 
        "FN": FN,
        "TN": TN
    }


def main():
    parser = argparse.ArgumentParser(description="Permission Classification Experiments")
    parser.add_argument("--experiment", "-e", choices=list(PROMPTS.keys()), 
                       help="Single experiment to run")
    parser.add_argument("--all", action="store_true", help="Run all experiments")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    # Load test set
    print("📋 Loading permission test set...")
    test_set = load_permission_test_set()
    print(f"   Loaded {len(test_set)} permission examples")
    
    # Run experiments
    all_results = {}
    
    if args.all:
        experiments = list(PROMPTS.keys())
    elif args.experiment:
        experiments = [args.experiment]
    else:
        print("❌ Please specify --experiment or --all")
        return 1
    
    for exp_id in experiments:
        result = run_experiment(exp_id, test_set, verbose=args.verbose)
        metrics = calculate_metrics(result["results"])
        result["metrics"] = metrics
        all_results[exp_id] = result
    
    # Summary
    print("\n" + "=" * 60)
    print("EXPERIMENT SUMMARY")
    print("=" * 60)
    
    for exp_id, result in all_results.items():
        print(f"\n{exp_id}:")
        print(f"  Accuracy:  {result['accuracy']:.1f}%")
        print(f"  Precision: {result['metrics']['precision']:.1%}")
        print(f"  Recall:    {result['metrics']['recall']:.1%}")
        print(f"  F1-Score:  {result['metrics']['f1_score']:.1%}")
    
    # Save results
    output_file = RESEARCH_DIR / "permission_experiments_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "experiments": all_results,
            "test_set_size": len(test_set),
            "summary": {
                exp_id: {
                    "accuracy": result["accuracy"],
                    "f1": result["metrics"]["f1_score"]
                }
                for exp_id, result in all_results.items()
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved: {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
