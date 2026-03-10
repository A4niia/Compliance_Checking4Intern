#!/usr/bin/env python3
"""
Recalculate Bootstrap CIs from Corrected Gold Standard
=======================================================
Uses the fixed gold_standard_annotated_v4.json with separate
human_llm_agreement_detection and human_llm_agreement_type fields.

Usage:
    python scripts/recalculate_bootstrap_ci.py
"""

import json
import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"
GS_FILE = RESEARCH_DIR / "gold_standard_annotated_v4.json"


def bootstrap_ci(successes: int, trials: int, n_iterations: int = 10000, confidence: float = 0.95):
    """Bootstrap confidence interval for a proportion."""
    if trials == 0:
        return 0.0, 0.0, 0.0
    accuracy = successes / trials
    np.random.seed(42)
    samples = np.random.binomial(trials, accuracy, size=n_iterations) / trials
    alpha = 1 - confidence
    lower = np.percentile(samples, alpha / 2 * 100)
    upper = np.percentile(samples, (1 - alpha / 2) * 100)
    return round(lower, 4), round(upper, 4), round(accuracy, 4)


def wilson_ci(successes: int, trials: int, z: float = 1.96):
    """Wilson score interval for a proportion."""
    if trials == 0:
        return 0.0, 0.0, 0.0
    p = successes / trials
    denom = 1 + z**2 / trials
    center = (p + z**2 / (2 * trials)) / denom
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * trials)) / trials) / denom
    return round(center - margin, 4), round(center + margin, 4), round(p, 4)


def cohens_kappa(cm):
    """Calculate Cohen's kappa from a 2x2 confusion matrix dict."""
    tp, tn, fp, fn = cm["tp"], cm["tn"], cm["fp"], cm["fn"]
    n = tp + tn + fp + fn
    po = (tp + tn) / n
    pe = ((tp + fp) * (tp + fn) + (tn + fn) * (tn + fp)) / (n * n)
    if pe == 1:
        return 1.0
    return round((po - pe) / (1 - pe), 4)


