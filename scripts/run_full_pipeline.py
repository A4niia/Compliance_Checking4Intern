#!/usr/bin/env python3
"""
Cross-Institutional Pipeline Orchestrator
==========================================
Runs the full extraction → classification → FOL → SHACL pipeline
for any institution (AIT, CU, TU).

Usage:
    python scripts/run_full_pipeline.py --source ait
    python scripts/run_full_pipeline.py --source cu
    python scripts/run_full_pipeline.py --source tu
    python scripts/run_full_pipeline.py --source all
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Ensure pdfplumber is available
try:
    import pdfplumber
except ImportError:
    print("⚠️  pdfplumber not installed. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
    import pdfplumber

# Ensure requests is available
try:
    import requests
except ImportError:
    print("⚠️  requests not installed. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent.parent
POLICY_DIR = PROJECT_ROOT / "insitutional_policy"
RESEARCH_DIR = PROJECT_ROOT / "research"
SHACL_DIR = PROJECT_ROOT / "shacl"

# Valid sources
SOURCES = {
    "ait": {"name": "Asian Institute of Technology", "short": "AIT", "prefix": "ait"},
    "cu":  {"name": "Chulalongkorn University",      "short": "CU",  "prefix": "cu"},
    "tu":  {"name": "Thammasat University",           "short": "TU",  "prefix": "tu"},
}

# Ollama config
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://10.99.200.2:11434")
MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# Deontic markers for extraction
DEONTIC_MARKERS = [
    r'\bmust\b', r'\bshall\b', r'\brequired\b', r'\bobligated\b',
    r'\bprohibited\b', r'\bforbidden\b', r'\bmay not\b', r'\bmust not\b',
    r'\bshall not\b', r'\bmay\b', r'\ballowed\b', r'\bpermitted\b',
    r'\bis entitled\b', r'\bhas to\b', r'\bhave to\b',
    r'\bwill be\b.*\b(suspended|terminated|dismissed|fined)\b',
    r'\bcannot\b',
]
RULE_PATTERN = re.compile('|'.join(DEONTIC_MARKERS), re.IGNORECASE)


# =============================================================================
# STEP 1: EXTRACT SENTENCES FROM PDFs
# =============================================================================

def extract_sentences_from_pdf(pdf_path: Path) -> List[Dict]:
    """Extract sentences from a PDF using pdfplumber."""

    sentences = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            # Split into sentences
            page_sentences = re.split(r'(?<=[.!?])\s+', text)
            for sent in page_sentences:
                sent = sent.strip()
                sent = re.sub(r'\s+', ' ', sent)  # normalize whitespace
                if len(sent) < 20:
                    continue
                sentences.append({
                    "text": sent,
                    "page": page_num,
                    "source": pdf_path.name,
                })
    return sentences


def step1_extract(source: str) -> Path:
    """Extract all sentences from PDFs for a given source."""
    print(f"\n{'='*65}")
    print(f"  STEP 1: EXTRACT SENTENCES — {SOURCES[source]['name']}")
    print(f"{'='*65}")

    docs_dir = POLICY_DIR / SOURCES[source]["short"] if source != "ait" else POLICY_DIR / "AIT"
    if not docs_dir.exists():
        print(f"  ❌ Policy directory not found: {docs_dir}")
        return None

    pdf_files = sorted(docs_dir.glob("*.pdf"))
    print(f"  📁 Found {len(pdf_files)} PDFs in {docs_dir.name}/")

    all_sentences = []
    for pdf_path in pdf_files:
        sents = extract_sentences_from_pdf(pdf_path)
        print(f"    📄 {pdf_path.name}: {len(sents)} sentences")
        all_sentences.extend(sents)

    print(f"  📊 Total extracted: {len(all_sentences)} sentences")

    # Save
    out_dir = RESEARCH_DIR / source
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "extracted_sentences.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "source": SOURCES[source]["name"],
            "extraction_date": datetime.now().isoformat(),
            "total_sentences": len(all_sentences),
            "documents": len(pdf_files),
            "sentences": all_sentences,
        }, f, indent=2, ensure_ascii=False)
    print(f"  💾 Saved: {out_file.relative_to(PROJECT_ROOT)}")
    return out_file


# =============================================================================
# STEP 2: PRE-FILTER + CLASSIFY CANDIDATES
# =============================================================================

def prefilter_sentence(text: str) -> Dict:
    """Lightweight pre-filter: check deontic markers, length, structure."""
    words = text.split()
    # Length check
    if len(words) < 5:
        return {"is_candidate": False, "reason": "too_short", "strength": "none"}
    if len(words) > 200:
        return {"is_candidate": False, "reason": "too_long", "strength": "none"}

    # Deontic marker check
    strong = re.search(
        r'\b(must|shall|required|obligated|prohibited|forbidden|must not|shall not)\b',
        text, re.IGNORECASE
    )
    weak = re.search(
        r'\b(may|should|allowed|permitted|entitled|has to|have to|cannot)\b',
        text, re.IGNORECASE
    )
    consequence = re.search(
        r'\b(suspended|terminated|dismissed|fined|penalty|sanction|expel)\b',
        text, re.IGNORECASE
    )

    if strong:
        return {"is_candidate": True, "reason": "strong_deontic", "strength": "strong",
                "markers": [strong.group()]}
    if consequence:
        return {"is_candidate": True, "reason": "consequence", "strength": "consequence",
                "markers": [consequence.group()]}
    if weak:
        return {"is_candidate": True, "reason": "weak_deontic", "strength": "weak",
                "markers": [weak.group()]}

    return {"is_candidate": False, "reason": "no_deontic_markers", "strength": "none"}


def classify_with_llm(text: str, source_name: str) -> Dict:
    """Classify a sentence using Ollama LLM."""

    prompt = f"""You are a legal policy analyst. Classify whether the following sentence from {source_name} is a POLICY RULE (a binding obligation, permission, or prohibition) or NOT A RULE (descriptive, procedural, or informational).

