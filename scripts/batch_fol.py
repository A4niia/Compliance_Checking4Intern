"""
Batch FOL Generation
Generates First-Order Logic formulas for multiple rules in a single LLM call.

Key Features:
- Smaller batch size (5 rules) due to longer outputs
- Structured JSON array response
- Fallback to individual processing
"""

import json
import requests
import os
from typing import List, Dict, Any, Optional


def generate_fol_batch(
    rules: List[str],
    model: str = "mistral",
    temperature: float = 0.0,
    ollama_url: str = "http://10.99.200.2:11434"
) -> List[Dict[str, Any]]:
    """
    Generate FOL for multiple rules in a single LLM call.
    
    Args:
        rules: List of rule texts
        model: LLM model name
        temperature: Temperature parameter
        ollama_url: Ollama API URL
    
    Returns:
        List of FOL results with same order as input
    """
    if not rules:
        return []
    
    # Build batch prompt
    rules_text = "\n\n".join([
        f"Rule {i+1}: \"{rule}\""
        for i, rule in enumerate(rules)
    ])
    
    prompt = f"""You are a formal logic expert. Generate First-Order Logic (FOL) deontic formulas for academic policy rules.

Use these templates:
- Obligation: O(action(student)) - "student must do action"
- Permission: P(action(student)) - "student may do action"  
- Prohibition: F(action(student)) - "student must not do action"

For each rule below, generate:
1. deontic_type: "obligation", "permission", or "prohibition"
2. deontic_formula: FOL formula using the template
3. variables: List of variables used

{rules_text}

Return ONLY a valid JSON array with {len(rules)} objects:
[
  {{
    "rule_num": 1,
    "deontic_type": "obligation",
    "deontic_formula": "O(payFees(student))",
    "variables": ["student"]
  }},
  ...
]

JSON output:"""

    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False,
                "options": {
                    "num_predict": 1000 + (len(rules) * 100),  # Longer for FOL
                    "stop": ["\n\n"]
                }
            },
            timeout=180  # Longer timeout for FOL
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        output_text = result.get("response", "").strip()
        
        # Parse JSON array
        json_start = output_text.find("[")
        json_end = output_text.rfind("]") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = output_text[json_start:json_end]
            fol_results = json.loads(json_text)
            
            # Sort by rule_num
            fol_results.sort(key=lambda x: x.get("rule_num", 0))
            return fol_results
        else:
            raise ValueError("Could not find JSON array in response")
            
    except Exception as e:
        print(f"Batch FOL generation error: {e}")
        return []


def generate_fol_with_batching(
    rules: List[Dict[str, Any]],
    batch_size: int = 5,  # Smaller batches for FOL
    model: str = "mistral",
    temperature: float = 0.0,
    ollama_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate FOL for rules with batching and fallback.
    
    Args:
        rules: List of rule dicts with 'id', 'type', 'original_text'
        batch_size: Number of rules per batch
        model: LLM model name
        temperature: Temperature parameter
        ollama_url: Ollama API URL
    
    Returns:
        List of results with 'id', 'fol', 'deontic_type', etc.
    """
    if ollama_url is None:
        ollama_url = os.getenv("OLLAMA_HOST", "http://10.99.200.2:11434")
    
    results = []
    
    # Process in batches
    for i in range(0, len(rules), batch_size):
        batch = rules[i:i+batch_size]
        batch_texts = [rule.get("original_text", "") for rule in batch]
        
        # Try batch FOL generation
        batch_results = generate_fol_batch(batch_texts, model, temperature, ollama_url)
        
        if batch_results and len(batch_results) == len(batch):
            # Batch successful
            for rule, fol_result in zip(batch, batch_results):
                results.append({
                    "id": rule.get("id"),
                    "fol": fol_result.get("deontic_formula", ""),
                    "fol_expansion": fol_result.get("deontic_formula", ""),
                    "deontic_type": fol_result.get("deontic_type", rule.get("type", "obligation")),
                    "original_text": rule.get("original_text", "")
                })
        else:
            # Batch failed - fallback to individual
            print(f"FOL batch {i//batch_size + 1} failed, falling back to individual processing")
            from scripts.generate_fol_v2 import generate_fol
            
            for rule in batch:
                try:
                    individual_result = generate_fol(rule.get("original_text", ""), ollama_url)
                    if individual_result and not individual_result.get("error"):
                        results.append({
                            "id": rule.get("id"),
                            "fol": individual_result.get("deontic_formula", ""),
                            "fol_expansion": individual_result.get("fol_expansion", ""),
                            "deontic_type": individual_result.get("deontic_type", rule.get("type")),
                            "original_text": rule.get("original_text", "")
                        })
                    else:
                        results.append({
                            "id": rule.get("id"),
                            "fol": f"O({rule.get('type')}(x))",
                            "original_text": rule.get("original_text", "")
                        })
                except Exception:
                    results.append({
                        "id": rule.get("id"),
                        "fol": f"O({rule.get('type')}(x))",
                        "original_text": rule.get("original_text", "")
                    })
    
    return results


if __name__ == "__main__":
    # Test batch FOL generation
    test_rules = [
        "Students must pay fees before registration.",
        "Students may apply for scholarships.",
        "Students shall not plagiarize."
    ]
    
    results = generate_fol_batch(test_rules)
    print(f"Batch FOL results: {json.dumps(results, indent=2)}")