def main():
    with open(GS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    rules = data if isinstance(data, list) else data.get("rules", data.get("entries", []))

    # --- 1. Rule Detection Agreement ---
    detection_agree = 0
    detection_total = 0
    tp, tn, fp, fn = 0, 0, 0, 0
    
    for entry in rules:
        detection_total += 1
        h_is_rule = entry.get("human_annotation", {}).get("is_rule", False)
        l_is_rule = entry.get("llm_annotation", {}).get("is_rule", False)
        
        if h_is_rule == l_is_rule:
            detection_agree += 1
            if h_is_rule:
                tp += 1
            else:
                tn += 1
        else:
            if l_is_rule:
                fp += 1
            else:
                fn += 1

    # --- 2. Type Classification Agreement (among rules both agreed are rules) ---
    type_agree = 0
    type_total = 0
    type_breakdown = {"obligation": {"agree": 0, "disagree": 0},
                      "permission": {"agree": 0, "disagree": 0},
                      "prohibition": {"agree": 0, "disagree": 0}}

    for entry in rules:
        h = entry.get("human_annotation", {})
        l = entry.get("llm_annotation", {})
        if not (h.get("is_rule") and l.get("is_rule")):
            continue
        type_total += 1
        h_type = (h.get("rule_type") or "").lower()
        l_type = (l.get("rule_type") or "").lower()
        if h_type == l_type:
            type_agree += 1
            if h_type in type_breakdown:
                type_breakdown[h_type]["agree"] += 1
        else:
            for t in [h_type, l_type]:
                if t in type_breakdown:
                    type_breakdown[t]["disagree"] += 1

    # --- 3. Compute all metrics ---
    cm = {"tp": tp, "tn": tn, "fp": fp, "fn": fn}
    kappa = cohens_kappa(cm)
    
    det_boot_lo, det_boot_hi, det_acc = bootstrap_ci(detection_agree, detection_total)
    det_wil_lo, det_wil_hi, _ = wilson_ci(detection_agree, detection_total)
    
    type_boot_lo, type_boot_hi, type_acc = bootstrap_ci(type_agree, type_total)
    type_wil_lo, type_wil_hi, _ = wilson_ci(type_agree, type_total)

    # --- 4. Print report ---
    print("=" * 65)
    print("  BOOTSTRAP CI RECALCULATION — Corrected Gold Standard v4")
    print("=" * 65)
    
    print(f"\n{'─' * 65}")
    print("  1. RULE DETECTION (is_rule binary classification)")
    print(f"{'─' * 65}")
    print(f"  Total entries:       {detection_total}")
    print(f"  Agreements:          {detection_agree}")
    print(f"  Confusion Matrix:    TP={tp}, TN={tn}, FP={fp}, FN={fn}")
    print(f"  Accuracy:            {det_acc:.2%}")
    print(f"  Bootstrap 95% CI:    [{det_boot_lo:.4f}, {det_boot_hi:.4f}]")
    print(f"  Wilson 95% CI:       [{det_wil_lo:.4f}, {det_wil_hi:.4f}]")
    print(f"  Cohen's kappa:       {kappa}")
    
    if kappa >= 0.81:
        interp = "Almost Perfect"
    elif kappa >= 0.61:
        interp = "Substantial"
    elif kappa >= 0.41:
        interp = "Moderate"
    else:
        interp = "Fair or below"
    print(f"  Kappa interpret.:    {interp}")
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    print(f"  Precision:           {precision:.4f}")
    print(f"  Recall:              {recall:.4f}")
    print(f"  F1-Score:            {f1:.4f}")
    
    f1_boot_lo, f1_boot_hi, _ = bootstrap_ci(int(f1 * detection_total), detection_total)
    print(f"  F1 Bootstrap 95% CI: [{f1_boot_lo:.4f}, {f1_boot_hi:.4f}]")
    
    print(f"\n{'─' * 65}")
    print("  2. TYPE CLASSIFICATION (among detected rules)")
    print(f"{'─' * 65}")
    print(f"  Total typed rules:   {type_total}")
    print(f"  Type agreements:     {type_agree}")
    print(f"  Type accuracy:       {type_acc:.2%}")
    print(f"  Bootstrap 95% CI:    [{type_boot_lo:.4f}, {type_boot_hi:.4f}]")
    print(f"  Wilson 95% CI:       [{type_wil_lo:.4f}, {type_wil_hi:.4f}]")
    
    print(f"\n  By deontic type:")
    for dtype, counts in type_breakdown.items():
        total_t = counts["agree"] + counts["disagree"]
        acc_t = counts["agree"] / total_t if total_t > 0 else 0
        print(f"    {dtype:12s}  agree={counts['agree']:2d}  disagree={counts['disagree']:2d}  acc={acc_t:.1%}")
    
    print(f"\n{'─' * 65}")
    print("  3. COMPARISON: ORIGINAL vs CORRECTED")
    print(f"{'─' * 65}")
    
    # Check for original agreement field
    orig_agree = sum(1 for e in rules if e.get("human_llm_agreement_original", e.get("human_llm_agreement")) == True)
    new_agree = sum(1 for e in rules if e.get("human_llm_agreement") == True)
    
    print(f"  Original overall agreement: {orig_agree}/{detection_total} ({orig_agree/detection_total:.2%})")
    print(f"  Corrected overall agreement: {new_agree}/{detection_total} ({new_agree/detection_total:.2%})")
    print(f"  Entries corrected:  {orig_agree - new_agree}")
    
    print(f"\n{'=' * 65}")
    print("  ✓ All metrics recalculated from corrected gold_standard_annotated_v4.json")
    print(f"{'=' * 65}")

    # Save results
    results = {
        "source": "gold_standard_annotated_v4.json (corrected)",
        "rule_detection": {
            "n": detection_total,
            "accuracy": det_acc,
            "bootstrap_ci_95": [det_boot_lo, det_boot_hi],
            "wilson_ci_95": [det_wil_lo, det_wil_hi],
            "confusion_matrix": cm,
            "cohens_kappa": kappa,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        },
        "type_classification": {
            "n": type_total,
            "accuracy": type_acc,
            "bootstrap_ci_95": [type_boot_lo, type_boot_hi],
            "wilson_ci_95": [type_wil_lo, type_wil_hi],
            "by_type": type_breakdown,
        },
    }
    
    out_file = RESEARCH_DIR / "corrected_bootstrap_ci.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved to: {out_file}")


if __name__ == "__main__":
    main()
