#!/usr/bin/env python3
"""
Multi-Model Rule Verification Comparison
Run verification on gold standard with multiple LLMs and compare results.

Usage:
    python scripts/compare_models.py --ollama-url http://hpc-host:11434

Output:
    - research/model_comparison_results.json
    - research/model_comparison_report.md (for thesis)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"

# Models available on HPC Ollama server (10.99.200.2:11434)
MODELS = [
    "mistral",            # 7B - Best for classification (primary)
    "llama3.2",           # 3B - Fast baseline
    "phi3",               # 3.8B - Microsoft compact
    "mixtral",            # 47B MoE - High quality
    "glm-4.7-flash",      # 30B - GLM reasoning
    "qwen3:32b",          # 32B - Alibaba latest
    "qwen2.5:32b-instruct", # 32B - Alibaba instruction-tuned
    "llama3.1:70b",       # 70B - Best accuracy (slow)
]

# Model metadata for thesis report
MODEL_INFO = {
    "llama3.2": {
        "size": "3B",
        "organization": "Meta AI",
        "year": 2024,
        "citation": "Meta AI. (2024). Llama 3.2 Technical Report.",
        "type": "Small"
    },
    "phi3": {
        "size": "3.8B", 
        "organization": "Microsoft Research",
        "year": 2024,
        "citation": "Microsoft Research. (2024). Phi-3 Technical Report: A Highly Capable Language Model Locally on Your Phone.",
        "type": "Small"
    },
    "mistral": {
        "size": "7B",
        "organization": "Mistral AI",
        "year": 2023,
        "citation": "Jiang, A.Q., et al. (2023). Mistral 7B. arXiv preprint arXiv:2310.06825.",
        "type": "Medium"
    },
    "mixtral": {
        "size": "47B (13B active)",
        "organization": "Mistral AI",
        "year": 2024,
        "citation": "Jiang, A.Q., et al. (2024). Mixtral of Experts. arXiv preprint arXiv:2401.04088.",
        "evidence": "Outperforms Llama 2 70B on most benchmarks with 5x fewer active parameters",
        "type": "Large (MoE)"
    },
    "llama3.1:70b": {
        "size": "70B",
        "organization": "Meta AI",
        "year": 2024,
        "citation": "Meta AI. (2024). Llama 3.1 Model Card and Prompt Formats.",
        "evidence": "Fine-tuned Llama 3 outperforms RoBERTa-large on text classification (arXiv 2024)",
        "type": "Large"
    },
    "glm-4.7-flash": {
        "size": "30B",
        "organization": "Zhipu AI / Tsinghua",
        "year": 2024,
        "citation": "GLM Team. (2024). GLM-4 Technical Report.",
        "type": "Large"
    },
    "qwen3:32b": {
        "size": "32B",
        "organization": "Alibaba Cloud",
        "year": 2024,
        "citation": "Qwen Team. (2024). Qwen Technical Report.",
        "type": "Large"
    },
    "qwen2.5:32b-instruct": {
        "size": "32B",
        "organization": "Alibaba Cloud",
        "year": 2024,
        "citation": "Qwen Team. (2024). Qwen2.5 Technical Report.",
        "evidence": "Instruction-tuned for following complex instructions",
        "type": "Large (Instruct)"
    }
}

# Prompts
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
  "reasoning": "brief explanation"
}}
"""


def query_ollama(prompt: str, model: str, ollama_url: str, timeout: int = 300) -> Optional[str]:
    """Query Ollama API with proper streaming handling for slow HPC environments."""
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 1024,
                }
            },
            timeout=timeout
        )
        if response.status_code == 200:
            return response.json().get("response", "")
    except requests.exceptions.Timeout:
        print(f"Timeout after {timeout}s - model may need preloading")
    except Exception as e:
        print(f"Error: {e}")
    return None


def parse_json_response(response: str) -> Optional[dict]:
    """Parse JSON from LLM response."""
    if not response:
        return None
    
    import re
    # Try to extract JSON from markdown code block
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if json_match:
        response = json_match.group(1)
    
    # Try to find JSON object
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    return None


def verify_rule_with_model(text: str, model: str, ollama_url: str) -> dict:
    """Verify a single rule with a specific model."""
    prompt = RULE_VERIFICATION_PROMPT.format(text=text)
    response = query_ollama(prompt, model, ollama_url)
    result = parse_json_response(response)
    
    if result is None:
        result = {"is_rule": None, "error": "Failed to parse response"}
    
    return result


