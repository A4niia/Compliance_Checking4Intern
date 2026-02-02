"""
Error Analysis for LLM Policy Rule Classification

Deep dive into misclassified rules to identify patterns and root causes.

This addresses Research Gap #4: Lack of detailed error analysis beyond accuracy metrics.

Analysis Dimensions:
1. Error categorization by linguistic pattern
2. Confusion matrix visualization
3. Confidence scores for errors vs. correct predictions
4. Systematic patterns (modal stacking, negation, implicit deontics)

Usage:
    python scripts/analyze_errors.py --model mistral

Output:
    research/error_analysis_results.json
"""

import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
import re


def load_gold_standard(filepath: str):
    """Load gold standard annotations"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract only rules (is_rule=true)
    rules = []
    for item in data:
        human_ann = item.get('human_annotation', {})
        if human_ann.get('is_rule', True):
            rules.append({
                'id': item.get('id', ''),
                'text': item.get('text', item.get('original_text', '')),
                'rule_type': human_ann.get('rule_type'),
                'source': item.get('source_document', '')
            })
    
    return rules


def load_model_predictions(filepath: str):
    """Load LLM model predictions"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def categorize_error(text: str, true_label: str, pred_label: str) -> str:
    """
    Categorize error by linguistic pattern
    
    Categories:
    - modal_stacking: "may be required", "must be allowed"
    - implicit_deontic: "expected to", "should", "supposed to"
    - negation_scope: "not required" vs "must not"
    - conditional: complex if-then structures
    - temporal: temporal precedence ("before", "after")
    - other: uncategorized
    """
    text_lower = text.lower()
    
    # Modal stacking: multiple modals in sequence
    if re.search(r'\b(may|can)\s+(be\s+)?(required|obligated|must|need)', text_lower):
        return 'modal_stacking'
    if re.search(r'\b(must|shall|required)\s+(be\s+)?(allowed|permitted|may)', text_lower):
        return 'modal_stacking'
    
    # Implicit deontic: weak modals
    if re.search(r'\b(expected|supposed|should|ought)\s+to\b', text_lower):
        return 'implicit_deontic'
    
    # Negation scope
    if re.search(r'\b(not\s+required|not\s+obligated|not\s+expected)\b', text_lower):
        return 'negation_scope'
    if re.search(r'\b(must\s+not|shall\s+not|cannot)\b', text_lower):
        if true_label == 'prohibition' and pred_label != 'prohibition':
            return 'negation_scope'
    
    # Conditional
    if re.search(r'\b(if|when|unless|provided|subject to)\b.*\b(then|must|shall|may)\b', text_lower):
        return 'conditional'
    
    # Temporal
    if re.search(r'\b(before|after|prior to|following|during)\b', text_lower):
        return 'temporal'
    
    return 'other'


def analyze_errors(gold_standard, predictions):
    """
    Comprehensive error analysis
    
    Returns:
        dict with error statistics, categorization, and examples
    """
    # Match predictions to gold standard
    pred_map = {p['id']: p for p in predictions}
    
    errors = []
    correct = []
    
    # Confusion matrix
    confusion = defaultdict(int)
    
    for rule in gold_standard:
        rule_id = rule['id']
        true_label = rule['rule_type']
        
        if rule_id not in pred_map:
            print(f"Warning: {rule_id} not in predictions, skipping")
            continue
        
        pred = pred_map[rule_id]
        pred_label = pred.get('rule_type', pred.get('predicted_type'))
        confidence = pred.get('confidence', 0.0)
        
        # Update confusion matrix
        confusion[(true_label, pred_label)] += 1
        
        if pred_label != true_label:
            # ERROR
            category = categorize_error(rule['text'], true_label, pred_label)
            
            errors.append({
                'id': rule_id,
                'text': rule['text'],
                'true_label': true_label,
                'predicted_label': pred_label,
                'confidence': confidence,
                'category': category,
                'source': rule['source']
            })
        else:
            # CORRECT
            correct.append({
                'id': rule_id,
                'confidence': confidence
            })
    
    # Calculate statistics
    total = len(gold_standard)
    error_count = len(errors)
    accuracy = (total - error_count) / total if total > 0 else 0
    
    # Categorize errors
    error_categories = Counter(e['category'] for e in errors)
    
    # Confidence analysis
    error_confidences = [e['confidence'] for e in errors]
    correct_confidences = [c['confidence'] for c in correct]
    
    avg_error_conf = sum(error_confidences) / len(error_confidences) if error_confidences else 0
    avg_correct_conf = sum(correct_confidences) / len(correct_confidences) if correct_confidences else 0
    
    return {
        'total_rules': total,
        'errors': error_count,
        'correct': total - error_count,
        'accuracy': accuracy,
        'error_rate': 1 - accuracy,
        'confusion_matrix': dict(confusion),
        'error_categories': dict(error_categories),
        'avg_confidence': {
            'errors': avg_error_conf,
            'correct': avg_correct_conf,
            'difference': avg_correct_conf - avg_error_conf
        },
        'error_details': errors,
        'high_confidence_errors': [e for e in errors if e['confidence'] > 0.8]
    }


