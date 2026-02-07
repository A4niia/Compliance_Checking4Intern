#!/usr/bin/env python3
"""
Improved LLM Annotation Script with Connection Verification
============================================================
This script ensures REAL LLM classification (not fallback) and proper
error handling for thesis research validation.

Usage:
    python scripts/populate_llm_annotations_v2.py --test-connection
    python scripts/populate_llm_annotations_v2.py --run

Output:
    - research/gold_standard_annotated.json
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://10.99.200.2:11434")
MODEL = "mistral"  # Best performing model based on comparison


def test_ollama_connection(host: str = OLLAMA_HOST) -> bool:
    """Test connection to Ollama server and verify model availability."""
    print(f"\n🔍 Testing connection to Ollama at {host}...")
    
    try:
        # Test basic connection
        response = requests.get(f"{host}/api/tags", timeout=10)
        if response.status_code != 200:
            print(f"   ❌ Server responded with status {response.status_code}")
            return False
        
        # Check available models
        models = [m["name"] for m in response.json().get("models", [])]
        print(f"   ✅ Connected! Available models: {len(models)}")
        
        # Check if target model is available
        if MODEL in models or any(MODEL in m for m in models):
            print(f"   ✅ Model '{MODEL}' is available")
        else:
            print(f"   ⚠️ Model '{MODEL}' not found. Available: {models[:5]}")
            return False
        
        # Test actual generation
        print(f"   🧪 Testing generation with {MODEL}...")
        test_response = requests.post(
            f"{host}/api/generate",
            json={
                "model": MODEL,
                "prompt": "Reply with only the word: OK",
                "temperature": 0.0,
                "stream": False
            },
            timeout=60
        )
        
        if test_response.status_code == 200:
            # Ollama may return NDJSON (newline-delimited JSON)
            response_text = test_response.text.strip()
            
            # Try to parse as single JSON first
            try:
                result_json = json.loads(response_text)
                result = result_json.get("response", "")
            except json.JSONDecodeError:
                # Parse as NDJSON (multiple JSON objects, one per line)
                result = ""
                for line in response_text.split('\n'):
                    if line.strip():
                        try:
                            line_json = json.loads(line)
                            result += line_json.get("response", "")
                        except json.JSONDecodeError:
                            pass
            
            print(f"   ✅ Model responded: {result[:50]}")
            return True
        else:
            print(f"   ❌ Generation failed: {test_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection error: {e}")
        return False
    except requests.exceptions.Timeout:
        print(f"   ❌ Connection timeout after 10 seconds")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def post_process_classification(result: dict, text: str) -> dict:
    """
    Post-process LLM classification to fix common errors.
    
    Fixes:
    1. Null rule_type when is_rule=True → infer from deontic marker
    2. "should" false positives → downgrade confidence, mark as not-rule if advisory
    3. Consequence statements → map to prohibition
    """
    import re
    text_lower = text.lower()
    
    # Fix 1: Resolve null rule_type
    if result.get("is_rule") and result.get("rule_type") is None:
        marker = result.get("deontic_marker", "").lower() if result.get("deontic_marker") else ""
        if not marker:
            # Try to find marker in text
            for m in ["must", "shall", "required", "have to", "has to"]:
                if m in text_lower:
                    marker = m
                    break
            for m in ["may not", "cannot", "shall not", "prohibited"]:
                if m in text_lower:
                    marker = m
                    break
            for m in ["may", "can"]:
                if m in text_lower:
                    marker = m
                    break
        
        if marker in ["may not", "cannot", "shall not", "prohibited", "must not"]:
            result["rule_type"] = "prohibition"
        elif marker in ["may", "can"]:
            # Check if consequence pattern: "may result in", "may be fined"
            if re.search(r'may\s+(result|lead|be\s+(fined|locked|dismissed|cancelled|terminated))', text_lower):
                result["rule_type"] = "prohibition"
            else:
                result["rule_type"] = "permission"
        else:
            result["rule_type"] = "obligation"
        result["post_processed"] = "null_type_resolved"
    
    # Fix 2: "should" false positive detection
    if result.get("is_rule") and "should" in text_lower:
        # Patterns that indicate advisory/recommendation (NOT binding rules)
        advisory_patterns = [
            r'should\s+consider',
            r'should\s+be\s+available',
            r'should\s+normally',
            r'should\s+proceed\s+to',
            r'should\s+seek',
            r'should\s+receive\s+preference',
            r'should\s+be\s+(supported|completed|reported|directed|held)',
        ]
        
        is_advisory = any(re.search(p, text_lower) for p in advisory_patterns)
        
        # Also check: "should not" is more likely a real prohibition
        has_should_not = "should not" in text_lower or "shouldn't" in text_lower
        
        if is_advisory and not has_should_not:
            result["is_rule"] = False
            result["rule_type"] = None
            result["confidence"] = max(result.get("confidence", 0) - 0.3, 0.3)
            result["post_processed"] = "should_advisory_filtered"
    
    # Fix 3: Consequence statements → prohibition
    if result.get("is_rule"):
        consequence_patterns = [
            r'may\s+result\s+in',
            r'will\s+be\s+fined',
            r'may\s+face\s+a\s+fine',
            r'shall\s+be\s+recommended\s+for\s+dismissal',
        ]
        if any(re.search(p, text_lower) for p in consequence_patterns):
            if result.get("rule_type") != "prohibition":
                result["rule_type"] = "prohibition"
                result["post_processed"] = "consequence_to_prohibition"
    
    return result


def classify_rule_strict(text: str, model: str = MODEL) -> dict:
    """
    Classify a text as a policy rule using LLM.
    STRICT MODE: Raises exception if LLM is not available (no fallback).
    Includes improved prompt with better "should" handling and post-processing.
    """
    prompt = f"""Analyze the following text from an academic policy document.

