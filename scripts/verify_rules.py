# Automated Rule Extraction and Verification System
# Uses Ollama for local LLM verification of policy rules

"""
This system:
1. Takes extracted rule candidates (from extract_rules.py)
2. Uses Ollama LLM to verify if each is a real policy rule
3. Extracts structured information (subject, condition, action, deontic)
4. Calculates evaluation metrics
5. Creates gold standard dataset

USAGE:
    python scripts/verify_rules.py --input research/extracted_rules.json
    python scripts/verify_rules.py --create-gold-standard 100
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import re

try:
    import requests
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"  # or "mistral", "phi3", etc.


# ============================================================
# PROMPTS FOR RULE VERIFICATION
# ============================================================

RULE_VERIFICATION_PROMPT = """You are an expert at identifying policy rules in academic documents.

Analyze the following text and determine:
1. Is this a policy rule? (A rule prescribes, prohibits, or permits certain actions)
2. If yes, extract the structured components.

Text: "{text}"

Respond in JSON format only:
{{
  "is_rule": true/false,
  "confidence": 0.0-1.0,
  "rule_type": "obligation" | "prohibition" | "permission" | "recommendation" | null,
  "subject": "who this applies to" | null,
  "condition": "under what circumstances" | null,
  "action": "what must/may/cannot happen" | null,
  "deontic_marker": "must/shall/may/should/etc" | null,
  "reasoning": "brief explanation of your classification"
}}

Important:
- Only classify as a rule if it clearly prescribes behavior
- Descriptive statements are NOT rules
- Definitions are NOT rules
- Historical information is NOT rules
"""

RULE_FORMALIZATION_PROMPT = """You are an expert in formal logic and policy formalization.

Given this policy rule, create a First-Order Logic (FOL) representation.

Policy Rule: "{text}"
Subject: {subject}
Condition: {condition}
Action: {action}
Rule Type: {rule_type}

Create a FOL statement using these conventions:
- ∀ for universal quantification (all)
- ∃ for existential quantification (exists)
- ∧ for conjunction (and)
- ∨ for disjunction (or)
- ¬ for negation (not)
- → for implication (if-then)
- Use CamelCase predicates like Student(x), IsPaid(o)

Respond in JSON format only:
{{
  "fol_statement": "the FOL formula",
  "predicates": ["list of predicates used"],
  "variables": {{"x": "meaning", "y": "meaning"}},
  "assumptions": ["any assumptions made"],
  "confidence": 0.0-1.0,
  "formalization_difficulty": "easy" | "medium" | "hard" | "impossible"
}}
"""


# ============================================================
# OLLAMA INTEGRATION
# ============================================================

def check_ollama_running() -> bool:
    """Check if Ollama is running locally."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_available_models() -> list:
    """Get list of available Ollama models."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except:
        pass
    return []


def query_ollama(prompt: str, model: str = MODEL_NAME, temperature: float = 0.1) -> Optional[str]:
    """Query Ollama with a prompt and return the response."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            print(f"Ollama error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return None


def parse_json_response(response: str) -> Optional[dict]:
    """Parse JSON from LLM response (handles markdown code blocks)."""
    if not response:
        return None
    
    # Try to extract JSON from markdown code block
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if json_match:
        response = json_match.group(1)
    
    # Try to find JSON object
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    return None


# ============================================================
# RULE VERIFICATION
# ============================================================

def verify_rule(text: str, model: str = MODEL_NAME) -> dict:
    """Verify if a text is a policy rule using LLM."""
    prompt = RULE_VERIFICATION_PROMPT.format(text=text)
    response = query_ollama(prompt, model)
    
    result = parse_json_response(response)
    if result is None:
        result = {
            "is_rule": None,
            "confidence": 0.0,
            "error": "Failed to parse LLM response",
            "raw_response": response
        }
    
    result["original_text"] = text
    return result


