#!/usr/bin/env python3
"""
FOL (First-Order Logic) Generation Script v4
Uses Mistral to generate formal logic representations of policy rules.

V4 CHANGES:
- Uses gold_standard_annotated_v4.json as input (not model_comparison_results.json)
- Filters to llm_annotation.is_rule == True (81 rules)
- Uses existing llm_annotation.rule_type for deontic classification
- Outputs to fol_formalization_v4_results.json

Usage:
    python scripts/generate_fol_v4.py --ollama-url http://10.99.200.2:11434
"""

import json
import argparse
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "requests", "-q"])
    import requests

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"

# Best model from comparison
MODEL = "mistral"

# Improved Deontic Logic Prompt with Temporal Extension
IMPROVED_PROMPT = """You are an expert in deontic logic and policy formalization.

Formalize this policy rule. KEEP YOUR RESPONSE UNDER 400 CHARACTERS.

Policy Rule: "{text}"

The rule has already been classified as: {deontic_type}

Deontic operators:
- O(φ) = Obligation (must)
- P(φ) = Permission (may)  
- F(φ) = Prohibition (cannot/shall not)

Temporal predicates (use if time-related):
- Within(n, unit, action) for deadlines
- Before(event1, event2) for ordering

FOL operators: forall, exists, implies, and, or, not

IMPORTANT: Use simple predicate names (no special characters, no underscores with backslash).

Return ONLY valid JSON (no markdown):
{{"deontic_type": "{deontic_type}", "deontic_formula": "short formula", "fol_expansion": "expanded formula", "shacl_hint": "brief hint", "explanation": "1 sentence"}}
"""


def query_ollama(prompt: str, ollama_url: str, model: str = MODEL, retries: int = 2) -> Optional[str]:
    """Query Ollama API with increased response length."""
    for attempt in range(retries):
        try:
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,  # Deterministic output
                        "seed": 42,          # Fixed seed for reproducibility
                        "num_predict": 1024,  # Increased from default ~128
                        "stop": ["\n\n"]  # Stop at double newline
                    }
                },
                timeout=180
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            time.sleep(1)
    return None


def clean_json_string(s: str) -> str:
    """Clean LLM response for JSON parsing."""
    # Remove markdown code blocks
    s = re.sub(r'```(?:json)?\s*', '', s)
    s = re.sub(r'```', '', s)
    
    # Fix LaTeX escapes that break JSON
    s = s.replace("\\_", "_")
    s = s.replace("\\n", " ")
    s = s.replace("\\\\", "\\")
    
    # Fix common Unicode issues
    s = s.replace("∧", " and ")
    s = s.replace("∨", " or ")
    s = s.replace("→", " implies ")
    s = s.replace("¬", "not ")
    s = s.replace("∀", "forall ")
    s = s.replace("∃", "exists ")
    
    # Remove control characters
    s = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', s)
    
    return s.strip()