Sentence: "{text}"

Respond ONLY with a JSON object:
{{"is_rule": true/false, "rule_type": "obligation"/"permission"/"prohibition"/"none", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.1, "num_predict": 256}},
            timeout=60,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "")

        # Parse JSON from response
        match = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            return result
        return {"is_rule": False, "rule_type": "none", "confidence": 0.0,
                "reasoning": "Failed to parse LLM response", "raw": raw[:200]}
    except Exception as e:
        return {"is_rule": False, "rule_type": "none", "confidence": 0.0,
                "error": str(e)[:200]}


def step2_classify(source: str) -> Path:
    """Pre-filter and classify sentences."""
    print(f"\n{'='*65}")
    print(f"  STEP 2: PRE-FILTER + CLASSIFY — {SOURCES[source]['name']}")
    print(f"{'='*65}")

    in_file = RESEARCH_DIR / source / "extracted_sentences.json"
    if not in_file.exists():
        print(f"  ❌ Input not found: {in_file}")
        return None

    with open(in_file, encoding="utf-8") as f:
        data = json.load(f)

    sentences = data["sentences"]
    print(f"  📋 Loaded {len(sentences)} sentences")

    # Pre-filter
    candidates = []
    rejected = []
    for sent in sentences:
        pf = prefilter_sentence(sent["text"])
        sent["prefilter"] = pf
        if pf["is_candidate"]:
            candidates.append(sent)
        else:
            rejected.append(sent)

    print(f"  🔍 Pre-filter: {len(candidates)} candidates, {len(rejected)} rejected")
    if len(sentences) > 0:
        print(f"     Filter rate: {len(rejected)/len(sentences)*100:.1f}%")
    else:
        print("  ⚠️  No sentences extracted — check PDF files and pdfplumber installation")
        return None

    # Classify candidates with LLM
    print(f"  🤖 Classifying {len(candidates)} candidates via {MODEL}...")
    source_name = SOURCES[source]["name"]
    classified = []
    rules_found = 0

    for i, sent in enumerate(candidates):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"     [{i+1}/{len(candidates)}]...", flush=True)

        result = classify_with_llm(sent["text"], source_name)
        sent["classification"] = result
        classified.append(sent)

        if result.get("is_rule"):
            rules_found += 1

    # Assign IDs to detected rules
    rule_idx = 0
    prefix = SOURCES[source]["prefix"].upper()
    for sent in classified:
        if sent["classification"].get("is_rule"):
            rule_idx += 1
            sent["rule_id"] = f"{prefix}-R{rule_idx:03d}"

    print(f"\n  📊 Results:")
    print(f"     Total sentences:    {len(sentences)}")
    print(f"     Candidates:         {len(candidates)}")
    print(f"     Rules detected:     {rules_found}")
    print(f"     Detection rate:     {rules_found/max(len(sentences),1)*100:.1f}%")

    # Count by type
    type_counts = {"obligation": 0, "permission": 0, "prohibition": 0}
    for s in classified:
        rt = s["classification"].get("rule_type", "none")
        if rt in type_counts:
            type_counts[rt] += 1
    print(f"     By type: O={type_counts['obligation']}, "
          f"P={type_counts['permission']}, F={type_counts['prohibition']}")

    # Save
    out_file = RESEARCH_DIR / source / "classified_rules.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "source": source_name,
            "classification_date": datetime.now().isoformat(),
            "model": MODEL,
            "total_sentences": len(sentences),
            "candidates": len(candidates),
            "rules_detected": rules_found,
            "deontic_distribution": type_counts,
            "classified_sentences": classified,
            "rejected_sentences": [{"text": s["text"], "source": s["source"],
                                     "reason": s["prefilter"]["reason"]}
                                    for s in rejected],
        }, f, indent=2, ensure_ascii=False)
    print(f"  💾 Saved: {out_file.relative_to(PROJECT_ROOT)}")
    return out_file


