"""
Batch LLM Classification
Processes multiple rules in a single LLM prompt for 4-10x speedup.

Key Features:
- Batch size configurable (default 10)
- Few-shot examples included in batch prompt
- JSON array output parsing
- Fallback to individual processing on batch errors
"""

import json
import requests
import os
from typing import List, Dict, Any, Optional


FEW_SHOT_EXAMPLES = [
    {
        "text": "Students must pay all fees before the mid-semester break.",
        "type": "obligation",
        "reasoning": "Keyword 'must' indicates obligation"
    },
    {
        "text": "Students may apply for fee deferrals if they have financial hardship.",
        "type": "permission",
        "reasoning": "Keyword 'may' indicates permission"
    },
    {
        "text": "Students shall not register without paying fees.",
        "type": "prohibition",
        "reasoning": "Negative obligation ('shall not') indicates prohibition"
    },
    {
        "text": "Full-time students are required to enroll in at least 12 credits.",
        "type": "obligation",
        "reasoning": "'Required to' indicates obligation"
    },
    {
        "text": "Students are allowed to take a leave of absence for up to one year.",
        "type": "permission",
        "reasoning": "'Allowed to' indicates permission"
    }
]


def classify_batch(
    rules: List[str],
    model: str = "mistral",
    temperature: float = 0.0,
    ollama_url: str = "http://10.99.200.2:11434"
) -> List[Dict[str, Any]]:
    """
    Classify multiple rules in a single LLM call.
    
    Args:
        rules: List of rule texts to classify
        model: LLM model name
        temperature: Temperature parameter
        ollama_url: Ollama API URL
    
    Returns:
        List of classification results with same order as input
    """
    if not rules:
        return []
    
    # Build few-shot examples
    examples_text = "\n\n".join([
        f"Example {i+1}:\nRule: \"{ex['text']}\"\nType: {ex['type']}\nReasoning: {ex['reasoning']}"
        for i, ex in enumerate(FEW_SHOT_EXAMPLES)
    ])
    
    # Build batch prompt
    rules_text = "\n\n".join([
        f"{i+1}. \"{rule}\""
        for i, rule in enumerate(rules)
    ])
    
    prompt = f"""You are a policy classification expert. Classify each academic policy rule into one of three categories:
- **obligation**: Rules that REQUIRE or MANDATE certain actions (keywords: must, shall, required, mandatory)
- **permission**: Rules that ALLOW or PERMIT certain actions (keywords: may, can, allowed, permitted)
- **prohibition**: Rules that FORBID or PROHIBIT certain actions (keywords: must not, shall not, prohibited, forbidden)

Here are some examples:

{examples_text}

Now classify the following {len(rules)} rules:

{rules_text}

Return ONLY a valid JSON array with {len(rules)} objects in the format:
[
  {{"rule_num": 1, "rule_type": "obligation"}},
  {{"rule_num": 2, "rule_type": "permission"}},
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
                    "num_predict": 500 + (len(rules) * 30)  # Dynamic based on batch size
                }
            },
            timeout=120  # Longer timeout for batches
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        output_text = result.get("response", "").strip()
        
        # Parse JSON array
        # Try to extract JSON array from output
        json_start = output_text.find("[")
        json_end = output_text.rfind("]") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = output_text[json_start:json_end]
            classifications = json.loads(json_text)
            
            # Validate and normalize
            results = []
            for item in classifications:
                rule_num = item.get("rule_num", 0)
                rule_type = item.get("rule_type", "obligation").lower()
                
                # Validate rule_type
                if rule_type not in ["obligation", "permission", "prohibition"]:
                    rule_type = "obligation"
                
                results.append({
                    "rule_num": rule_num,
                    "rule_type": rule_type
                })
            
            # Sort by rule_num to ensure order
            results.sort(key=lambda x: x.get("rule_num", 0))
            return results
        else:
            raise ValueError("Could not find JSON array in response")
            
    except Exception as e:
        print(f"Batch classification error: {e}")
        # Return empty results - caller should fallback
        return []


def classify_rules_with_batching(
    rules: List[Dict[str, Any]],
    batch_size: int = 10,
    model: str = "mistral",
    temperature: float = 0.0,
    ollama_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Classify rules with batching and fallback to individual processing.
    
    Args:
        rules: List of rule dicts with 'id' and 'original_text'
        batch_size: Number of rules per batch
        model: LLM model name
        temperature: Temperature parameter
        ollama_url: Ollama API URL
    
    Returns:
        List of results with 'id', 'type', 'original_text'
    """
    if ollama_url is None:
        ollama_url = os.getenv("OLLAMA_HOST", "http://10.99.200.2:11434")
    
    results = []
    
    # Process in batches
    for i in range(0, len(rules), batch_size):
        batch = rules[i:i+batch_size]
        batch_texts = [rule.get("original_text", "") for rule in batch]
        
        # Try batch classification
        batch_results = classify_batch(batch_texts, model, temperature, ollama_url)
        
        if batch_results and len(batch_results) == len(batch):
            # Batch successful - merge with rule IDs
            for rule, classification in zip(batch, batch_results):
                results.append({
                    "id": rule.get("id"),
                    "type": classification.get("rule_type", "obligation"),
                    "original_text": rule.get("original_text", "")
                })
        else:
            # Batch failed - fallback to individual
            print(f"Batch {i//batch_size + 1} failed, falling back to individual processing")
            from scripts.populate_llm_annotations_v2 import classify_rule_strict
            
            for rule in batch:
                try:
                    individual_result = classify_rule_strict(rule.get("original_text", ""))
                    results.append({
                        "id": rule.get("id"),
                        "type": individual_result.get("rule_type", "obligation"),
                        "original_text": rule.get("original_text", "")
                    })
                except Exception:
                    results.append({
                        "id": rule.get("id"),
                        "type": "obligation",
                        "original_text": rule.get("original_text", "")
                    })
    
    return results


if __name__ == "__main__":
    # Test batch classification
    test_rules = [
        "Students must pay fees before registration.",
        "Students may apply for scholarships.",
        "Students shall not plagiarize.",
        "Full-time students are required to enroll in 12 credits.",
        "Students can request grade appeals."
    ]
    
    results = classify_batch(test_rules)
    print(f"Batch results: {json.dumps(results, indent=2)}")