def format_confusion_matrix(confusion: dict) -> str:
    """Format confusion matrix for display"""
    classes = ['obligation', 'permission', 'prohibition']
    
    lines = ["\nConfusion Matrix (Rows = True, Columns = Predicted):\n"]
    lines.append("=" * 70)
    
    # Header
    header = "              " + "".join(f"{c:>14}" for c in classes)
    lines.append(header)
    lines.append("=" * 70)
    
    # Rows
    for true_cls in classes:
        row = f"{true_cls:>13} |"
        for pred_cls in classes:
            count = confusion.get((true_cls, pred_cls), 0)
            row += f"{count:>13} "
        lines.append(row)
    
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze classification errors in detail'
    )
    parser.add_argument(
        '--gold',
        default='research/gold_standard_annotated.json',
        help='Gold standard path'
    )
    parser.add_argument(
        '--predictions',
        default='research/model_comparison_results.json',
        help='Model predictions path'
    )
    parser.add_argument(
        '--model',
        default='mistral',
        help='Model name to analyze'
    )
    parser.add_argument(
        '--output',
        default='research/error_analysis_results.json',
        help='Output path'
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*70}")
    print("ERROR ANALYSIS")
    print(f"{'='*70}\n")
    
    # Load data
    gold_standard = load_gold_standard(args.gold)
    print(f"✓ Loaded {len(gold_standard)} gold standard rules")
    
    # Load predictions
    pred_data = load_model_predictions(args.predictions)
    
    # Extract model-specific predictions
    # Structure: {model_results: {model_name: [{id, result}, ...]}}
    if 'model_results' in pred_data:
        model_results = pred_data['model_results'].get(args.model, [])
        # Convert to standard format
        predictions = []
        for item in model_results:
            result = item.get('result', {})
            # Skip parsing errors
            if result.get('is_rule') is None:
                continue
            
            predictions.append({
                'id': item.get('id'),
                'rule_type': result.get('rule_type'),
                'confidence': result.get('confidence', 0.0)
            })
    elif 'models' in pred_data:
        # Structure: {models: {model_name: {predictions: [...]}}}
        model_data = pred_data['models'].get(args.model, {})
        predictions = model_data.get('predictions', [])
    elif 'predictions' in pred_data:
        # Structure: {predictions: [...]}
        predictions = pred_data['predictions']
    else:
        print(f"✗ Error: Cannot find predictions in {args.predictions}")
        return
    
    print(f"✓ Loaded {len(predictions)} predictions for model '{args.model}'")
    
    # Analyze
    results = analyze_errors(gold_standard, predictions)
    
    # Display results
    print(f"\n{'-'*70}")
    print("OVERALL STATISTICS")
    print(f"{'-'*70}\n")
    print(f"  Total Rules:     {results['total_rules']}")
    print(f"  Correct:         {results['correct']} ({results['accuracy']*100:.1f}%)")
    print(f"  Errors:          {results['errors']} ({results['error_rate']*100:.1f}%)")
    print(f"\n  Accuracy:        {results['accuracy']:.4f}")
    
    # Confusion matrix
    print(format_confusion_matrix(results['confusion_matrix']))
    
    # Error categories
    print(f"\n{'-'*70}")
    print("ERROR CATEGORIES")
    print(f"{'-'*70}\n")
    
    for category, count in sorted(results['error_categories'].items(), 
                                   key=lambda x: x[1], reverse=True):
        pct = count / results['errors'] * 100 if results['errors'] > 0 else 0
        print(f"  {category:>20}: {count:>2} ({pct:>5.1f}%)")
    
    # Confidence analysis
    print(f"\n{'-'*70}")
    print("CONFIDENCE ANALYSIS")
    print(f"{'-'*70}\n")
    print(f"  Avg confidence (correct):  {results['avg_confidence']['correct']:.3f}")
    print(f"  Avg confidence (errors):   {results['avg_confidence']['errors']:.3f}")
    print(f"  Difference:                {results['avg_confidence']['difference']:.3f}")
    
    if results['avg_confidence']['difference'] > 0:
        print(f"\n  → Model is LESS confident on errors (good calibration)")
    else:
        print(f"\n  → Model is MORE confident on errors (poor calibration)")
    
    # High confidence errors
    if results['high_confidence_errors']:
        print(f"\n{'-'*70}")
        print(f"HIGH CONFIDENCE ERRORS (confidence > 0.8)")
        print(f"{'-'*70}\n")
        
        for i, err in enumerate(results['high_confidence_errors'][:3], 1):
            print(f"{i}. {err['id']}: {err['text'][:80]}...")
            print(f"   True: {err['true_label']}, Predicted: {err['predicted_label']}")
            print(f"   Confidence: {err['confidence']:.2f}, Category: {err['category']}")
            print()
    
    # Detailed error examples
    print(f"\n{'-'*70}")
    print(f"ERROR EXAMPLES (showing top 5)")
    print(f"{'-'*70}\n")
    
    for i, err in enumerate(results['error_details'][:5], 1):
        print(f"{i}. {err['id']}")
        print(f"   Text: {err['text'][:100]}...")
        print(f"   True: {err['true_label']} → Predicted: {err['predicted_label']}")
        print(f"   Category: {err['category']}, Confidence: {err['confidence']:.2f}")
        print()
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Results saved to: {output_path}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