# =============================================================================
# STEP 3: GENERATE FOL FORMULAS
# =============================================================================

def generate_fol_for_rule(text: str, rule_type: str, source_name: str) -> Dict:
    """Generate FOL formula for a classified rule."""
    import requests

    prompt = f"""You are a formal logic expert. Convert the following policy rule into First-Order Logic (FOL) with deontic operators.

Policy rule from {source_name}: "{text}"
Rule type: {rule_type}

Use these deontic operators:
- O(φ) for obligations (must, shall, required)
- P(φ) for permissions (may, allowed, permitted)
- F(φ) for prohibitions (must not, prohibited, forbidden)

Respond ONLY with a JSON object:
{{"fol_formula": "the FOL formula", "subject": "who it applies to", "predicate": "what action", "variables": ["x", "y"]}}"""

    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.1, "num_predict": 512}},
            timeout=90,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "")

        match = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"fol_formula": "PARSE_ERROR", "raw": raw[:300]}
    except Exception as e:
        return {"fol_formula": "ERROR", "error": str(e)[:200]}


def step3_fol(source: str) -> Path:
    """Generate FOL formulas for all classified rules."""
    print(f"\n{'='*65}")
    print(f"  STEP 3: FOL FORMALIZATION — {SOURCES[source]['name']}")
    print(f"{'='*65}")

    in_file = RESEARCH_DIR / source / "classified_rules.json"
    if not in_file.exists():
        print(f"  ❌ Input not found: {in_file}")
        return None

    with open(in_file, encoding="utf-8") as f:
        data = json.load(f)

    rules = [s for s in data["classified_sentences"] if s["classification"].get("is_rule")]
    print(f"  📋 Generating FOL for {len(rules)} rules...")

    source_name = SOURCES[source]["name"]
    fol_results = []
    success = 0

    for i, rule in enumerate(rules):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"     [{i+1}/{len(rules)}]...", flush=True)

        result = generate_fol_for_rule(
            rule["text"],
            rule["classification"].get("rule_type", "obligation"),
            source_name,
        )
        fol_results.append({
            "rule_id": rule.get("rule_id", f"R{i+1}"),
            "text": rule["text"],
            "source_document": rule.get("source", ""),
            "rule_type": rule["classification"].get("rule_type"),
            "fol": result,
        })
        if result.get("fol_formula") not in ("PARSE_ERROR", "ERROR"):
            success += 1

    print(f"\n  📊 FOL generation: {success}/{len(rules)} successful ({success/max(len(rules),1)*100:.1f}%)")

    # Save
    out_file = RESEARCH_DIR / source / "fol_formulas.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "source": source_name,
            "fol_date": datetime.now().isoformat(),
            "model": MODEL,
            "total_rules": len(rules),
            "successful": success,
            "formulas": fol_results,
        }, f, indent=2, ensure_ascii=False)
    print(f"  💾 Saved: {out_file.relative_to(PROJECT_ROOT)}")
    return out_file


