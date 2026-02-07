#!/usr/bin/env python3
"""
FOL (First-Order Logic) Generation Script v2
Uses Mistral to generate formal logic representations of policy rules.

IMPROVEMENTS (v2):
- Increased response length (num_predict)
- Better JSON parsing with LaTeX escape handling
- Temporal logic extension predicates
- Retry mechanism for failed parses

Usage:
    python scripts/generate_fol_v2.py --ollama-url http://10.99.200.2:11434 --limit 10
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
{{"deontic_type": "obligation|permission|prohibition", "deontic_formula": "short formula", "fol_expansion": "expanded formula", "shacl_hint": "brief hint", "explanation": "1 sentence"}}
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
                        "temperature": 0.0,  # Changed from 0.1 for reproducibility
                        "seed": 42,          # Fixed seed for deterministic output
                        "num_predict": 1024,  # Increased from default ~128
                        "stop": ["\n\n"]  # Stop at double newline to prevent runaway
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
            candidate = re.sub(r',\s*}', '}', candidate)  # Remove trailing commas
            candidate = re.sub(r'"\s*:\s*"([^"]*)"([^,}])', r'": "\1"\2', candidate)
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


def generate_fol(rule_text: str, ollama_url: str) -> dict:
    """Generate FOL for a single rule with improved handling."""
    # Truncate very long rules
    if len(rule_text) > 300:
        rule_text = rule_text[:300] + "..."
    
    prompt = IMPROVED_PROMPT.format(text=rule_text)
    response = query_ollama(prompt, ollama_url)
    result = parse_json_response(response)
    
    if result is None:
        # Retry with simpler prompt
        simple_prompt = f"""Convert to deontic logic JSON: "{rule_text[:150]}"
Return: {{"deontic_type": "...", "deontic_formula": "...", "explanation": "..."}}"""
        
        response = query_ollama(simple_prompt, ollama_url)
        result = parse_json_response(response)
    
    if result is None:
        result = {
            "error": "Failed to parse response",
            "raw_response": response[:300] if response else None,
            "recoverable": True
        }
    
    return result


def process_rules(ollama_url: str, limit: int = None, reprocess_errors: bool = True):
    """Process rules from comparison results and generate FOL."""
    print(f"\n{'='*60}")
    print("FOL GENERATION v2 - IMPROVED PARSING")
    print(f"{'='*60}")
    print(f"Model: {MODEL}")
    print(f"Ollama URL: {ollama_url}")
    print(f"Improvements: Longer response, better JSON parsing, temporal ops")
    print(f"{'='*60}\n")
    
    # Load comparison results
    results_file = RESEARCH_DIR / "model_comparison_results.json"
    if not results_file.exists():
        print(f"Error: {results_file} not found. Run compare_models.py first.")
        return
    
    with open(results_file, 'r', encoding='utf-8') as f:
        comparison = json.load(f)
    
    # Get Mistral's results
    mistral_results = comparison["model_results"]["mistral"]
    
    # Load gold standard for original text
    gold_file = RESEARCH_DIR / "gold_standard_template.json"
    with open(gold_file, 'r', encoding='utf-8') as f:
        gold = json.load(f)
    gold_dict = {g["id"]: g["original_text"] for g in gold}
    
    if limit:
        mistral_results = mistral_results[:limit]
    
    print(f"Processing {len(mistral_results)} rules...\n")
    
    fol_results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": MODEL,
            "version": "v2_improved",
            "ollama_url": ollama_url,
            "total_rules": len(mistral_results),
            "improvements": [
                "increased_response_length",
                "latex_escape_handling",
                "multi_strategy_parsing",
                "retry_mechanism"
            ]
        },
        "formalized_rules": [],
        "statistics": {
            "success": 0,
            "failed": 0,
            "manual_parse": 0
        }
    }
    
    for i, item in enumerate(mistral_results, 1):
        rule_id = item["id"]
        result = item["result"]
        
        # Skip if not classified as rule
        if not result.get("is_rule"):
            print(f"[{i}/{len(mistral_results)}] {rule_id} - Skipped (not a rule)")
            continue
        
        original_text = gold_dict.get(rule_id)
        if not original_text:
            continue
        
        print(f"[{i}/{len(mistral_results)}] {rule_id}")
        print(f"  Text: {original_text[:50]}...")
        
        # Generate FOL
        fol = generate_fol(original_text, ollama_url)
        
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
        
        print(f"  Status: {status}")
        print(f"  Type: {fol.get('deontic_type', 'N/A')}")
        formula = fol.get('deontic_formula', fol.get('fol_formula', 'Error'))
        if formula:
            print(f"  FOL: {str(formula)[:50]}...")
        print()
        
        fol_results["formalized_rules"].append({
            "id": rule_id,
            "original_text": original_text,
            "llm_classification": result,
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
    print(f"{'='*60}\n")
    
    # Save results
    output_file = RESEARCH_DIR / "fol_formalization_v2_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fol_results, f, indent=2, ensure_ascii=False)
    print(f"💾 Results saved: {output_file}")
    
    # Generate report
    report = generate_fol_report(fol_results)
    report_file = RESEARCH_DIR / "fol_formalization_v2_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📝 Report saved: {report_file}")
    
    return fol_results


def generate_fol_report(results: dict) -> str:
    """Generate markdown report."""
    stats = results["statistics"]
    total = stats["success"] + stats["failed"]
    success_rate = (stats["success"] / total * 100) if total > 0 else 0
    
    # Count deontic types
    type_counts = {"obligation": 0, "permission": 0, "prohibition": 0, "other": 0}
    for rule in results["formalized_rules"]:
        fol = rule.get("fol_formalization", {})
        if "error" not in fol:
            dtype = fol.get("deontic_type", "other")
            if dtype in type_counts:
                type_counts[dtype] += 1
            else:
                type_counts["other"] += 1
    
    report = f"""# FOL Formalization Results (v2 Improved)

