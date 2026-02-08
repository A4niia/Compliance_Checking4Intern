"""
Comprehensive Data Consistency Audit Script
Scans all thesis and webapp files for data discrepancies
"""
import json
import re
import os
from pathlib import Path
from collections import defaultdict

# Load authoritative source
with open('research/gold_standard_annotated_v4.json', 'r', encoding='utf-8') as f:
    gold_data = json.load(f)

# Calculate authoritative values
total_entries = len(gold_data)

# Human annotation counts
human_rules = [r for r in gold_data if r.get('human_annotation', {}).get('is_rule') == True]
human_non_rules = [r for r in gold_data if r.get('human_annotation', {}).get('is_rule') == False]

human_stats = {
    'total': total_entries,
    'rules': len(human_rules),
    'non_rules': len(human_non_rules),
    'obligation': sum(1 for r in human_rules if r.get('human_annotation', {}).get('rule_type') == 'obligation'),
    'permission': sum(1 for r in human_rules if r.get('human_annotation', {}).get('rule_type') == 'permission'),
    'prohibition': sum(1 for r in human_rules if r.get('human_annotation', {}).get('rule_type') == 'prohibition'),
}

# LLM annotation counts
llm_rules = [r for r in gold_data if r.get('llm_annotation', {}).get('is_rule') == True]
llm_non_rules = [r for r in gold_data if r.get('llm_annotation', {}).get('is_rule') == False]

llm_stats = {
    'total': total_entries,
    'rules': len(llm_rules),
    'non_rules': len(llm_non_rules),
    'obligation': sum(1 for r in llm_rules if r.get('llm_annotation', {}).get('rule_type') == 'obligation'),
    'permission': sum(1 for r in llm_rules if r.get('llm_annotation', {}).get('rule_type') == 'permission'),
    'prohibition': sum(1 for r in llm_rules if r.get('llm_annotation', {}).get('rule_type') == 'prohibition'),
}

print("=" * 60)
print("AUTHORITATIVE DATA (gold_standard_annotated_v4.json)")
print("=" * 60)
print(f"\nTotal entries: {total_entries}")
print(f"\n{'Category':<20} {'Human':<15} {'LLM v4':<15}")
print("-" * 50)
print(f"{'Is Rule (True)':<20} {human_stats['rules']:<15} {llm_stats['rules']:<15}")
print(f"{'Is Rule (False)':<20} {human_stats['non_rules']:<15} {llm_stats['non_rules']:<15}")
print(f"{'Obligations':<20} {human_stats['obligation']:<15} {llm_stats['obligation']:<15}")
print(f"{'Permissions':<20} {human_stats['permission']:<15} {llm_stats['permission']:<15}")
print(f"{'Prohibitions':<20} {human_stats['prohibition']:<15} {llm_stats['prohibition']:<15}")

# Known OBSOLETE values that should NOT appear
obsolete_values = {
    '96': 'Old LLM formalized count (now 81)',
    '65': 'Old LLM obligations (now 48)',
    '17': 'Old LLM permissions (now 15) - but 17 could be legit in other contexts',
    '14': 'Old LLM prohibitions (now 18) - but 14 could be legit in other contexts',
    '99%': 'Old accuracy claim (now 95.88%)',
    '96/97': 'Old fraction (should be 81/97 for LLM or 83/97 for human)',
}

# Define patterns to search for
patterns = [
    (r'\b96\b.*(?:rule|formali|classif)', '96 with rule/formalized/classified context'),
    (r'\b65\b.*(?:oblig|rule)', '65 with obligation/rule context'),
    (r'\b(?:oblig|rule).*\b65\b', 'obligation/rule with 65'),
    (r'\b17\b.*(?:permis|rule)', '17 with permission/rule context'),
    (r'\b15\b.*(?:prohib)', '15 with prohibition context (OLD - now 18)'),
    (r'99\s*%', '99% accuracy'),
    (r'96/97', '96/97 fraction'),
    (r'\b67\s*%', '67% (old obligation percentage)'),
    (r'\b68\s*%', '68% (old obligation percentage)'),
]

print("\n" + "=" * 60)
print("SCANNING FILES FOR POTENTIAL OBSOLETE VALUES")
print("=" * 60)

# Files to scan
scan_dirs = [
    ('d:/Thesis-PoC_v1/latex', ['.tex']),
    ('d:/Thesis-PoC_v1/RuleChecker_PoCv1/webapp/frontend/src', ['.jsx', '.js', '.tsx']),
    ('d:/Thesis-PoC_v1/RuleChecker_PoCv1/webapp/backend', ['.py']),
    ('d:/Thesis-PoC_v1/RuleChecker_PoCv1/webapp/agent', ['.py']),
]

findings = defaultdict(list)

for base_dir, extensions in scan_dirs:
    base_path = Path(base_dir)
    if not base_path.exists():
        continue
    
    for ext in extensions:
        for filepath in base_path.rglob(f'*{ext}'):
            try:
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    
                    # Check for specific concerning patterns
                    # 96 in context of rules/formalization
                    if re.search(r'\b96\b', line) and any(x in line_lower for x in ['rule', 'formali', 'classif', 'fol']):
                        findings[str(filepath)].append((i, line.strip()[:100], 'OBSOLETE: 96 rules/formalized'))
                    
                    # 65 obligations
                    if re.search(r'\b65\b', line) and 'oblig' in line_lower:
                        findings[str(filepath)].append((i, line.strip()[:100], 'OBSOLETE: 65 obligations'))
                    
                    # 99% accuracy (but not 95.88%)
                    if re.search(r'99\s*%', line) and 'accura' in line_lower and '95.88' not in line:
                        findings[str(filepath)].append((i, line.strip()[:100], 'OBSOLETE: 99% accuracy'))
                    
                    # 96/97 fraction
                    if '96/97' in line:
                        findings[str(filepath)].append((i, line.strip()[:100], 'OBSOLETE: 96/97 fraction'))
                        
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

if findings:
    print(f"\n⚠️  FOUND {sum(len(v) for v in findings.values())} POTENTIAL ISSUES:\n")
    for filepath, issues in sorted(findings.items()):
        print(f"\n📄 {filepath}")
        for line_num, line_preview, issue_type in issues:
            print(f"   L{line_num}: [{issue_type}]")
            print(f"         {line_preview}...")
else:
    print("\n✅ No obvious obsolete values found!")

# Also check for correct values that SHOULD be present
print("\n" + "=" * 60)
print("VERIFYING CORRECT VALUES ARE PRESENT")
print("=" * 60)

correct_values = {
    '97': 'Total candidates',
    '83': 'Human validated rules',
    '81': 'LLM classified rules (v4)',
    '47': 'Human obligations',
    '31': 'Human permissions', 
    '5': 'Human prohibitions',
    '48': 'LLM obligations (v4)',
    '15': 'LLM permissions (v4)',
    '18': 'LLM prohibitions (v4)',
    '95.88': 'Validated accuracy',
    '0.8503': 'Cohen kappa',
}

for value, desc in correct_values.items():
    found_in = []
    for base_dir, extensions in scan_dirs:
        base_path = Path(base_dir)
        if not base_path.exists():
            continue
        for ext in extensions:
            for filepath in base_path.rglob(f'*{ext}'):
                try:
                    content = filepath.read_text(encoding='utf-8', errors='ignore')
                    if value in content:
                        found_in.append(str(filepath.relative_to(Path('d:/Thesis-PoC_v1'))))
                except:
                    pass
    
    status = "✅" if found_in else "❌"
    print(f"{status} {value} ({desc})")
    if not found_in:
        print(f"   ⚠️  NOT FOUND in any scanned files!")