def run_model_comparison(gold_standard_file: str, ollama_url: str, limit: int = None):
    """Run comparison across all models."""
    print(f"\n{'='*60}")
    print("MULTI-MODEL RULE VERIFICATION COMPARISON")
    print(f"{'='*60}")
    print(f"Ollama URL: {ollama_url}")
    print(f"Models: {', '.join(MODELS)}")
    print(f"{'='*60}\n")
    
    # Load gold standard
    with open(gold_standard_file, 'r', encoding='utf-8') as f:
        gold_standard = json.load(f)
    
    if limit:
        gold_standard = gold_standard[:limit]
    
    print(f"Processing {len(gold_standard)} rules...\n")
    
    # Results storage
    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "ollama_url": ollama_url,
            "models": MODELS,
            "total_rules": len(gold_standard)
        },
        "model_results": {model: [] for model in MODELS},
        "comparison": []
    }
    
    # Process each rule with each model
    for i, item in enumerate(gold_standard, 1):
        rule_id = item["id"]
        text = item["original_text"]
        
        print(f"[{i}/{len(gold_standard)}] {rule_id}")
        
        comparison_entry = {
            "id": rule_id,
            "text": text[:80] + "..." if len(text) > 80 else text,
            "models": {}
        }
        
        for model in MODELS:
            print(f"  → Testing {model}...", end=" ", flush=True)
            
            result = verify_rule_with_model(text, model, ollama_url)
            
            is_rule = result.get("is_rule")
            confidence = result.get("confidence", 0)
            
            print(f"{'✅ RULE' if is_rule else '❌ NOT'} (conf: {confidence:.2f})")
            
            results["model_results"][model].append({
                "id": rule_id,
                "result": result
            })
            
            comparison_entry["models"][model] = {
                "is_rule": is_rule,
                "confidence": confidence,
                "rule_type": result.get("rule_type")
            }
        
        results["comparison"].append(comparison_entry)
        print()
    
    # Calculate agreement metrics
    print(f"\n{'='*60}")
    print("CALCULATING METRICS")
    print(f"{'='*60}\n")
    
    results["metrics"] = calculate_comparison_metrics(results)
    
    # Save results
    output_file = RESEARCH_DIR / "model_comparison_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Results saved: {output_file}")
    
    # Generate report
    report_file = generate_thesis_report(results)
    print(f"📝 Report saved: {report_file}")
    
    return results


def calculate_comparison_metrics(results: dict) -> dict:
    """Calculate inter-model agreement and individual metrics."""
    metrics = {}
    
    # Count agreements between models
    total = len(results["comparison"])
    
    for model in MODELS:
        model_results = results["model_results"][model]
        
        # Count classifications
        rule_count = sum(1 for r in model_results if r["result"].get("is_rule") == True)
        not_rule_count = sum(1 for r in model_results if r["result"].get("is_rule") == False)
        error_count = sum(1 for r in model_results if r["result"].get("is_rule") is None)
        
        avg_confidence = sum(
            r["result"].get("confidence", 0) for r in model_results
        ) / len(model_results) if model_results else 0
        
        metrics[model] = {
            "total": total,
            "classified_as_rule": rule_count,
            "classified_as_not_rule": not_rule_count,
            "errors": error_count,
            "rule_rate": rule_count / total if total > 0 else 0,
            "avg_confidence": avg_confidence
        }
        
        print(f"{model}:")
        print(f"  Rules: {rule_count} | Not Rules: {not_rule_count} | Errors: {error_count}")
        print(f"  Rule Rate: {rule_count/total*100:.1f}% | Avg Confidence: {avg_confidence:.2f}")
        print()
    
    # Calculate pairwise agreement
    metrics["pairwise_agreement"] = {}
    for i, model1 in enumerate(MODELS):
        for model2 in MODELS[i+1:]:
            agreements = 0
            for item in results["comparison"]:
                m1_result = item["models"].get(model1, {}).get("is_rule")
                m2_result = item["models"].get(model2, {}).get("is_rule")
                if m1_result is not None and m2_result is not None:
                    if m1_result == m2_result:
                        agreements += 1
            
            agreement_rate = agreements / total if total > 0 else 0
            metrics["pairwise_agreement"][f"{model1}_vs_{model2}"] = {
                "agreements": agreements,
                "total": total,
                "rate": agreement_rate
            }
            print(f"{model1} vs {model2}: {agreement_rate*100:.1f}% agreement")
    
    return metrics