# =============================================================================
# STEP 4: GENERATE SHACL SHAPES
# =============================================================================

ENTITY_MAP = {
    "student": "Student", "postgraduate": "PostgraduateStudent",
    "faculty": "FacultyMember", "staff": "StaffMember",
    "researcher": "Researcher", "advisor": "Advisor",
    "committee": "Committee", "institution": "Institution",
    "university": "University", "person": "Person",
}

SEVERITY_MAP = {
    "obligation": "sh:Violation", "prohibition": "sh:Violation", "permission": "sh:Info"
}


def detect_target_class(text: str) -> str:
    """Detect target class from rule text."""
    text_lower = text.lower()
    for keyword, cls in ENTITY_MAP.items():
        if keyword in text_lower:
            return cls
    return "Person"


def make_shacl_shape(rule: Dict, idx: int, prefix: str) -> str:
    """Generate a SHACL shape for a single rule."""
    rule_type = rule.get("rule_type", "obligation")
    text = rule.get("text", "")
    rule_id = rule.get("rule_id", f"R{idx}")
    target = detect_target_class(text)
    severity = SEVERITY_MAP.get(rule_type, "sh:Info")
    prop_name = re.sub(r'[^a-zA-Z0-9]', '', rule_id)

    shape = f"""
{prefix}:{prop_name}Shape a sh:NodeShape ;
    sh:targetClass {prefix}:{target} ;
    rdfs:comment "{text[:120].replace('"', "'")}" ;
    sh:severity {severity} ;
    sh:property [
        sh:path {prefix}:{prop_name}Compliance ;
        sh:name "{rule_id}: {rule_type}" ;"""

    if rule_type == "obligation":
        shape += "\n        sh:minCount 1 ;"
    elif rule_type == "prohibition":
        shape += "\n        sh:maxCount 0 ;"

    shape += f"""
        sh:message "{rule_type.title()}: {text[:80].replace('"', "'")}" ;
    ] ."""
    return shape


def step4_shacl(source: str) -> Path:
    """Generate SHACL shapes from FOL results."""
    print(f"\n{'='*65}")
    print(f"  STEP 4: SHACL GENERATION — {SOURCES[source]['name']}")
    print(f"{'='*65}")

    in_file = RESEARCH_DIR / source / "fol_formulas.json"
    if not in_file.exists():
        print(f"  ❌ Input not found: {in_file}")
        return None

    with open(in_file, encoding="utf-8") as f:
        data = json.load(f)

    rules = data["formulas"]
    prefix = SOURCES[source]["prefix"]
    print(f"  📋 Generating SHACL for {len(rules)} rules...")

    # Build prefix header
    header = f"""@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix {prefix}: <http://example.org/{prefix}-policy#> .
"""

    shapes = [header]
    for i, rule in enumerate(rules, 1):
        shape = make_shacl_shape(rule, i, prefix)
        shapes.append(shape)

    # Save
    out_dir = SHACL_DIR / source
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{source}_shapes.ttl"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(shapes))

    # Count triples (rough estimate: ~16 per shape)
    triple_count = len(rules) * 16
    print(f"  📊 Generated {len(rules)} shapes (~{triple_count} triples)")
    print(f"  💾 Saved: {out_file.relative_to(PROJECT_ROOT)}")

    # Save summary
    summary_file = RESEARCH_DIR / source / "shacl_summary.json"
    type_counts = {"obligation": 0, "permission": 0, "prohibition": 0}
    for r in rules:
        rt = r.get("rule_type", "obligation")
        if rt in type_counts:
            type_counts[rt] += 1

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "source": SOURCES[source]["name"],
            "total_shapes": len(rules),
            "estimated_triples": triple_count,
            "by_type": type_counts,
            "output_file": str(out_file.relative_to(PROJECT_ROOT)),
        }, f, indent=2, ensure_ascii=False)

    return out_file


# =============================================================================
# STEP 5: SUMMARY REPORT
# =============================================================================