def parse_json_response(response: str) -> Optional[dict]:
    """Robust JSON parsing with multiple fallback strategies."""
    if not response:
        return None
    
    # Strategy 1: Direct parse
    try:
        return json.loads(response)
    except:
        pass
    
    # Strategy 2: Clean and parse
    cleaned = clean_json_string(response)
    try:
        return json.loads(cleaned)
    except:
        pass
    
    # Strategy 3: Extract JSON object
    json_match = re.search(r'\{[^{}]*\}', cleaned, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    
    # Strategy 4: Find outermost braces
    try:
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            candidate = cleaned[start:end+1]
            # Fix common JSON issues
            candidate = re.sub(r',\s*}', '}', candidate)
            return json.loads(candidate)
    except:
        pass
    
    # Strategy 5: Manual extraction of key fields
    try:
        result = {}
        
        # Extract deontic_type
        type_match = re.search(r'"deontic_type"\s*:\s*"(obligation|permission|prohibition)"', cleaned)
        if type_match:
            result["deontic_type"] = type_match.group(1)
        
        # Extract deontic_formula
        formula_match = re.search(r'"deontic_formula"\s*:\s*"([^"]+)"', cleaned)
        if formula_match:
            result["deontic_formula"] = formula_match.group(1)
        
        # Extract fol_expansion
        fol_match = re.search(r'"fol_expansion"\s*:\s*"([^"]+)"', cleaned)
        if fol_match:
            result["fol_expansion"] = fol_match.group(1)
        
        if result:
            result["parsed_manually"] = True
            return result
    except:
        pass
    
    return None


def generate_fol(rule_text: str, deontic_type: str, ollama_url: str) -> dict:
    """Generate FOL for a single rule with improved handling."""
    # Truncate very long rules
    if len(rule_text) > 300:
        rule_text = rule_text[:300] + "..."
    
    prompt = IMPROVED_PROMPT.format(text=rule_text, deontic_type=deontic_type)
    response = query_ollama(prompt, ollama_url)
    result = parse_json_response(response)
    
    if result is None:
        # Retry with simpler prompt
        simple_prompt = f"""Convert to deontic logic JSON: "{rule_text[:150]}"
The rule is a {deontic_type}.
Return: {{"deontic_type": "{deontic_type}", "deontic_formula": "...", "explanation": "..."}}"""
        
        response = query_ollama(simple_prompt, ollama_url)
        result = parse_json_response(response)
    
    if result is None:
        result = {
            "error": "Failed to parse response",
            "raw_response": response[:300] if response else None,
            "recoverable": True,
            "deontic_type": deontic_type  # Use pre-classified type
        }
    
    # Ensure deontic_type is consistent with pre-classification
    if "deontic_type" not in result or not result["deontic_type"]:
        result["deontic_type"] = deontic_type
    
    return result


def process_rules_v4(ollama_url: str, limit: int = None):
    """Process rules from gold_standard_annotated_v4.json and generate FOL."""
    print(f"\n{'='*60}")
    print("FOL GENERATION v4 - USING V4 GOLD STANDARD")
    print(f"{'='*60}")
    print(f"Model: {MODEL}")
    print(f"Ollama URL: {ollama_url}")
    print(f"Input: gold_standard_annotated_v4.json")
    print(f"Filter: llm_annotation.is_rule == True")
    print(f"{'='*60}\n")
    
    # Load v4 gold standard
    gold_file = RESEARCH_DIR / "gold_standard_annotated_v4.json"
    if not gold_file.exists():
        print(f"Error: {gold_file} not found.")
        return
    
    with open(gold_file, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)
    
    # Filter to LLM-classified rules only
    llm_rules = [
        r for r in gold_data 
        if r.get('llm_annotation', {}).get('is_rule') == True
    ]
    
    print(f"Total entries in v4: {len(gold_data)}")
    print(f"LLM-classified as rules: {len(llm_rules)}")
    
    if limit:
        llm_rules = llm_rules[:limit]
        print(f"Processing limited to: {limit}")
    
    print(f"\nProcessing {len(llm_rules)} rules...\n")
    
    fol_results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": MODEL,
            "version": "v4_gold_standard",
            "ollama_url": ollama_url,
            "input_file": "gold_standard_annotated_v4.json",
            "total_candidates": len(gold_data),
            "total_rules": len(llm_rules),
            "filter": "llm_annotation.is_rule == True"
        },
        "formalized_rules": [],
        "statistics": {
            "success": 0,
            "failed": 0,
            "manual_parse": 0,
            "by_type": {
                "obligation": 0,
                "permission": 0,
                "prohibition": 0
            }
        }
    }
    
    for i, rule in enumerate(llm_rules, 1):
        rule_id = rule.get("id")
        original_text = rule.get("original_text")
        
        # Get deontic type from LLM annotation
        llm_annotation = rule.get('llm_annotation', {})
        deontic_type = llm_annotation.get('rule_type', 'obligation')
        
        print(f"[{i}/{len(llm_rules)}] {rule_id}")
        print(f"  Text: {original_text[:50]}...")
        print(f"  Pre-classified as: {deontic_type}")
        
        # Generate FOL
        fol = generate_fol(original_text, deontic_type, ollama_url)
        
        # Track statistics
        if "error" in fol:
            fol_results["statistics"]["failed"] += 1
            status = "❌ FAILED"
        elif fol.get("parsed_manually"):
            fol_results["statistics"]["manual_parse"] += 1
            fol_results["statistics"]["success"] += 1
            status = "⚠️ MANUAL PARSE"
        else:
            fol_results["statistics"]["success"] += 1
            status = "✅ SUCCESS"
        
        # Track by type
        final_type = fol.get('deontic_type', deontic_type)
        if final_type in fol_results["statistics"]["by_type"]:
            fol_results["statistics"]["by_type"][final_type] += 1
        
        print(f"  Status: {status}")
        formula = fol.get('deontic_formula', fol.get('fol_formula', 'Error'))
        if formula:
            print(f"  FOL: {str(formula)[:50]}...")
        print()
        
        fol_results["formalized_rules"].append({
            "id": rule_id,
            "original_text": original_text,
            "llm_annotation": llm_annotation,
            "fol_formalization": fol
        })
        
        time.sleep(0.3)
    
    # Calculate success rate
    total = fol_results["statistics"]["success"] + fol_results["statistics"]["failed"]
    success_rate = (fol_results["statistics"]["success"] / total * 100) if total > 0 else 0
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Success: {fol_results['statistics']['success']}")
    print(f"⚠️ Manual Parse: {fol_results['statistics']['manual_parse']}")
    print(f"❌ Failed: {fol_results['statistics']['failed']}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    print(f"\n📊 By Deontic Type:")
    for dtype, count in fol_results["statistics"]["by_type"].items():
        print(f"   {dtype.capitalize()}: {count}")
    print(f"{'='*60}\n")
    
    # Save results
    output_file = RESEARCH_DIR / "fol_formalization_v4_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fol_results, f, indent=2, ensure_ascii=False)
    print(f"💾 Results saved: {output_file}")
    
    # Generate report
    report = generate_fol_report(fol_results)
    report_file = RESEARCH_DIR / "fol_formalization_v4_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📝 Report saved: {report_file}")
    
    return fol_results


