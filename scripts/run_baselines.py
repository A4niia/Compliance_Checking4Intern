"""
Baseline Classifiers for Policy Rule Classification

Research-backed implementation following Dietterich (1998) methodology.

Baselines:
1. Random Classifier - Expected 33.3% (3-class uniform)
2. Majority Class - Uses dataset statistics  
3. Rule-Based Regex - Deontic marker matching (Breaux & Anton, 2008)

Usage:
    python scripts/run_baselines.py --gold research/gold_standard_annotated.json

Output:
    research/baseline_results.json

Author: Generated for Thesis Research Gap Implementation
Date: 2026-02-02
"""

import json
import re
import random
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter
import argparse


class RandomClassifier:
    """Baseline 1: Random assignment (Dietterich, 1998)"""
    
    def __init__(self, seed=42):
        self.classes = ["obligation", "permission", "prohibition"]
        random.seed(seed)
    
    def classify(self, text: str) -> str:
        return random.choice(self.classes)
    
    def name(self) -> str:
        return "Random"


class MajorityClassifier:
    """Baseline 2: Always predict most frequent class"""
    
    def __init__(self, majority_class: str):
        self.majority_class = majority_class
    
    def classify(self, text: str) -> str:
        return self.majority_class
    
    def name(self) -> str:
        return "Majority Class"


class RegexClassifier:
    """
    Baseline 3: Rule-based deontic marker matching
    
    Based on legal NLP literature:
    - Breaux & Anton (2008): Regulatory rule extraction
    - Maxwell et al. (2011): Privacy policy analysis
    
    Patterns ordered by specificity (most specific first).
    """
    
    def __init__(self):
        # Deontic marker patterns (ORDERED BY PRIORITY)
        self.patterns = [
            # 1. PROHIBITIONS (most specific - check first)
            (r'\b(cannot|can\s*not|must\s*not|shall\s*not|prohibited|forbidden|may\s*not|disallowed)\b', 
             'prohibition'),
            
            # 2. OBLIGATIONS (medium specificity)
            (r'\b(must|shall|required\s*to|obligated\s*to|have\s*to|need\s*to|expected\s*to)\b', 
             'obligation'),
            
            # 3. PERMISSIONS (least specific - check last)
            (r'\b(may|can|permitted\s*to|allowed\s*to|optional)\b', 
             'permission'),
        ]
    
    def classify(self, text: str) -> str:
        """
        Classify using regex patterns (case-insensitive).
        
        Pattern matching order matters:
        - "must not" should match prohibition (not obligation)
        - "may be required" is ambiguous (matches both)
        """
        text_lower = text.lower()
        
        # Apply patterns in order of specificity
        for pattern, rule_type in self.patterns:
            if re.search(pattern, text_lower):
                return rule_type
        
        # Default: If no markers found, predict majority class
        return "obligation"  # 67% of dataset
    
    def name(self) -> str:
        return "Rule-Based (Regex)"


