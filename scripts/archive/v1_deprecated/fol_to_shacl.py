#!/usr/bin/env python3
"""FOL to SHACL Translation - v2 Clean"""

import json
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"
SHACL_DIR = PROJECT_ROOT / "shacl"

PREFIXES = """@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ait: <http://example.org/ait-policy#> .
@prefix deontic: <http://example.org/deontic#> .
"""

SEVERITY = {"obligation": "sh:Violation", "prohibition": "sh:Violation", "permission": "sh:Info"}

def clean(text):
    if not text: return ""
    text = str(text).replace('\n', ' ').replace('\r', ' ').replace('"', "'").replace('\\', '')
    return re.sub(r'\s+', ' ', text).strip()[:100]

def normalize(pred):
    pred = re.sub(r'[^A-Za-z0-9_]', '', str(pred))
    return pred.capitalize() if pred else "Thing"

def extract_preds(formula):
    matches = re.findall(r'([A-Za-z][A-Za-z0-9_]*)\s*\(', str(formula))
    skip = {'forall', 'exists', 'O', 'P', 'F', 'implies', 'and', 'or', 'not', 'if', 'then', 'Within', 'Before'}
    return [m for m in matches if m not in skip][:4]

def make_shape(rule, idx):
    fol = rule.get('fol_formalization', {})
    if not fol or 'error' in fol: return ""
    rule_id = rule.get('id', f'R{idx}')
    dtype = fol.get('deontic_type', 'obligation')
    formula = fol.get('deontic_formula', '') + ' ' + fol.get('fol_expansion', '')
    orig = clean(rule.get('original_text', ''))
    preds = extract_preds(formula)
    main = normalize(preds[0]) if preds else "Thing"
    sev = SEVERITY.get(dtype, 'sh:Warning')
    shape = f"\nait:{normalize(rule_id)}Shape a sh:NodeShape ;\n"
    shape += f"    sh:targetClass ait:{main} ;\n"
    shape += f'    rdfs:label "{rule_id}" ;\n'
    shape += f'    rdfs:comment "{orig}" ;\n'
    shape += f"    deontic:type deontic:{dtype} ;\n"
    shape += f"    sh:severity {sev}"
    for p in preds[1:4]:
        shape += f" ;\n    sh:property [ sh:path ait:{normalize(p).lower()} ; sh:minCount 1 ]"
    shape += " .\n"
    return shape

def main():
    print("FOL TO SHACL v2")
    SHACL_DIR.mkdir(exist_ok=True)
    rf = RESEARCH_DIR / "fol_formalization_v2_results.json"
    if not rf.exists(): rf = RESEARCH_DIR / "fol_formalization_results.json"
    with open(rf, 'r', encoding='utf-8') as f: data = json.load(f)
    rules = data['formalized_rules']
    out = PREFIXES + "\n"
    out += "ait:PolicyOntology a owl:Ontology .\n"
    out += "deontic:obligation a rdfs:Class .\ndeontic:permission a rdfs:Class .\ndeontic:prohibition a rdfs:Class .\n"
    stats = {"obligation": 0, "permission": 0, "prohibition": 0}
    for i, r in enumerate(rules, 1):
        fol = r.get('fol_formalization', {})
        if 'error' not in fol:
            dtype = fol.get('deontic_type', 'obligation')
            if dtype in stats: stats[dtype] += 1
            out += make_shape(r, i)
    outf = SHACL_DIR / "ait_policy_shapes.ttl"
    with open(outf, 'w', encoding='utf-8') as f: f.write(out)
    print(f"Saved: {outf}")
    print(f"O:{stats['obligation']} P:{stats['permission']} F:{stats['prohibition']}")

if __name__ == "__main__": main()
