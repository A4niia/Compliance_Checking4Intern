#!/usr/bin/env python3
"""
Enhanced Rule Classification Pipeline (v2)
============================================
Two-stage classification with hierarchical pre-filtering
and section-aware LLM prompting.

Stage 1: Heuristic pre-filter (prefilter.py) — fast, no LLM
Stage 2: Enhanced LLM classification — section context + speech act hints

Research basis:
- Goknil et al. (2024) — hierarchical filtering for policy analysis
- Brodie et al. (2006) — section-aware classification
- Searle (1969) — speech act theory

Usage:
    python scripts/classify_rules_v2.py
    python scripts/classify_rules_v2.py --verbose
    python scripts/classify_rules_v2.py --compare  # Compare with v1
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# Add scripts dir to path for importing prefilter
sys.path.insert(0, str(Path(__file__).parent))
from prefilter import PreFilter, FilterResult

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://10.99.200.2:11434")
MODEL = "mistral"


# =============================================================================
# ENHANCED PROMPT with Section Context + Speech Act Hints
# =============================================================================

def build_enhanced_prompt(text: str, filter_result: FilterResult) -> str:
    """
    Build an enhanced classification prompt that includes:
    1. Section context (from pre-filter)
    2. Speech act hint (from pre-filter)
    3. Deontic marker hint (from pre-filter)
    4. Core classification task
    """
    # Section context clause
    section_clause = ""
    if filter_result.section_context:
        section_clause = f'\nCONTEXT: This text comes from the "{filter_result.section_context}" section of an academic policy document.\n'
    else:
        section_clause = "\nCONTEXT: This text comes from an academic policy document.\n"
    
    # Speech act hint
    speech_act_hint = ""
    if filter_result.speech_act == "directive":
        speech_act_hint = "HINT: This sentence appears to contain a directive (command/order). Check if it specifies a clear obligation.\n"
    elif filter_result.speech_act == "commissive":
        speech_act_hint = "HINT: This sentence appears to grant permission (uses 'may'/'entitled'). Determine if it's a NORMATIVE permission (granting institutional rights) or just a FACTUAL description of possibilities.\n"
    elif filter_result.speech_act == "prohibitive":
        speech_act_hint = "HINT: This sentence appears to contain a prohibition. Check if it forbids a specific action.\n"
    elif filter_result.speech_act == "suggestive":
        speech_act_hint = "HINT: This sentence uses 'should' or similar. Be CAREFUL: 'should' in policy often means recommendation, NOT a mandatory obligation. Only classify as rule if there's clear mandatory intent.\n"
    
    # Deontic marker hint
    marker_hint = ""
    if filter_result.deontic_markers:
        markers = ', '.join(set(m.lower() for m in filter_result.deontic_markers))
        marker_hint = f'DEONTIC MARKERS DETECTED: "{markers}"\n'
    
    prompt = f"""Analyze the following text from an academic policy document.
{section_clause}
TASK: Determine if this is a policy RULE following deontic logic.

Think step-by-step:
1. IDENTIFY the speech act: Is this a DIRECTIVE (command), COMMISSIVE (grant), PROHIBITIVE (ban), or ASSERTIVE (fact)?
2. CHECK for deontic content: Does it specify an OBLIGATION, PERMISSION, or PROHIBITION?
3. VERIFY subject: Who does this apply to?
4. DECIDE: Is this a binding normative statement or just information/procedure/suggestion?

DEFINITION of a Policy Rule (following deontic logic):
- Contains a DEONTIC operator (must, shall, may, should, required, prohibited, cannot)
- Specifies an OBLIGATION (what must be done), PERMISSION (what may be done), or PROHIBITION (what cannot be done)
- Has a clear SUBJECT (who the rule applies to)
- Has actionable REQUIREMENTS (specific actions)
- Is NOT a procedure (step-by-step instructions)
- Is NOT a suggestion or recommendation (unless clearly mandatory)
- Is NOT a factual description or definition

{speech_act_hint}{marker_hint}
CRITICAL DISTINCTIONS:
• "Students must submit by May 15" → OBLIGATION ✓ (binding requirement)
• "Students should attend workshops" → NOT a rule ✗ (recommendation only)
• "First, submit the form to the office" → NOT a rule ✗ (procedure/instruction)
• "The university provides library resources" → NOT a rule ✗ (factual description)
• "Students may request extensions" → PERMISSION ✓ (normative: grants institutional right)
• "It may rain tomorrow" → NOT a rule ✗ (epistemic possibility, not normative)

Text to analyze:
"{text}"

