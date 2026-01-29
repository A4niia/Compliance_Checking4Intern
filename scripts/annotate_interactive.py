#!/usr/bin/env python3
"""
Interactive Human Annotation Tool
Guides annotators through policy rule classification.
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"


def load_data(filepath: Path):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_data(data, filepath: Path):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def show_rule(rule, idx, total):
    print("\n" + "=" * 70)
    print(f"RULE {idx}/{total}: {rule['id']}")
    print("=" * 70)
    print(f"Source: {rule.get('source_document', 'Unknown')}")
    print(f"Page: {rule.get('page_number', 'N/A')}")
    print("-" * 70)
    print("TEXT:")
    print(rule['original_text'])
    print("-" * 70)


def get_annotation():
    print("\nANNOTATION OPTIONS:")
    print("  1. OBLIGATION (must, shall, required)")
    print("  2. PERMISSION (may, can, allowed)")
    print("  3. PROHIBITION (must not, cannot, forbidden)")
    print("  4. NOT A RULE (factual statement, description)")
    print("  s. SKIP for now")
    print("  q. QUIT and save")
    
    while True:
        choice = input("\nYour choice [1/2/3/4/s/q]: ").strip().lower()
        
        if choice == '1':
            return {'is_rule': True, 'rule_type': 'obligation'}
        elif choice == '2':
            return {'is_rule': True, 'rule_type': 'permission'}
        elif choice == '3':
            return {'is_rule': True, 'rule_type': 'prohibition'}
        elif choice == '4':
            return {'is_rule': False, 'rule_type': None}
        elif choice == 's':
            return None  # Skip
        elif choice == 'q':
            return 'quit'
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, s, or q.")


def get_confidence():
    while True:
        try:
            conf = int(input("Confidence (1-5, where 5=very confident): "))
            if 1 <= conf <= 5:
                return conf
        except ValueError:
            pass
        print("Please enter a number between 1 and 5.")


def get_deontic_marker(text):
    markers = ['must', 'shall', 'may', 'can', 'cannot', 'required', 'prohibited', 'should']
    for m in markers:
        if m in text.lower():
            return m
    return input("Deontic marker (e.g., must, may): ").strip() or None


def main():
    print("=" * 70)
    print("HUMAN ANNOTATION TOOL")
    print("=" * 70)
    
    # Get annotator name
    annotator = input("Enter your name: ").strip()
    if not annotator:
        annotator = "Anonymous"
    
    # Load data
    gs_file = RESEARCH_DIR / "gold_standard_template.json"
    data = load_data(gs_file)
    
    # Find unannotated rules
    unannotated = []
    for i, rule in enumerate(data):
        ann = rule.get('human_annotation', {})
        if ann.get('is_rule') is None:
            unannotated.append((i, rule))
    
    print(f"\nFound {len(unannotated)} unannotated rules out of {len(data)} total.")
    print("Press Enter to start...")
    input()
    
    # Annotate
    annotated_count = 0
    for idx, (i, rule) in enumerate(unannotated, 1):
        show_rule(rule, idx, len(unannotated))
        
        result = get_annotation()
        
        if result == 'quit':
            break
        elif result is None:
            continue  # Skip
        
        # Get additional details
        confidence = get_confidence()
        deontic = get_deontic_marker(rule['original_text']) if result['is_rule'] else None
        notes = input("Notes (optional): ").strip()
        
        # Update annotation
        data[i]['human_annotation'] = {
            'is_rule': result['is_rule'],
            'rule_type': result['rule_type'],
            'subject': None,  # Can be added if needed
            'condition': None,
            'action': None,
            'deontic_marker': deontic,
            'annotator': annotator,
            'annotation_date': datetime.now().isoformat(),
            'confidence': confidence,
            'notes': notes
        }
        
        annotated_count += 1
        
        # Auto-save every 5 annotations
        if annotated_count % 5 == 0:
            save_data(data, gs_file)
            print(f"\n✅ Auto-saved ({annotated_count} annotations)")
    
    # Final save
    save_data(data, gs_file)
    print(f"\n" + "=" * 70)
    print(f"DONE! Annotated {annotated_count} rules.")
    print(f"Saved to: {gs_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
