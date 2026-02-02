#!/usr/bin/env python3
"""
FOL (First-Order Logic) Generation Script
Uses Mistral to generate formal logic representations of policy rules.

Usage:
    python scripts/generate_fol.py --ollama-url http://10.99.200.2:11434 --limit 10
"""

import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

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

# FOL Generation Prompt
FOL_PROMPT = """You are an expert in formal logic and policy formalization.

Convert this policy rule into First-Order Logic (FOL) notation.

Policy Rule: "{text}"

Use these conventions:
- ∀ (forall), ∃ (exists), → (implies), ∧ (and), ∨ (or), ¬ (not)
- Use CamelCase for predicates: Student(x), IsPaid(x), HasObligation(x,y)
- Use lowercase for variables: x, y, s, o

Return JSON only:
{{
  "fol_formula": "the FOL formula",
  "predicates": ["list of predicates used"],
  "variables": {{"x": "description", "y": "description"}},
  "explanation": "brief explanation of the formalization"
}}
"""

# Deontic Logic Operators
DEONTIC_PROMPT = """You are an expert in deontic logic and policy formalization.

Formalize this policy rule using deontic logic operators.

Policy Rule: "{text}"

Use these deontic operators:
- O(φ) = Obligation: φ must happen
- P(φ) = Permission: φ may happen  
- F(φ) = Prohibition: φ is forbidden (equivalent to O(¬φ))

Combined with FOL:
- ∀ (forall), ∃ (exists), → (implies), ∧ (and), ∨ (or), ¬ (not)

Return JSON only:
{{
  "deontic_type": "obligation" | "permission" | "prohibition",
  "deontic_formula": "the formula using O, P, or F operators",
  "fol_expansion": "the expanded FOL formula without deontic operators",
  "shacl_hint": "how this could be expressed in SHACL",
  "explanation": "brief explanation"
}}
"""


def query_ollama(prompt: str, ollama_url: str, model: str = MODEL) -> Optional[str]:
    """Query Ollama API."""
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            },
            timeout=180
        )
        if response.status_code == 200:
            return response.json().get("response", "")
    except Exception as e:
        print(f"Error: {e}")
    return None


def parse_json_response(response: str) -> Optional[dict]:
    """Parse JSON from LLM response."""
    if not response:
        return None
    
    import re
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if json_match:
        response = json_match.group(1)
    
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    return None


def generate_fol(rule_text: str, ollama_url: str, use_deontic: bool = True) -> dict:
    """Generate FOL for a single rule."""
    if use_deontic:
        prompt = DEONTIC_PROMPT.format(text=rule_text)
    else:
        prompt = FOL_PROMPT.format(text=rule_text)
    
    response = query_ollama(prompt, ollama_url)
    result = parse_json_response(response)
    
    if result is None:
        result = {"error": "Failed to parse response", "raw_response": response[:500] if response else None}
    
    return result


def process_rules(ollama_url: str, limit: int = None, use_deontic: bool = True):
    """Process rules from comparison results and generate FOL."""
    print(f"\n{'='*60}")
    print("FOL GENERATION FOR POLICY RULES")
    print(f"{'='*60}")
    print(f"Model: {MODEL} (best from comparison)")
    print(f"Ollama URL: {ollama_url}")
    print(f"Using Deontic Logic: {use_deontic}")
    print(f"{'='*60}\n")
    
    # Load comparison results to get verified rules
    results_file = RESEARCH_DIR / "model_comparison_results.json"
    if not results_file.exists():
        print(f"Error: {results_file} not found. Run compare_models.py first.")
        return
    
    with open(results_file, 'r', encoding='utf-8') as f:
        comparison = json.load(f)
    
    # Get Mistral's results (best model)
    mistral_results = comparison["model_results"]["mistral"]
    
    if limit:
        mistral_results = mistral_results[:limit]
    
    print(f"Processing {len(mistral_results)} rules...\n")
    
    fol_results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": MODEL,
            "ollama_url": ollama_url,
            "total_rules": len(mistral_results),
            "deontic_mode": use_deontic
        },
        "formalized_rules": []
    }
    
    for i, item in enumerate(mistral_results, 1):
        rule_id = item["id"]
        result = item["result"]
        
        # Skip if not classified as rule
        if not result.get("is_rule"):
            print(f"[{i}/{len(mistral_results)}] {rule_id} - Skipped (not a rule)")
            continue
        
        # Get original text from gold standard
        gold_file = RESEARCH_DIR / "gold_standard_template.json"
        with open(gold_file, 'r', encoding='utf-8') as f:
            gold = json.load(f)
        
        original_text = None
        for g in gold:
            if g["id"] == rule_id:
                original_text = g["original_text"]
                break
        
        if not original_text:
            continue
        
        print(f"[{i}/{len(mistral_results)}] {rule_id}")
        print(f"  Text: {original_text[:60]}...")
        
        # Generate FOL
        fol = generate_fol(original_text, ollama_url, use_deontic)
        
        print(f"  Type: {fol.get('deontic_type', 'N/A')}")
        print(f"  FOL: {fol.get('deontic_formula', fol.get('fol_formula', 'Error'))[:60]}...")
        print()
        
        fol_results["formalized_rules"].append({
            "id": rule_id,
            "original_text": original_text,
            "llm_classification": result,
            "fol_formalization": fol
        })
        
        time.sleep(0.5)  # Rate limiting
    
    # Save results
    output_file = RESEARCH_DIR / "fol_formalization_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fol_results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 FOL results saved: {output_file}")
    
    # Generate summary report
    report = generate_fol_report(fol_results)
    report_file = RESEARCH_DIR / "fol_formalization_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📝 Report saved: {report_file}")
    
    return fol_results


def generate_fol_report(results: dict) -> str:
    """Generate markdown report for FOL formalization."""
    report = f"""# FOL Formalization Results

**Generated:** {results['metadata']['timestamp']}
**Model:** {results['metadata']['model']}
**Total Rules Formalized:** {len(results['formalized_rules'])}

## Deontic Type Distribution

| Type | Count |
|------|-------|
"""
    
    # Count deontic types
    type_counts = {"obligation": 0, "permission": 0, "prohibition": 0, "other": 0}
    for rule in results["formalized_rules"]:
        fol = rule.get("fol_formalization", {})
        dtype = fol.get("deontic_type", "other")
        if dtype in type_counts:
            type_counts[dtype] += 1
        else:
            type_counts["other"] += 1
    
    for dtype, count in type_counts.items():
        report += f"| {dtype.title()} | {count} |\n"
    
    report += """
## Sample Formalizations

"""
    
    # Add first 10 samples
    for rule in results["formalized_rules"][:10]:
        fol = rule.get("fol_formalization", {})
        report += f"""### {rule['id']}

**Text:** {rule['original_text'][:100]}...

**Deontic Type:** {fol.get('deontic_type', 'N/A')}

**Formula:**
```
{fol.get('deontic_formula', fol.get('fol_formula', 'Error'))}
```

**SHACL Hint:** {fol.get('shacl_hint', 'N/A')}

---

"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate FOL for policy rules")
    parser.add_argument("--ollama-url", default="http://localhost:11434",
                       help="Ollama API URL")
    parser.add_argument("--limit", type=int, help="Limit number of rules")
    parser.add_argument("--no-deontic", action="store_true",
                       help="Use plain FOL without deontic operators")
    
    args = parser.parse_args()
    
    process_rules(args.ollama_url, args.limit, not args.no_deontic)


if __name__ == "__main__":
    main()