**Generated:** {results['metadata']['timestamp']}
**Model:** {results['metadata']['model']}
**Version:** {results['metadata']['version']}

## Performance Metrics

| Metric | Value |
|--------|-------|
| Total Processed | {total} |
| Successful | {stats['success']} |
| Manual Parse Recovery | {stats['manual_parse']} |
| Failed | {stats['failed']} |
| **Success Rate** | **{success_rate:.1f}%** |

## Improvements Applied

- ✅ Increased response length (num_predict: 1024)
- ✅ LaTeX escape character handling
- ✅ Multi-strategy JSON parsing (5 strategies)
- ✅ Retry mechanism for failed requests
- ✅ Manual field extraction fallback

## Deontic Type Distribution

| Type | Count |
|------|-------|
| Obligation | {type_counts['obligation']} |
| Permission | {type_counts['permission']} |
| Prohibition | {type_counts['prohibition']} |
| Other | {type_counts['other']} |

## Sample Formalizations

"""
    
    # Add successful samples
    samples_added = 0
    for rule in results["formalized_rules"]:
        if samples_added >= 5:
            break
        fol = rule.get("fol_formalization", {})
        if "error" not in fol:
            report += f"""### {rule['id']}

**Text:** {rule['original_text'][:100]}...

**Type:** {fol.get('deontic_type', 'N/A')}

**Formula:**
```
{fol.get('deontic_formula', 'N/A')}
```

---

"""
            samples_added += 1
    
    # Add failure analysis
    failures = [r for r in results["formalized_rules"] if "error" in r.get("fol_formalization", {})]
    if failures:
        report += f"""## Failure Analysis

{len(failures)} rules failed to parse. Sample failures:

"""
        for failure in failures[:3]:
            report += f"""### {failure['id']}
**Text:** {failure['original_text'][:80]}...
**Raw:** {failure['fol_formalization'].get('raw_response', 'N/A')[:100]}...

---

"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate FOL for policy rules (v2 improved)")
    parser.add_argument("--ollama-url", default="http://localhost:11434",
                       help="Ollama API URL")
    parser.add_argument("--limit", type=int, help="Limit number of rules")
    
    args = parser.parse_args()
    
    process_rules(args.ollama_url, args.limit)


if __name__ == "__main__":
    main()