def generate_thesis_report(results: dict) -> Path:
    """Generate markdown report for thesis."""
    metrics = results["metrics"]
    
    report = f"""# LLM Model Comparison for Policy Rule Verification

**Generated:** {results['metadata']['timestamp']}

## Overview

This report compares three Large Language Models (LLMs) for their ability to identify policy rules in academic documents. This comparison supports the methodology of the thesis by providing empirical justification for model selection.

## Models Tested

| Model | Type | Size | Purpose |
|-------|------|------|---------|
| Llama 3.2 | Open Source (Meta) | 3B | Baseline, efficient classification |
| Mistral | Open Source | 7B | Instruction-following, extraction |
| Phi3 | Open Source (Microsoft) | 3.8B | Compact reasoning |

## Results Summary

### Classification Statistics

| Model | Rules Found | Not Rules | Errors | Rule Rate | Avg Confidence |
|-------|-------------|-----------|--------|-----------|----------------|
"""
    
    for model in MODELS:
        m = metrics.get(model, {})
        report += f"| {model} | {m.get('classified_as_rule', 0)} | {m.get('classified_as_not_rule', 0)} | {m.get('errors', 0)} | {m.get('rule_rate', 0)*100:.1f}% | {m.get('avg_confidence', 0):.2f} |\n"
    
    report += """
### Inter-Model Agreement

| Model Pair | Agreement Rate |
|------------|----------------|
"""
    
    for pair, data in metrics.get("pairwise_agreement", {}).items():
        report += f"| {pair.replace('_', ' ')} | {data.get('rate', 0)*100:.1f}% |\n"
    
    report += f"""
## Sample Comparisons

The following table shows how models classified the same rule text:

| Rule ID | Llama 3.2 | Mistral | Phi3 |
|---------|-----------|---------|------|
"""
    
    # Add first 10 comparisons
    for item in results["comparison"][:10]:
        llama = "✅" if item["models"].get("llama3.2", {}).get("is_rule") else "❌"
        mistral = "✅" if item["models"].get("mistral", {}).get("is_rule") else "❌"
        phi3 = "✅" if item["models"].get("phi3", {}).get("is_rule") else "❌"
        report += f"| {item['id']} | {llama} | {mistral} | {phi3} |\n"
    
    report += """
## Methodology Notes

1. **Prompt Design**: All models used identical prompts for fair comparison
2. **Temperature**: Set to 0.1 for consistent, deterministic outputs
3. **Evaluation**: Binary classification (is_rule: true/false)

## Recommendations for Thesis

Based on the comparison results:

1. **Primary Model**: [To be determined based on results]
2. **Validation**: Cross-validate with model showing highest agreement
3. **Documentation**: Report inter-model agreement as measure of reliability

## References

- Meta AI. (2024). Llama 3.2 Technical Report.
- Mistral AI. (2023). Mistral 7B.
- Microsoft Research. (2024). Phi-3 Technical Report.
"""
    
    report_file = RESEARCH_DIR / "model_comparison_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return report_file


def main():
    parser = argparse.ArgumentParser(description="Multi-model comparison for rule verification")
    parser.add_argument("--ollama-url", default="http://10.99.200.2:11434",
                       help="Ollama API URL (default: HPC server)")
    parser.add_argument("--gold-standard", default=str(RESEARCH_DIR / "gold_standard_template.json"),
                       help="Path to gold standard JSON file")
    parser.add_argument("--limit", type=int, help="Limit number of rules to process")
    
    args = parser.parse_args()
    
    # Check connection
    print(f"Testing connection to {args.ollama_url}...")
    try:
        response = requests.get(f"{args.ollama_url}/api/tags", timeout=10)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            print(f"✅ Connected! Available models: {models}")
        else:
            print(f"❌ Connection failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("Make sure Ollama is running on the HPC server.")
        return
    
    # Run comparison
    run_model_comparison(args.gold_standard, args.ollama_url, args.limit)


if __name__ == "__main__":
    main()
