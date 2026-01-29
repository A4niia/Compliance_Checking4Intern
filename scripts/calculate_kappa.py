#!/usr/bin/env python3
"""
Calculate Cohen's Kappa for Human vs LLM Agreement
"""

import json
from pathlib import Path

try:
    from sklearn.metrics import cohen_kappa_score, confusion_matrix, classification_report
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: sklearn not installed. Install with: pip install scikit-learn")

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"


def load_annotations(filepath: Path) -> dict:
    """Load annotated gold standard."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_kappa_manual(labels1, labels2):
    """Calculate Cohen's Kappa without sklearn."""
    n = len(labels1)
    if n == 0:
        return 0.0
    
    # Observed agreement
    agree = sum(1 for a, b in zip(labels1, labels2) if a == b)
    po = agree / n
    
    # Expected agreement
    p1_yes = sum(labels1) / n
    p2_yes = sum(labels2) / n
    pe = p1_yes * p2_yes + (1 - p1_yes) * (1 - p2_yes)
    
    # Kappa
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def main():
    print("=" * 60)
    print("COHEN'S KAPPA CALCULATION")
    print("Human vs LLM Agreement")
    print("=" * 60)
    
    # Load gold standard
    gs_file = RESEARCH_DIR / "gold_standard_template.json"
    if not gs_file.exists():
        print(f"Error: {gs_file} not found")
        return
    
    data = load_annotations(gs_file)
    rules = data.get('rules', data.get('extracted_rules', []))
    
    human_labels = []
    llm_labels = []
    missing_annotations = 0
    
    for rule in rules:
        # Get LLM classification
        llm_class = rule.get('llm_classification', {})
        llm_is_rule = llm_class.get('is_rule', False)
        
        # Get human annotation
        human_ann = rule.get('human_annotation', {})
        if not human_ann or 'is_rule' not in human_ann:
            missing_annotations += 1
            continue
        
        human_is_rule = human_ann.get('is_rule', False)
        
        # Convert to binary
        human_labels.append(1 if human_is_rule else 0)
        llm_labels.append(1 if llm_is_rule else 0)
    
    print(f"\nTotal rules: {len(rules)}")
    print(f"Annotated: {len(human_labels)}")
    print(f"Missing annotations: {missing_annotations}")
    
    if len(human_labels) < 2:
        print("\n⚠️ Not enough annotations. Please add human_annotation to rules.")
        print("\nExample annotation format:")
        print('''
{
  "human_annotation": {
    "is_rule": true,
    "rule_type": "obligation",
    "confidence": 5,
    "annotator": "Your Name",
    "reasoning": "Contains 'must' deontic marker"
  }
}
''')
        return
    
    # Calculate Kappa
    if HAS_SKLEARN:
        kappa = cohen_kappa_score(human_labels, llm_labels)
        print("\n" + "=" * 60)
        print(f"Cohen's Kappa: {kappa:.4f}")
        print("=" * 60)
        
        # Interpretation
        if kappa < 0.20:
            interp = "Poor agreement"
        elif kappa < 0.40:
            interp = "Fair agreement"
        elif kappa < 0.60:
            interp = "Moderate agreement"
        elif kappa < 0.80:
            interp = "Substantial agreement"
        else:
            interp = "Almost perfect agreement"
        
        print(f"Interpretation: {interp}")
        
        # Confusion matrix
        print("\nConfusion Matrix:")
        print("              LLM=No  LLM=Yes")
        cm = confusion_matrix(human_labels, llm_labels)
        print(f"Human=No      {cm[0][0]:5d}    {cm[0][1]:5d}")
        print(f"Human=Yes     {cm[1][0]:5d}    {cm[1][1]:5d}")
        
        # Classification report
        print("\nClassification Report:")
        print(classification_report(human_labels, llm_labels, 
                                    target_names=['Not Rule', 'Is Rule']))
    else:
        kappa = calculate_kappa_manual(human_labels, llm_labels)
        print("\n" + "=" * 60)
        print(f"Cohen's Kappa: {kappa:.4f}")
        print("=" * 60)
    
    # Save results
    results = {
        "total_rules": len(rules),
        "annotated": len(human_labels),
        "cohens_kappa": round(kappa, 4),
        "human_positive": sum(human_labels),
        "llm_positive": sum(llm_labels),
        "agreement": sum(1 for h, l in zip(human_labels, llm_labels) if h == l)
    }
    
    output_file = RESEARCH_DIR / "kappa_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\n📊 Results saved: {output_file}")


if __name__ == "__main__":
    main()