def formalize_rule(verification_result: dict, model: str = MODEL_NAME) -> dict:
    """Generate FOL formalization for a verified rule."""
    if not verification_result.get("is_rule"):
        return {"error": "Not a rule, skipping formalization"}
    
    prompt = RULE_FORMALIZATION_PROMPT.format(
        text=verification_result.get("original_text", ""),
        subject=verification_result.get("subject", "unknown"),
        condition=verification_result.get("condition", "none"),
        action=verification_result.get("action", "unknown"),
        rule_type=verification_result.get("rule_type", "unknown")
    )
    
    response = query_ollama(prompt, model)
    result = parse_json_response(response)
    
    if result is None:
        result = {
            "fol_statement": None,
            "error": "Failed to parse FOL response",
            "raw_response": response
        }
    
    return result


# ============================================================
# BATCH PROCESSING
# ============================================================

def process_extracted_rules(input_file: str, output_file: str = None, 
                           model: str = MODEL_NAME, limit: int = None):
    """Process all extracted rules through verification."""
    
    # Check Ollama
    if not check_ollama_running():
        print("❌ Ollama is not running. Please start Ollama first:")
        print("   ollama serve")
        return
    
    # Check model availability
    models = get_available_models()
    if model not in [m.split(":")[0] for m in models]:
        print(f"❌ Model '{model}' not found. Available models: {models}")
        print(f"   Pull model with: ollama pull {model}")
        return
    
    # Load extracted rules
    with open(input_file, 'r', encoding='utf-8') as f:
        rules = json.load(f)
    
    if limit:
        rules = rules[:limit]
    
    print(f"\n{'='*60}")
    print(f"RULE VERIFICATION USING {model.upper()}")
    print(f"{'='*60}")
    print(f"Total rules to process: {len(rules)}")
    
    results = []
    verified_count = 0
    not_rule_count = 0
    
    for i, rule in enumerate(rules, 1):
        print(f"\n[{i}/{len(rules)}] Processing: {rule['rule_id']}")
        print(f"   Text: {rule['original_text'][:80]}...")
        
        # Verify rule
        verification = verify_rule(rule['original_text'], model)
        
        is_rule = verification.get("is_rule", False)
        confidence = verification.get("confidence", 0)
        
        if is_rule:
            verified_count += 1
            print(f"   ✅ IS RULE (confidence: {confidence:.2f})")
            print(f"   Type: {verification.get('rule_type')}")
            
            # Formalize rule
            formalization = formalize_rule(verification, model)
            verification["formalization"] = formalization
            
            if formalization.get("fol_statement"):
                print(f"   FOL: {formalization['fol_statement'][:60]}...")
        else:
            not_rule_count += 1
            print(f"   ❌ NOT A RULE (confidence: {confidence:.2f})")
            print(f"   Reason: {verification.get('reasoning', 'N/A')}")
        
        # Merge with original data
        result = {**rule, "llm_verification": verification}
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total processed: {len(results)}")
    print(f"Verified as rules: {verified_count} ({100*verified_count/len(results):.1f}%)")
    print(f"Not rules: {not_rule_count} ({100*not_rule_count/len(results):.1f}%)")
    
    # Save results
    if output_file is None:
        output_file = RESEARCH_DIR / "verified_rules.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to: {output_file}")
    
    return results


# ============================================================
# GOLD STANDARD CREATION
# ============================================================

def create_gold_standard_template(sample_size: int = 100):
    """Create a template for gold standard annotation."""
    
    # Load extracted rules
    rules_file = RESEARCH_DIR / "extracted_rules.json"
    if not rules_file.exists():
        print(f"❌ Rules file not found: {rules_file}")
        return
    
    with open(rules_file, 'r', encoding='utf-8') as f:
        all_rules = json.load(f)
    
    # Sample rules (stratified by source document)
    from collections import defaultdict
    by_source = defaultdict(list)
    for rule in all_rules:
        by_source[rule["source_document"]].append(rule)
    
    # Proportional sampling
    sampled = []
    for source, rules in by_source.items():
        proportion = sample_size * len(rules) / len(all_rules)
        sample_n = max(1, int(proportion))
        import random
        random.seed(42)  # Reproducibility
        sampled.extend(random.sample(rules, min(sample_n, len(rules))))
    
    # Trim to exact sample size
    sampled = sampled[:sample_size]
    
    # Create gold standard template
    gold_standard = []
    for i, rule in enumerate(sampled, 1):
        gold_standard.append({
            "id": f"GS-{i:03d}",
            "rule_id": rule["rule_id"],
            "source_document": rule["source_document"],
            "page_number": rule["page_number"],
            "original_text": rule["original_text"],
            
            # Human annotation fields (to be filled)
            "human_annotation": {
                "is_rule": None,  # true/false
                "rule_type": None,  # obligation/prohibition/permission/recommendation
                "subject": None,
                "condition": None,
                "action": None,
                "deontic_marker": None,
                "annotator": "",
                "annotation_date": "",
                "confidence": None,  # 1-5
                "notes": ""
            },
            
            # LLM annotation (to be filled by verify_rules)
            "llm_annotation": None,
            
            # Agreement fields
            "human_llm_agreement": None
        })
    
    # Save template
    output_file = RESEARCH_DIR / "gold_standard_template.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(gold_standard, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Gold standard template created: {output_file}")
    print(f"   Sample size: {len(gold_standard)} rules")
    print(f"\nNext steps:")
    print("   1. Open the JSON file")
    print("   2. Fill in 'human_annotation' for each rule")
    print("   3. Run verification to get 'llm_annotation'")
    print("   4. Calculate agreement metrics")
    
    return gold_standard


