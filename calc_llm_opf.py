import json

with open('research/gold_standard_annotated_v4.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get LLM-identified rules (is_rule=True in llm_annotation)
llm_rules = [r for r in data if r.get('llm_annotation', {}).get('is_rule') == True]

print(f"LLM identified as rules: {len(llm_rules)}")

# Count O/P/F from LLM classification
types = {'obligation': 0, 'permission': 0, 'prohibition': 0, 'other': 0}
for r in llm_rules:
    rt = r.get('llm_annotation', {}).get('rule_type', 'other')
    if rt in types:
        types[rt] += 1
    else:
        types['other'] += 1

print(f"\nLLM O/P/F breakdown (of {len(llm_rules)} LLM-identified rules):")
print(f"  Obligations:  {types['obligation']} ({types['obligation']/len(llm_rules)*100:.1f}%)")
print(f"  Permissions:  {types['permission']} ({types['permission']/len(llm_rules)*100:.1f}%)")
print(f"  Prohibitions: {types['prohibition']} ({types['prohibition']/len(llm_rules)*100:.1f}%)")
print(f"  Other:        {types['other']}")
print(f"  Sum: {types['obligation'] + types['permission'] + types['prohibition']}")