def load_gold_standard(filepath: str) -> List[Dict]:
    """Load gold standard annotations"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Loaded {len(data)} rules from {filepath}")
        return data
    except FileNotFoundError:
        print(f"✗ Error: File not found: {filepath}")
        print(f"  Please ensure gold standard exists at this location.")
        raise
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON in {filepath}")
        print(f"  {str(e)}")
        raise


def evaluate_classifier(classifier, gold_standard: List[Dict]) -> Dict:
    """
    Evaluate classifier performance with confusion matrix
    
    Returns comprehensive metrics dictionary with:
    - accuracy, precision, recall, F1
    - per-class metrics
    - confusion matrix
    - error cases
    """
    predictions = []
    errors = []
    
    # Confusion matrix: {(true, pred): count}
    confusion = {}
    
    for i, rule in enumerate(gold_standard):
        text = rule['text']
        true_label = rule['rule_type']
        
        # Classify
        pred_label = classifier.classify(text)
        predictions.append(pred_label)
        
        # Update confusion matrix
        key = (true_label, pred_label)
        confusion[key] = confusion.get(key, 0) + 1
        
        # Track errors for analysis
        if pred_label != true_label:
            errors.append({
                'rule_id': rule.get('id', f'rule_{i+1}'),
                'text': text[:100] + '...' if len(text) > 100 else text,
                'true_label': true_label,
                'predicted_label': pred_label
            })
    
    # Calculate overall metrics
    correct = sum(1 for rule, pred in zip(gold_standard, predictions) 
                  if rule['rule_type'] == pred)
    accuracy = correct / len(gold_standard) if gold_standard else 0
    
    # Per-class metrics
    classes = ["obligation", "permission", "prohibition"]
    precision_scores = {}
    recall_scores = {}
    f1_scores = {}
    
    for cls in classes:
        # True Positives: correctly predicted this class
        tp = confusion.get((cls, cls), 0)
        
        # False Positives: predicted this class but was actually another
        fp = sum(confusion.get((other, cls), 0) 
                for other in classes if other != cls)
        
        # False Negatives: was this class but predicted another
        fn = sum(confusion.get((cls, other), 0) 
                for other in classes if other != cls)
        
        # Calculate P, R, F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        precision_scores[cls] = precision
        recall_scores[cls] = recall
        f1_scores[cls] = f1
    
    # Macro-averaged metrics (treat all classes equally)
    avg_precision = sum(precision_scores.values()) / len(precision_scores)
    avg_recall = sum(recall_scores.values()) / len(recall_scores)
    avg_f1 = sum(f1_scores.values()) / len(f1_scores)
    
    return {
        "accuracy": accuracy,
        "precision": avg_precision,
        "recall": avg_recall,
        "f1": avg_f1,
        "confusion_matrix": confusion,
        "per_class_precision": precision_scores,
        "per_class_recall": recall_scores,
        "per_class_f1": f1_scores,
        "errors": errors,
        "error_count": len(errors)
    }


def format_confusion_matrix(confusion: Dict, classes: List[str]) -> str:
    """Format confusion matrix as ASCII table for terminal display"""
    
    # Header
    header = "              " + "".join(f"{c:>14}" for c in classes)
    separator = "=" * len(header)
    
    lines = [separator, header, separator]
    
    # Rows
    for true_cls in classes:
        row = f"{true_cls:>13} |"
        for pred_cls in classes:
            count = confusion.get((true_cls, pred_cls), 0)
            row += f"{count:>13} "
        lines.append(row)
    
    lines.append(separator)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate baseline classifiers for policy rule classification'
    )
    parser.add_argument(
        '--gold', 
        default='research/gold_standard_annotated.json',
        help='Path to gold standard JSON file'
    )
    parser.add_argument(
        '--output', 
        default='research/baseline_results.json',
        help='Output path for results JSON'
    )
    parser.add_argument(
        '--seed', 
        type=int, 
        default=42,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    # Print header
    print(f"\n{'='*70}")
    print("BASELINE CLASSIFIER EVALUATION")
    print(f"{'='*70}\n")
    
    # Load gold standard
    gold_standard = load_gold_standard(args.gold)
    
    # Calculate class distribution
    true_labels = [rule['rule_type'] for rule in gold_standard]
    class_dist = Counter(true_labels)
    majority_class = class_dist.most_common(1)[0][0]
    
    print(f"\nDataset Statistics:")
    print(f"  Total rules: {len(gold_standard)}")
    print(f"\nClass Distribution:")
    for cls in ["obligation", "permission", "prohibition"]:
        count = class_dist[cls]
        pct = count / len(gold_standard) * 100
        print(f"  {cls:>12}: {count:>3} ({pct:>5.1f}%)")
    print(f"\n  Majority class: {majority_class} ({class_dist[majority_class]/len(gold_standard)*100:.1f}%)")
    print()
    
    # Initialize classifiers
    classifiers = [
        RandomClassifier(seed=args.seed),
        MajorityClassifier(majority_class),
        RegexClassifier()
    ]
    
    # Evaluate each classifier
    results = {
        "dataset_size": len(gold_standard),
        "class_distribution": dict(class_dist),
        "majority_class": majority_class,
        "seed": args.seed,
        "classifiers": {}
    }
    
    for classifier in classifiers:
        print(f"\n{'-'*70}")
        print(f"Evaluating: {classifier.name()}")
        print(f"{'-'*70}\n")
        
        metrics = evaluate_classifier(classifier, gold_standard)
        
        # Print summary metrics
        print(f"  Accuracy:  {metrics['accuracy']*100:>5.1f}%")
        print(f"  Precision: {metrics['precision']*100:>5.1f}%")
        print(f"  Recall:    {metrics['recall']*100:>5.1f}%")
        print(f"  F1 Score:  {metrics['f1']*100:>5.1f}%")
        print(f"\n  Errors: {metrics['error_count']}/{len(gold_standard)} ({metrics['error_count']/len(gold_standard)*100:.1f}%)")
        
        # Print per-class F1
        print(f"\n  Per-Class F1:")
        for cls in ["obligation", "permission", "prohibition"]:
            f1 = metrics['per_class_f1'][cls]
            print(f"    {cls:>12}: {f1*100:>5.1f}%")
        
        # Print confusion matrix
        print(f"\n  Confusion Matrix:")
        print(f"  (Rows = True, Columns = Predicted)\n")
        classes = ["obligation", "permission", "prohibition"]
        cm_str = format_confusion_matrix(metrics['confusion_matrix'], classes)
        for line in cm_str.split('\n'):
            print(f"  {line}")
        print()
        
        # Store results
        results["classifiers"][classifier.name()] = {
            "accuracy": float(metrics['accuracy']),
            "precision": float(metrics['precision']),
            "recall": float(metrics['recall']),
            "f1": float(metrics['f1']),
            "confusion_matrix": {
                f"{k[0]}->{k[1]}": v 
                for k, v in metrics['confusion_matrix'].items()
            },
            "per_class": {
                cls: {
                    "precision": float(metrics['per_class_precision'][cls]),
                    "recall": float(metrics['per_class_recall'][cls]),
                    "f1": float(metrics['per_class_f1'][cls])
                }
                for cls in ["obligation", "permission", "prohibition"]
            },
            "error_count": metrics['error_count'],
            "errors_sample": metrics['errors'][:5]  # Save first 5 errors
        }
    
    # Save results to JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Results saved to: {output_path}")
    print(f"{'='*70}\n")
    
    # Final comparison table
    print("\nBASELINE COMPARISON SUMMARY\n")
    print(f"{'Classifier':<25} {'Accuracy':>10} {'F1':>10} {'vs Random':>12}")
    print(f"{'-'*60}")
    
    random_acc = results["classifiers"]["Random"]["accuracy"]
    
    for name in ["Random", "Majority Class", "Rule-Based (Regex)"]:
        metrics = results["classifiers"][name]
        acc = metrics["accuracy"] * 100
        f1 = metrics["f1"] * 100
        improvement = (metrics["accuracy"] - random_acc) * 100
        
        print(f"{name:<25} {acc:>9.1f}% {f1:>9.1f}% {improvement:>+11.1f}pp")
    
    print(f"\n{'='*70}\n")
    
    # Interpretation
    regex_acc = results["classifiers"]["Rule-Based (Regex)"]["accuracy"]
    maj_acc = results["classifiers"]["Majority Class"]["accuracy"]
    
    print("INTERPRETATION:\n")
    print(f"1. Random performance ({random_acc*100:.1f}%) establishes absolute minimum")
    print(f"2. Majority class ({maj_acc*100:.1f}%) shows dataset imbalance baseline")
    print(f"3. Regex ({regex_acc*100:.1f}%) shows what keyword matching achieves")
    print(f"\nYour LLM models should significantly exceed {regex_acc*100:.1f}% to")
    print(f"demonstrate genuine semantic understanding beyond pattern matching.")
    print()


if __name__ == '__main__':
    main()