# ============================================================
# EVALUATION METRICS
# ============================================================

def calculate_metrics(gold_standard_file: str):
    """Calculate precision, recall, F1 and Cohen's Kappa."""
    try:
        from sklearn.metrics import precision_recall_fscore_support, cohen_kappa_score
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "scikit-learn", "-q"])
        from sklearn.metrics import precision_recall_fscore_support, cohen_kappa_score
    
    with open(gold_standard_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    human_labels = []
    llm_labels = []
    
    for item in data:
        human = item.get("human_annotation", {}).get("is_rule")
        llm = item.get("llm_annotation", {}).get("is_rule")
        
        if human is not None and llm is not None:
            human_labels.append(1 if human else 0)
            llm_labels.append(1 if llm else 0)
    
    if not human_labels:
        print("❌ No completed annotations found")
        return
    
    # Calculate metrics (LLM as prediction, human as ground truth)
    precision, recall, f1, _ = precision_recall_fscore_support(
        human_labels, llm_labels, average='binary'
    )
    
    kappa = cohen_kappa_score(human_labels, llm_labels)
    
    print(f"\n{'='*60}")
    print("EVALUATION METRICS")
    print(f"{'='*60}")
    print(f"Sample size: {len(human_labels)}")
    print(f"Precision:   {precision:.4f}")
    print(f"Recall:      {recall:.4f}")
    print(f"F1 Score:    {f1:.4f}")
    print(f"Cohen's κ:   {kappa:.4f}")
    
    # Interpret Kappa
    if kappa >= 0.8:
        kappa_interpretation = "Almost perfect agreement"
    elif kappa >= 0.6:
        kappa_interpretation = "Substantial agreement"
    elif kappa >= 0.4:
        kappa_interpretation = "Moderate agreement"
    elif kappa >= 0.2:
        kappa_interpretation = "Fair agreement"
    else:
        kappa_interpretation = "Slight agreement"
    
    print(f"   → {kappa_interpretation}")
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "cohen_kappa": kappa,
        "sample_size": len(human_labels)
    }


# ============================================================
# MAIN
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Rule Verification System")
    parser.add_argument("--input", help="Input JSON file with extracted rules")
    parser.add_argument("--output", help="Output file for verified rules")
    parser.add_argument("--model", default=MODEL_NAME, help="Ollama model to use")
    parser.add_argument("--limit", type=int, help="Limit number of rules to process")
    parser.add_argument("--create-gold-standard", type=int, metavar="N",
                       help="Create gold standard template with N samples")
    parser.add_argument("--evaluate", help="Calculate metrics from gold standard file")
    
    args = parser.parse_args()
    
    if args.create_gold_standard:
        create_gold_standard_template(args.create_gold_standard)
    elif args.evaluate:
        calculate_metrics(args.evaluate)
    elif args.input:
        process_extracted_rules(args.input, args.output, args.model, args.limit)
    else:
        # Default: process extracted rules
        input_file = RESEARCH_DIR / "extracted_rules.json"
        if input_file.exists():
            process_extracted_rules(str(input_file), model=args.model, limit=args.limit)
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