def step5_report(source: str) -> Path:
    """Generate a summary report for the pipeline run."""
    print(f"\n{'='*65}")
    print(f"  STEP 5: PIPELINE REPORT — {SOURCES[source]['name']}")
    print(f"{'='*65}")

    report = {
        "source": SOURCES[source]["name"],
        "source_code": source,
        "pipeline_date": datetime.now().isoformat(),
        "model": MODEL,
    }

    # Load each step's results
    extract_file = RESEARCH_DIR / source / "extracted_sentences.json"
    classify_file = RESEARCH_DIR / source / "classified_rules.json"
    fol_file = RESEARCH_DIR / source / "fol_formulas.json"
    shacl_file = RESEARCH_DIR / source / "shacl_summary.json"

    if extract_file.exists():
        with open(extract_file, encoding="utf-8") as f:
            d = json.load(f)
        report["extraction"] = {
            "documents": d.get("documents", 0),
            "total_sentences": d.get("total_sentences", 0),
        }

    if classify_file.exists():
        with open(classify_file, encoding="utf-8") as f:
            d = json.load(f)
        report["classification"] = {
            "candidates": d.get("candidates", 0),
            "rules_detected": d.get("rules_detected", 0),
            "detection_rate": f"{d.get('rules_detected',0)/max(d.get('total_sentences',1),1)*100:.1f}%",
            "deontic_distribution": d.get("deontic_distribution", {}),
        }

    if fol_file.exists():
        with open(fol_file, encoding="utf-8") as f:
            d = json.load(f)
        report["fol"] = {
            "total_rules": d.get("total_rules", 0),
            "successful": d.get("successful", 0),
            "success_rate": f"{d.get('successful',0)/max(d.get('total_rules',1),1)*100:.1f}%",
        }

    if shacl_file.exists():
        with open(shacl_file, encoding="utf-8") as f:
            d = json.load(f)
        report["shacl"] = d

    # Print summary
    print(f"\n  {'─'*40}")
    for section, data in report.items():
        if isinstance(data, dict):
            print(f"  {section}:")
            for k, v in data.items():
                print(f"    {k}: {v}")
    print(f"  {'─'*40}")

    # Save
    out_file = RESEARCH_DIR / source / "pipeline_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  💾 Saved: {out_file.relative_to(PROJECT_ROOT)}")
    return out_file


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

def run_pipeline(source: str, skip_llm: bool = False):
    """Run the full pipeline for a given source."""
    t0 = time.time()
    print(f"\n{'━'*65}")
    print(f"  FULL PIPELINE: {SOURCES[source]['name']}")
    print(f"{'━'*65}")

    # Step 1: Extract
    result = step1_extract(source)
    if not result:
        return

    if skip_llm:
        print(f"\n  ⏭️  Skipping LLM steps (--extract-only mode)")
        return

    # Step 2: Classify
    result = step2_classify(source)
    if not result:
        return

    # Step 3: FOL
    result = step3_fol(source)
    if not result:
        return

    # Step 4: SHACL
    step4_shacl(source)

    # Step 5: Report
    step5_report(source)

    elapsed = time.time() - t0
    print(f"\n{'━'*65}")
    print(f"  ✅ Pipeline complete for {SOURCES[source]['name']}")
    print(f"     Elapsed: {elapsed:.1f}s")
    print(f"{'━'*65}")


def main():
    parser = argparse.ArgumentParser(
        description="Cross-Institutional Policy Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_full_pipeline.py --source ait
  python scripts/run_full_pipeline.py --source cu
  python scripts/run_full_pipeline.py --source all
  python scripts/run_full_pipeline.py --source cu --extract-only
        """,
    )
    parser.add_argument("--source", required=True,
                        choices=list(SOURCES.keys()) + ["all"],
                        help="Institution to process")
    parser.add_argument("--extract-only", action="store_true",
                        help="Only extract sentences (no LLM)")
    args = parser.parse_args()

    if args.source == "all":
        for src in SOURCES:
            run_pipeline(src, skip_llm=args.extract_only)
    else:
        run_pipeline(args.source, skip_llm=args.extract_only)


if __name__ == "__main__":
    main()
