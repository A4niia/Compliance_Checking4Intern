import json

with open('research/gold_standard_annotated_v4.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total entries: {len(data)}\n")

# Count by human_annotation
human_true = [r for r in data if r.get('human_annotation', {}).get('is_rule') == True]
human_false = [r for r in data if r.get('human_annotation', {}).get('is_rule') == False]

# Count by llm_annotation
llm_true = [r for r in data if r.get('llm_annotation', {}).get('is_rule') == True]
llm_false = [r for r in data if r.get('llm_annotation', {}).get('is_rule') == False]

print("=== is_rule Classification ===")
print(f"Human: {len(human_true)} True, {len(human_false)} False")
print(f"LLM:   {len(llm_true)} True, {len(llm_false)} False")

# Confusion Matrix
tp = sum(1 for r in data if r.get('human_annotation', {}).get('is_rule') == True and r.get('llm_annotation', {}).get('is_rule') == True)
tn = sum(1 for r in data if r.get('human_annotation', {}).get('is_rule') == False and r.get('llm_annotation', {}).get('is_rule') == False)
fp = sum(1 for r in data if r.get('human_annotation', {}).get('is_rule') == False and r.get('llm_annotation', {}).get('is_rule') == True)
fn = sum(1 for r in data if r.get('human_annotation', {}).get('is_rule') == True and r.get('llm_annotation', {}).get('is_rule') == False)

print(f"\n=== Confusion Matrix (is_rule) ===")
print(f"True Positives (both say rule):     {tp}")
print(f"True Negatives (both say not-rule): {tn}")
print(f"False Positives (LLM says rule, Human says no): {fp}")
print(f"False Negatives (LLM says no, Human says rule): {fn}")
print(f"Total: {tp + tn + fp + fn}")

print(f"\n=== Accuracy ===")
accuracy = (tp + tn) / (tp + tn + fp + fn) * 100
print(f"Accuracy: {accuracy:.2f}%")

# Show the LLM false classifications
print(f"\n=== LLM classified as NOT rules ({len(llm_false)} entries) ===")
for r in llm_false:
    hum = r.get('human_annotation', {}).get('is_rule')
    print(f"{r['id']}: Human={hum}, LLM=False")
    print(f"        Text: {r.get('original_text', '')[:60]}...")