TASK: Determine if this is a policy RULE (normative statement) or not.

DEFINITION of a Policy Rule:
- Contains a DEONTIC operator (must, shall, may, required, prohibited, cannot)
- Specifies an OBLIGATION (what must be done), PERMISSION (what may be done), or PROHIBITION (what cannot be done)
- Has a clear SUBJECT (who the rule applies to)
- Has actionable REQUIREMENTS (specific actions or behaviors)

CRITICAL GUIDANCE on "should":
- "Should" is OFTEN advisory/recommendatory, NOT a binding rule
- "Should" IS a rule ONLY when combined with strong enforcement language (penalties, consequences)
- "Should not" with clear prohibition intent IS a rule (prohibition)
- When in doubt about "should" statements, classify as NOT a rule

EXAMPLES:
1. "Students must submit their thesis by May 15th" → is_rule: true, obligation (strong "must")
2. "Faculty may request additional office space" → is_rule: true, permission (grants right)
3. "Students shall not disturb fellow students" → is_rule: true, prohibition (clear "shall not")
4. "Plagiarism is strictly prohibited" → is_rule: true, prohibition
5. "Students should consider attending workshops" → is_rule: false (recommendation only)
6. "Hearings should normally be held within ten days" → is_rule: false (advisory "should normally")
7. "The settlement should be supported by receipts" → is_rule: false (recommendation, not mandatory)
8. "The appeal should be addressed to the VP" → is_rule: false (guidance, not binding)
9. "The university provides library resources" → is_rule: false (factual description)

RULE TYPE must always be specified when is_rule is true. Never leave rule_type as null:
- If text uses "must/shall/required/have to" → obligation
- If text uses "may/can" (granting ability) → permission
- If text uses "shall not/cannot/may not/prohibited" → prohibition
- If text describes consequences ("may result in", "will be fined") → prohibition

Text to analyze:
"{text}"

Respond with ONLY a JSON object (no explanation before or after):
{{
    "is_rule": true or false,
    "rule_type": "obligation" | "permission" | "prohibition" | null,
    "confidence": 0.0 to 1.0,
    "deontic_marker": "the specific word like must/shall/may" | null,
    "subject": "who this applies to" | null,
    "reasoning": "one sentence explanation"
}}

