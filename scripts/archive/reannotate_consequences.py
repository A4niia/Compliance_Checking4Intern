"""
Re-annotate Gold Standard - Fix Consequence/Sanction Mislabeling

Problem: Sentences like "Sub-letting may result in eviction" are labeled as
"permission" because they contain "may", but they express PROHIBITION 
(don't sub-let) with a consequence.

Deontic Logic:
- Permission: "Students may park on campus" (allowed to do X)
- Prohibition with consequence: "Parking in fire lanes may result in fines" (not allowed)

This script identifies and corrects these systematic annotation errors.

Usage:
    python scripts/reannotate_consequences.py
"""

import json
import re
from pathlib import Path
from datetime import datetime


def is_consequence_sentence(text: str) -> bool:
    """
    Detect if sentence expresses consequence/sanction rather than true permission.
    
    Patterns:
    - "may result in [negative consequence]"
    - "may face [sanction]"
    - "may be [passive sanction]" (cancelled, fined, evicted, etc.)
    - "may have their [possession] [action]" (sealed, removed, etc.)
    - "may only be given" (restriction, not permission)
    - "may also be [sanction]"
    """
    text_lower = text.lower()
    
    # Consequence patterns
    consequence_patterns = [
        r'\bmay\s+result\s+in\b',           # may result in eviction
        r'\bmay\s+face\b',                   # may face a fine
        r'\bmay\s+be\s+(cancelled|fined|evicted|sealed|terminated|dismissed|imposed)',  # passive sanctions
        r'\bmay\s+have\s+their\s+\w+\s+(sealed|removed|cancelled)',  # possession sanctions
        r'\bmay\s+only\s+be\s+given\b',     # restrictive exception
        r'\bmay\s+also\s+be\s+(cancelled|imposed|fined)',  # additional sanctions
        r'\bmay\s+not\s+reside\b',          # negative permission = prohibition
        r'\bmay\s+be\s+locked\s+or',        # sanctions list
    ]
    
    return any(re.search(pattern, text_lower) for pattern in consequence_patterns)


def suggest_correct_type(text: str) -> str:
    """
    Suggest correct deontic type for consequence sentences.
    
    Most consequence sentences are prohibitions (forbidding the action that
    leads to the consequence), though some are obligations (you will be sanctioned).
    """
    text_lower = text.lower()
    
    # If it's a clear prohibition marker
    if re.search(r'\bmay\s+not\b', text_lower):
        return 'prohibition'
    
    # "will be" sanctions are obligations
    if re.search(r'\bwill\s+be\s+(fined|charged|terminated)', text_lower):
        return 'obligation'
    
    # Most "may result in" / "may face" are prohibitions
    # (the implicit meaning is "don't do X or Y will happen")
    if re.search(r'\b(may\s+result|may\s+face|may\s+be\s+dismissed|may\s+be\s+evicted)', text_lower):
        return 'prohibition'
    
    # Default to prohibition for consequence patterns
    return 'prohibition'


def reannotate_gold_standard(input_path: str, output_path: str):
    """
    Re-annotate gold standard file, fixing consequence mislabeling.
    
    Returns:
        dict with statistics on changes made
    """
    # Load data
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\nLoaded {len(data)} entries from {input_path}")
    
    # Track changes
    changes = []
    stats = {
        'total_rules': 0,
        'permissions': 0,
        'consequence_patterns_found': 0,
        'reannotated': 0,
        'changes': []
    }
    
    for item in data:
        human_ann = item.get('human_annotation', {})
        
        # Only process rules
        if not human_ann.get('is_rule', True):
            continue
        
        stats['total_rules'] += 1
        
        original_type = human_ann.get('rule_type')
        text = item.get('text', item.get('original_text', ''))
        
        # Count permissions
        if original_type == 'permission':
            stats['permissions'] += 1
            
            # Check if it's actually a consequence sentence
            if is_consequence_sentence(text):
                stats['consequence_patterns_found'] += 1
                
                # Suggest correct type
                suggested_type = suggest_correct_type(text)
                
                # Update annotation
                human_ann['rule_type'] = suggested_type
                human_ann['reannotation_reason'] = 'consequence_pattern'
                human_ann['original_type'] = 'permission'
                human_ann['reannotation_date'] = datetime.now().isoformat()
                
                stats['reannotated'] += 1
                
                # Track change
                change = {
                    'id': item.get('id'),
                    'text': text[:80] + '...' if len(text) > 80 else text,
                    'original': 'permission',
                    'new': suggested_type,
                    'pattern': 'consequence/sanction'
                }
                stats['changes'].append(change)
                changes.append(change)
    
    # Save updated data
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return stats, changes


def main():
    input_file = 'research/gold_standard_annotated.json'
    output_file = 'research/gold_standard_annotated_v2.json'
    
    print(f"\n{'='*70}")
    print("GOLD STANDARD RE-ANNOTATION")
    print(f"{'='*70}\n")
    
    # Re-annotate
    stats, changes = reannotate_gold_standard(input_file, output_file)
    
    # Display results
    print(f"\n{'-'*70}")
    print("STATISTICS")
    print(f"{'-'*70}\n")
    print(f"  Total rules:                {stats['total_rules']}")
    print(f"  Original permissions:       {stats['permissions']}")
    print(f"  Consequence patterns found: {stats['consequence_patterns_found']}")
    print(f"  Re-annotated:               {stats['reannotated']}")
    print(f"\n  Re-annotation rate:         {stats['reannotated']/stats['permissions']*100:.1f}% of permissions")
    
    # Show changes
    if changes:
        print(f"\n{'-'*70}")
        print(f"CHANGES MADE (showing first 10 of {len(changes)})")
        print(f"{'-'*70}\n")
        
        for i, change in enumerate(changes[:10], 1):
            print(f"{i}. {change['id']}: {change['original']} → {change['new']}")
            print(f"   Text: {change['text']}")
            print()
    
    print(f"\n{'='*70}")
    print(f"✓ Re-annotated data saved to: {output_file}")
    print(f"✓ Original file unchanged: {input_file}")
    print(f"{'='*70}\n")
    
    # Save detailed report
    report_file = 'research/reannotation_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    print(f"✓ Detailed report saved to: {report_file}\n")


if __name__ == '__main__':
    main()
