#!/usr/bin/env python3
"""
Cross-Institutional Comparison Script
=======================================
Compares pipeline results across AIT, CU, and TU.

Usage:
    python scripts/compare_institutions.py
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"

SOURCES = {
    "ait": "Asian Institute of Technology",
    "cu":  "Chulalongkorn University",
    "tu":  "Thammasat University",
}


def load_report(source: str) -> dict:
    """Load pipeline report for a given source."""
    report_file = RESEARCH_DIR / source / "pipeline_report.json"
    if not report_file.exists():
        return None
    with open(report_file, encoding="utf-8") as f:
        return json.load(f)


def compare():
    """Generate cross-institutional comparison."""
    print("=" * 70)
    print("  CROSS-INSTITUTIONAL COMPARISON")
    print("=" * 70)

    reports = {}
    for src, name in SOURCES.items():
        report = load_report(src)
        if report:
            reports[src] = report
            print(f"  ✅ Loaded {name}")
        else:
            print(f"  ⚠️  No data for {name}")

    if len(reports) < 2:
        print("\n  ❌ Need at least 2 institutional reports to compare.")
        return

    # Build comparison
    comparison = {
        "comparison_date": datetime.now().isoformat(),
        "institutions": len(reports),
        "data": {},
    }

    # Print comparison table
    print(f"\n  {'─'*65}")
    header = f"  {'Metric':<30}"
    for src in reports:
        header += f"  {SOURCES[src][:15]:>15}"
    print(header)
    print(f"  {'─'*65}")

    metrics = []

    # Documents
    row = {"metric": "Documents"}
    line = f"  {'Documents':<30}"
    for src, r in reports.items():
        val = r.get("extraction", {}).get("documents", "-")
        line += f"  {str(val):>15}"
        row[src] = val
    print(line)
    metrics.append(row)

    # Total sentences
    row = {"metric": "Total Sentences"}
    line = f"  {'Total Sentences':<30}"
    for src, r in reports.items():
        val = r.get("extraction", {}).get("total_sentences", "-")
        line += f"  {str(val):>15}"
        row[src] = val
    print(line)
    metrics.append(row)

    # Candidates (after prefilter)
    row = {"metric": "Candidates (post-filter)"}
    line = f"  {'Candidates (post-filter)':<30}"
    for src, r in reports.items():
        val = r.get("classification", {}).get("candidates", "-")
        line += f"  {str(val):>15}"
        row[src] = val
    print(line)
    metrics.append(row)

    # Rules detected
    row = {"metric": "Rules Detected"}
    line = f"  {'Rules Detected':<30}"
    for src, r in reports.items():
        val = r.get("classification", {}).get("rules_detected", "-")
        line += f"  {str(val):>15}"
        row[src] = val
    print(line)
    metrics.append(row)

    # Detection rate
    row = {"metric": "Detection Rate"}
    line = f"  {'Detection Rate':<30}"
    for src, r in reports.items():
        val = r.get("classification", {}).get("detection_rate", "-")
        line += f"  {str(val):>15}"
        row[src] = val
    print(line)
    metrics.append(row)

    # Rule density (rules per document)
    row = {"metric": "Rules / Document"}
    line = f"  {'Rules / Document':<30}"
    for src, r in reports.items():
        docs = r.get("extraction", {}).get("documents", 1)
        rules = r.get("classification", {}).get("rules_detected", 0)
        val = f"{rules/max(docs,1):.1f}"
        line += f"  {val:>15}"
        row[src] = val
    print(line)
    metrics.append(row)

    # Sentence density (sentences per document)
    row = {"metric": "Sentences / Document"}
    line = f"  {'Sentences / Document':<30}"
    for src, r in reports.items():
        docs = r.get("extraction", {}).get("documents", 1)
        sents = r.get("extraction", {}).get("total_sentences", 0)
        val = f"{sents/max(docs,1):.1f}"
        line += f"  {val:>15}"
        row[src] = val
    print(line)
    metrics.append(row)

    print(f"  {'─'*65}")

    # Deontic distribution
    print(f"\n  Deontic Distribution:")
    print(f"  {'─'*65}")
    for dtype in ["obligation", "permission", "prohibition"]:
        row = {"metric": f"  {dtype.title()}"}
        line = f"  {dtype.title():<30}"
        for src, r in reports.items():
            dist = r.get("classification", {}).get("deontic_distribution", {})
            val = dist.get(dtype, 0)
            rules = r.get("classification", {}).get("rules_detected", 1)
            pct = f"{val} ({val/max(rules,1)*100:.0f}%)"
            line += f"  {pct:>15}"
            row[src] = pct
        print(line)
        metrics.append(row)
    print(f"  {'─'*65}")

    # FOL success
    print(f"\n  FOL Formalization:")
    print(f"  {'─'*65}")
    row = {"metric": "FOL Success Rate"}
    line = f"  {'FOL Success Rate':<30}"
    for src, r in reports.items():
        val = r.get("fol", {}).get("success_rate", "-")
        line += f"  {str(val):>15}"
        row[src] = val
    print(line)
    metrics.append(row)
    print(f"  {'─'*65}")

    # SHACL
    print(f"\n  SHACL Output:")
    print(f"  {'─'*65}")
    for smetric in ["total_shapes", "estimated_triples"]:
        row = {"metric": smetric.replace("_", " ").title()}
        line = f"  {smetric.replace('_', ' ').title():<30}"
        for src, r in reports.items():
            val = r.get("shacl", {}).get(smetric, "-")
            line += f"  {str(val):>15}"
            row[src] = val
        print(line)
        metrics.append(row)
    print(f"  {'─'*65}")

    # Imbalance analysis (by candidate sentences)
    print(f"\n  📊 Imbalance Analysis (by candidate sentences):")
    candidates = {src: r.get("classification", {}).get("candidates", 0)
                  for src, r in reports.items()}
    max_cand = max(candidates.values()) if candidates else 1
    for src, count in candidates.items():
        ratio = count / max_cand if max_cand > 0 else 0
        bar = "█" * int(ratio * 30)
        print(f"    {SOURCES[src][:20]:<20} {count:>5} {bar}")

    # Save comparison
    comparison["metrics"] = metrics
    comparison["reports"] = {src: r for src, r in reports.items()}

    out_dir = RESEARCH_DIR / "comparison"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "cross_institutional_comparison.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    print(f"\n  💾 Saved: {out_file.relative_to(PROJECT_ROOT)}")

    # Generate markdown table for thesis
    md_file = out_dir / "comparison_table.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# Cross-Institutional Comparison\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        # Main table
        cols = list(reports.keys())
        f.write(f"| Metric | {' | '.join(SOURCES[c] for c in cols)} |\n")
        f.write(f"|---|{'---|' * len(cols)}\n")
        for m in metrics:
            row = f"| {m['metric']} |"
            for c in cols:
                row += f" {m.get(c, '-')} |"
            f.write(row + "\n")

    print(f"  💾 Saved: {md_file.relative_to(PROJECT_ROOT)}")
    print(f"\n{'='*70}")
    print(f"  ✅ Comparison complete")
    print(f"{'='*70}")


if __name__ == "__main__":
    compare()
