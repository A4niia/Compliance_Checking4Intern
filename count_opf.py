import json

with open('research/gold_standard_annotated_v4.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total entries: {len(data)}")

# Count by human_annotation
is_rule_true = [r for r in data if r.get('human_annotation', {}).get('is_rule') == True]
is_rule_false = [r for r in data if r.get('human_annotation', {}).get('is_rule') == False]

print(f"\nHuman Annotation:")
print(f"  is_rule=True:  {len(is_rule_true)}")
print(f"  is_rule=False: {len(is_rule_false)}")

# Count O/P/F for validated rules only
obligations = [r for r in is_rule_true if r.get('human_annotation', {}).get('rule_type') == 'obligation']
permissions = [r for r in is_rule_true if r.get('human_annotation', {}).get('rule_type') == 'permission']
prohibitions = [r for r in is_rule_true if r.get('human_annotation', {}).get('rule_type') == 'prohibition']
no_type = [r for r in is_rule_true if not r.get('human_annotation', {}).get('rule_type')]

print(f"\nDeontic Distribution (validated rules only):")
print(f"  Obligations:  {len(obligations)}")
print(f"  Permissions:  {len(permissions)}")
print(f"  Prohibitions: {len(prohibitions)}")
print(f"  No type set:  {len(no_type)}")
print(f"  Sum: {len(obligations) + len(permissions) + len(prohibitions)}")

# If sum doesn't match, show the discrepancy
if len(no_type) > 0:
    print(f"\n=== Rules with is_rule=True but no rule_type ===")
    for r in no_type[:5]:
        print(f"  {r['id']}: {r.get('original_text', '')[:60]}...")
