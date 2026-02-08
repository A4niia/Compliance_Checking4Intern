import json

with open('research/fol_formalization_v2_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

rules = data.get('formalized_rules', [])
print(f"Total formalized: {len(rules)}")

# Count by deontic type
types = {'obligation': 0, 'permission': 0, 'prohibition': 0}
for r in rules:
    dt = r.get('fol_formalization', {}).get('deontic_type', 'unknown')
    if dt in types:
        types[dt] += 1
    else:
        print(f"Unknown type: {dt} for {r.get('id')}")

print(f"O={types['obligation']}, P={types['permission']}, F={types['prohibition']}")
print(f"Sum: {sum(types.values())}")