JSON:"""

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,  # For reproducibility
                    "seed": 42,          # Fixed seed for deterministic output
                    "num_predict": 800
                }
            },
            timeout=120
        )
        response.raise_for_status()
        
        result_text = response.json().get("response", "")
        
        # Parse JSON from response with improved regex
        import re
        # Try to match complete JSON object (handles nested structures)
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                # Apply post-processing fixes
                result = post_process_classification(result, text)
                return result
            except json.JSONDecodeError:
                # If full match fails, try simpler pattern
                json_match = re.search(r'\{[^{}]*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    result = post_process_classification(result, text)
                    return result
        
        # If no JSON found, show more of the response for debugging
        raise ValueError(f"Could not parse JSON from response: {result_text[:400]}")
        
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Cannot connect to Ollama at {OLLAMA_HOST}")
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse error: {e}. Response was: {result_text[:400]}")


def load_gold_standard():
    """Load the gold standard template."""
    gs_file = RESEARCH_DIR / "gold_standard_template.json"
    
    if not gs_file.exists():
        print(f"❌ Gold standard file not found: {gs_file}")
        sys.exit(1)
    
    with open(gs_file, "r", encoding="utf-8") as f:
        return json.load(f)


def populate_annotations_strict(gold_standard: list) -> list:
    """Populate LLM annotations for all rules (STRICT - no fallback)."""
    print("\n🤖 Populating LLM annotations (STRICT MODE)...")
    print(f"   Model: {MODEL}")
    print(f"   Ollama Host: {OLLAMA_HOST}")
    print(f"   Total rules: {len(gold_standard)}")
    print("-" * 60)
    
    annotated = []
    success_count = 0
    error_count = 0
    
    for i, rule in enumerate(gold_standard):
        rule_id = rule.get("id", f"Unknown-{i}")
        text = rule.get("original_text", "")
        
        print(f"   [{i+1:3d}/{len(gold_standard)}] {rule_id}...", end=" ", flush=True)
        
        try:
            result = classify_rule_strict(text)
            success_count += 1
            
            # Add LLM annotation
            rule["llm_annotation"] = {
                "is_rule": result.get("is_rule", False),
                "rule_type": result.get("rule_type"),
                "confidence": result.get("confidence", 0.0),
                "deontic_marker": result.get("deontic_marker"),
                "subject": result.get("subject"),
                "reasoning": result.get("reasoning", ""),
                "model": MODEL,
                "annotation_date": datetime.now().isoformat(),
                "method": "llm"  # Mark as actual LLM, not fallback
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
            
            print(f"{status} ({result.get('rule_type', 'none')})")
            
        except Exception as e:
            error_count += 1
            print(f"❌ Error: {str(e)[:50]}")
            
            # Mark as error, but continue
            rule["llm_annotation"] = {
                "is_rule": None,
                "error": str(e),
                "model": MODEL,
                "annotation_date": datetime.now().isoformat(),
                "method": "error"
            }
            rule["human_llm_agreement"] = None
        
        annotated.append(rule)
    
    print("\n" + "-" * 60)
    print(f"   Success: {success_count}/{len(gold_standard)}")
    print(f"   Errors: {error_count}/{len(gold_standard)}")
    
    return annotated


def save_annotated(annotated: list) -> Path:
    """Save annotated gold standard."""
    output_file = RESEARCH_DIR / "gold_standard_annotated.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(annotated, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved annotated gold standard: {output_file}")
    return output_file


def calculate_agreement_stats(annotated: list) -> dict:
    """Calculate agreement statistics."""
    total = len(annotated)
    
    # Count by method
    llm_method = sum(1 for r in annotated if r.get("llm_annotation", {}).get("method") == "llm")
    error_method = sum(1 for r in annotated if r.get("llm_annotation", {}).get("method") == "error")
    
    agreed = sum(1 for r in annotated if r.get("human_llm_agreement") == True)
    disagreed = sum(1 for r in annotated if r.get("human_llm_agreement") == False)
    
    agreement_rate = agreed / (agreed + disagreed) if (agreed + disagreed) > 0 else 0
    
    # Count by rule type
    rule_types = {}
    for r in annotated:
        rt = r.get("llm_annotation", {}).get("rule_type")
        if rt:
            rule_types[rt] = rule_types.get(rt, 0) + 1
    
    return {
        "total_rules": total,
        "llm_annotated": llm_method,
        "errors": error_method,
        "agreed": agreed,
        "disagreed": disagreed,
        "agreement_rate": round(agreement_rate * 100, 2),
        "rule_types": rule_types
    }


def main():
    """Main execution flow."""
    global OLLAMA_HOST  # Declare global before first use
    
    parser = argparse.ArgumentParser(description="LLM Annotation with Connection Verification")
    parser.add_argument("--test-connection", action="store_true", help="Test Ollama connection only")
    parser.add_argument("--run", action="store_true", help="Run annotation (requires successful connection)")
    parser.add_argument("--host", default=OLLAMA_HOST, help=f"Ollama host (default: {OLLAMA_HOST})")
    args = parser.parse_args()
    
    OLLAMA_HOST = args.host
    
    print("=" * 60)
    print("LLM ANNOTATION (STRICT MODE - NO FALLBACK)")
    print("=" * 60)
    
    if args.test_connection or not args.run:
        if not test_ollama_connection():
            print("\n❌ Connection test failed!")
            print("   Please ensure:")
            print(f"   1. Ollama is running at {OLLAMA_HOST}")
            print(f"   2. Model '{MODEL}' is available")
            print("   3. Network access is allowed")
            return 1
        
        if not args.run:
            print("\n✅ Connection test passed!")
            print("   Run with --run flag to populate annotations")
            return 0
    
    # Test connection before running
    if args.run:
        if not test_ollama_connection():
            print("\n❌ Cannot run without valid Ollama connection!")
            return 1
        
        # Load gold standard
        gold_standard = load_gold_standard()
        print(f"\n📋 Loaded {len(gold_standard)} rules from gold standard")
        
        # Populate annotations
        annotated = populate_annotations_strict(gold_standard)
        
        # Calculate stats
        stats = calculate_agreement_stats(annotated)
        
        print("\n" + "=" * 60)
        print("ANNOTATION STATISTICS")
        print("=" * 60)
        print(f"""
    Total Rules:        {stats['total_rules']}
    LLM Annotated:      {stats['llm_annotated']}
    Errors:             {stats['errors']}
    Agreed:             {stats['agreed']}
    Disagreed:          {stats['disagreed']}
    Agreement Rate:     {stats['agreement_rate']}%
    
    Rule Types:         {json.dumps(stats['rule_types'], indent=8)}
""")
        
        # Save results
        save_annotated(annotated)
        
        print("\n✅ Annotation complete!")
        print("   Run 'python scripts/calculate_irr.py' for Cohen's Kappa")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