Respond with ONLY a JSON object (no explanation before or after):
{{
    "is_rule": true or false,
    "rule_type": "obligation" | "permission" | "prohibition" | null,
    "confidence": 0.0 to 1.0,
    "deontic_marker": "the specific word like must/shall/may" | null,
    "subject": "who this applies to" | null,
    "speech_act": "directive" | "commissive" | "prohibitive" | "assertive" | "suggestive",
    "reasoning": "one sentence explanation"
}}

JSON:"""
    
    return prompt


# =============================================================================
# CLASSIFICATION ENGINE
# =============================================================================

def classify_with_context(text: str, filter_result: FilterResult,
                         model: str = MODEL) -> Dict:
    """
    Classify a text using enhanced prompt with section context.
    
    Returns classification result with adjusted confidence
    based on pre-filter signals.
    """
    prompt = build_enhanced_prompt(text, filter_result)
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,     # Deterministic
                    "seed": 42,             # Reproducible
                    "num_predict": 800
                }
            },
            timeout=120
        )
        response.raise_for_status()
        
        result_text = response.json().get("response", "")
        
        # Parse JSON from response
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            return {"error": f"No JSON found in response: {result_text[:200]}"}
        
        # --- Apply confidence adjustment from pre-filter ---
        raw_confidence = result.get("confidence", 0.5)
        adjusted_confidence = min(1.0, max(0.0, 
            raw_confidence + filter_result.confidence_boost
        ))
        result["raw_confidence"] = raw_confidence
        result["adjusted_confidence"] = adjusted_confidence
        result["confidence"] = adjusted_confidence
        
        # --- Confidence rejection zone ---
        if 0.4 <= adjusted_confidence <= 0.6:
            result["confidence_zone"] = "uncertain"
        elif adjusted_confidence > 0.6:
            result["confidence_zone"] = "confident"
        else:
            result["confidence_zone"] = "low"
        
        # Add pre-filter metadata
        result["prefilter"] = {
            "deontic_strength": filter_result.deontic_strength,
            "section_context": filter_result.section_context,
            "section_weight": filter_result.section_weight,
            "speech_act_hint": filter_result.speech_act,
            "confidence_boost": filter_result.confidence_boost,
        }
        
        return result
        
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot connect to Ollama at {OLLAMA_HOST}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}"}
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# PIPELINE: Pre-filter → LLM Classification
# =============================================================================

def run_pipeline(gold_standard_path: Path = None, verbose: bool = False) -> Dict:
    """
    Run the full two-stage pipeline on gold standard data.
    
    Stage 1: Pre-filter (fast, heuristic)
    Stage 2: LLM classification (only for candidates)
    
    Returns pipeline results with statistics.
    """
    # Load gold standard
    if gold_standard_path is None:
        gold_standard_path = RESEARCH_DIR / "gold_standard_annotated_v2.json"
    
    if not gold_standard_path.exists():
        print(f"❌ Gold standard not found: {gold_standard_path}")
        return {}
    
    with open(gold_standard_path, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)
    
    rules = gold_data if isinstance(gold_data, list) else gold_data.get("rules", [])
    print(f"📋 Loaded {len(rules)} items from gold standard")
    
    # Initialize pre-filter
    pf = PreFilter()
    
    # --- Stage 1: Pre-filter ---
    print("\n" + "=" * 60)
    print("STAGE 1: HEURISTIC PRE-FILTER")
    print("=" * 60)
    
    filter_results = []
    for rule in rules:
        text = rule.get("original_text", rule.get("text", ""))
        source = rule.get("source_document", "")
        
        # Create a simple section context from source document name
        result = pf.filter_sentence(text, source)
        filter_results.append((rule, result))
    
    candidates = [(r, fr) for r, fr in filter_results if fr.is_candidate]
    rejected = [(r, fr) for r, fr in filter_results if not fr.is_candidate]
    
    stats = pf.get_stats([fr for _, fr in filter_results])
    print(f"\n   Total sentences: {stats['total_sentences']}")
    print(f"   Candidates: {stats['candidates']} (→ sent to LLM)")
    print(f"   Rejected: {stats['rejected']} ({stats['filter_rate']} filtered)")
    print(f"   Deontic strength: {stats['by_deontic_strength']}")
    
    # Check false negatives — rules that were filtered out but are true rules
    false_negatives = []
    for rule, fr in rejected:
        human_ann = rule.get("human_annotation", {})
        if human_ann.get("is_rule", False):
            false_negatives.append((rule, fr))
    
    if false_negatives:
        print(f"\n   ⚠️  FALSE NEGATIVES (true rules filtered out): {len(false_negatives)}")
        for rule, fr in false_negatives[:5]:
            print(f"      - {rule.get('id', '?')}: {fr.rejection_reason}")
            print(f"        Text: {rule.get('original_text', '')[:80]}...")
    else:
        print(f"\n   ✅ No false negatives — all true rules passed pre-filter")
    
    # --- Stage 2: LLM Classification ---
    print("\n" + "=" * 60)
    print("STAGE 2: ENHANCED LLM CLASSIFICATION")
    print("=" * 60)
    print(f"   Classifying {len(candidates)} candidates...")
    
    classification_results = []
    correct = 0
    uncertain = 0
    errors = 0
    
    for i, (rule, fr) in enumerate(candidates):
        text = rule.get("original_text", rule.get("text", ""))
        rule_id = rule.get("id", f"R{i}")
        
        if verbose:
            print(f"\n   [{i+1}/{len(candidates)}] {rule_id}...", end=" ", flush=True)
        
        # Classify with enhanced prompt
        result = classify_with_context(text, fr)
        
        if "error" in result:
            errors += 1
            if verbose:
                print(f"⚠️ Error: {result['error'][:50]}")
            classification_results.append({
                "rule_id": rule_id,
                "text": text[:80],
                "error": result["error"],
            })
            continue
        
        # Compare with human annotation
        human_ann = rule.get("human_annotation", {})
        human_is_rule = human_ann.get("is_rule", None)
        llm_is_rule = result.get("is_rule", False)
        
        is_correct = human_is_rule == llm_is_rule if human_is_rule is not None else None
        if is_correct:
            correct += 1
        
        if result.get("confidence_zone") == "uncertain":
            uncertain += 1
        
        if verbose:
            if is_correct:
                print(f"✅ {result.get('rule_type', 'n/a')} (conf={result['confidence']:.2f})")
            elif is_correct is not None:
                print(f"❌ predicted={llm_is_rule}, actual={human_is_rule}")
            else:
                print(f"🔍 {result.get('rule_type', 'n/a')} (no ground truth)")
        
        classification_results.append({
            "rule_id": rule_id,
            "text": text[:100],
            "is_rule": llm_is_rule,
            "rule_type": result.get("rule_type"),
            "confidence": result.get("confidence"),
            "confidence_zone": result.get("confidence_zone"),
            "speech_act": result.get("speech_act"),
            "reasoning": result.get("reasoning", ""),
            "prefilter": result.get("prefilter", {}),
            "human_is_rule": human_is_rule,
            "correct": is_correct,
        })
    
    # --- Results ---
    evaluated = sum(1 for r in classification_results if r.get("correct") is not None)
    accuracy = correct / evaluated * 100 if evaluated > 0 else 0
    
    print(f"\n{'=' * 60}")
    print("PIPELINE RESULTS")
    print(f"{'=' * 60}")
    print(f"   Pre-filter: {stats['rejected']} rejected, {stats['candidates']} candidates")
    print(f"   LLM classified: {len(classification_results)}")
    print(f"   Errors: {errors}")
    print(f"   Uncertain (0.4-0.6 conf): {uncertain}")
    print(f"   Accuracy: {correct}/{evaluated} = {accuracy:.1f}%")
    print(f"   False negatives from filter: {len(false_negatives)}")
    
    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "pipeline_version": "v2_hierarchical",
        "model": MODEL,
        "prefilter_stats": stats,
        "false_negatives": [
            {"id": r.get("id"), "text": r.get("original_text", "")[:100], 
             "reason": fr.rejection_reason}
            for r, fr in false_negatives
        ],
        "classification_results": classification_results,
        "summary": {
            "total_sentences": len(rules),
            "prefiltered_out": stats["rejected"],
            "sent_to_llm": stats["candidates"],
            "accuracy": accuracy,
            "uncertain_count": uncertain,
            "error_count": errors,
            "false_negative_count": len(false_negatives),
        }
    }
    
    output_file = RESEARCH_DIR / "classification_v2_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved: {output_file}")
    return output


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Enhanced Rule Classification Pipeline v2")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--compare", action="store_true", help="Compare with v1 results")
    args = parser.parse_args()
    
    results = run_pipeline(verbose=args.verbose)
    
    if args.compare and results:
        # Load v1 results for comparison
        v1_file = RESEARCH_DIR / "gold_standard_annotated_v2.json"
        if v1_file.exists():
            print("\n" + "=" * 60)
            print("COMPARISON: v1 vs v2 Pipeline")
            print("=" * 60)
            print(f"   v2 accuracy: {results['summary']['accuracy']:.1f}%")
            print(f"   v2 sentences sent to LLM: {results['summary']['sent_to_llm']} "
                  f"(vs {results['summary']['total_sentences']} in v1)")
            print(f"   LLM calls saved: {results['summary']['prefiltered_out']} "
                  f"({results['prefilter_stats']['filter_rate']})")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