def generate_fol_report(results: dict) -> str:
    """Generate markdown report."""
    stats = results["statistics"]
    meta = results["metadata"]
    
    report = f"""# FOL Formalization Report v4

## Metadata
- **Timestamp**: {meta['timestamp']}
- **Model**: {meta['model']}
- **Input**: {meta['input_file']}
- **Total Candidates**: {meta['total_candidates']}
- **Rules Processed**: {meta['total_rules']}

## Statistics
| Metric | Count |
|--------|-------|
| Success | {stats['success']} |
| Manual Parse | {stats['manual_parse']} |
| Failed | {stats['failed']} |
| **Success Rate** | **{(stats['success'] / (stats['success'] + stats['failed']) * 100) if (stats['success'] + stats['failed']) > 0 else 0:.1f}%** |

## Distribution by Deontic Type
| Type | Count | Percentage |
|------|-------|------------|
| Obligation | {stats['by_type']['obligation']} | {stats['by_type']['obligation'] / meta['total_rules'] * 100:.1f}% |
| Permission | {stats['by_type']['permission']} | {stats['by_type']['permission'] / meta['total_rules'] * 100:.1f}% |
| Prohibition | {stats['by_type']['prohibition']} | {stats['by_type']['prohibition'] / meta['total_rules'] * 100:.1f}% |

## Sample Formalizations

"""
    
    # Add sample formalizations
    for i, rule in enumerate(results["formalized_rules"][:5], 1):
        fol = rule.get("fol_formalization", {})
        report += f"""### {i}. {rule['id']}
**Original**: {rule['original_text'][:100]}...

**Deontic Type**: {fol.get('deontic_type', 'N/A')}

**Formula**: `{fol.get('deontic_formula', fol.get('fol_formula', 'N/A'))}`

---

"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate FOL from v4 gold standard")
    parser.add_argument("--ollama-url", default="http://10.99.200.2:11434", help="Ollama server URL")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rules to process")
    args = parser.parse_args()
    
    process_rules_v4(args.ollama_url, args.limit)


if __name__ == "__main__":
    main()
