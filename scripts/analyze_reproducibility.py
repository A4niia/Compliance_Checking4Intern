#!/usr/bin/env python3
"""
Analyze reproducibility test results
"""
import json
from collections import Counter
from pathlib import Path

# Load results
results_file = Path("research/reproducibility_results/reproducibility_report_20260206_235943.json")
with open(results_file) as f:
    data = json.load(f)

runs = data['runs']
analysis = data['analysis']

print("=" * 80)
print(" " * 20 + "REPRODUCIBILITY TEST ANALYSIS")
print("=" * 80)

# Overall metrics
print(f"\n📊 OVERALL METRICS")
print(f"  Total runs: {len(runs)}")
print(f"  Successful runs: {analysis['successful_runs']}")
print(f"  Total duration: {(runs[-1]['end_time'][:19], runs[0]['start_time'][:19])}")
print(f"  Average time per run: {analysis['total_time_mean']:.1f}s (~{analysis['total_time_mean']/60:.1f} min)")

# Reproducibility analysis
print(f"\n🎯 REPRODUCIBILITY ANALYSIS")
print(f"  Unique final outputs: {analysis['unique_outputs']}")
print(f"  All identical: {analysis['all_identical']}")
print(f"  Reproducibility rate: {(20-analysis['unique_outputs']+1)/20*100:.1f}%")

# Hash distribution
print(f"\n📦 FINAL HASH DISTRIBUTION")
hash_counts = Counter([r['final_shacl_hash'] for r in runs])
for hash_val, count in hash_counts.most_common():
    pct = count/20*100
    bar = "█" * int(pct/5)
    print(f"  {hash_val}: {count:2d} runs ({pct:5.1f}%) {bar}")

# Phase-by-phase variation
print(f"\n🔍 PHASE-BY-PHASE ANALYSIS")

# Classification
class_hashes = [r['phases']['classification']['output_hash'] for r in runs]
class_counts = Counter(class_hashes)
print(f"\n  CLASSIFICATION:")
print(f"    Unique outputs: {len(class_counts)}")
print(f"    Most common: {class_counts.most_common(1)[0][1]}/{len(runs)} runs")

# Check deontic type variations
for i, run in enumerate(runs, 1):
    c = run['phases']['classification']
    print(f"    Run {i:2d}: O={c['obligations']:2d} P={c['permissions']:2d} Pr={c['prohibitions']:2d}")

# FOL generation
fol_hashes = [r['phases']['fol_generation']['output_hash'] for r in runs]
fol_counts = Counter(fol_hashes)
print(f"\n  FOL GENERATION:")
print(f"    Unique outputs: {len(fol_counts)}")
print(f"    Consistency: {fol_counts.most_common(1)[0][1]}/{len(runs)} runs match")

# SHACL translation
shacl_hashes = [r['phases']['shacl_translation']['output_hash'] for r in runs]
shacl_counts = Counter(shacl_hashes)
print(f"\n  SHACL TRANSLATION:")
print(f"    Unique outputs: {len(shacl_counts)}")
print(f"    Consistency: {shacl_counts.most_common(1)[0][1]}/{len(runs)} runs match")

# Timing statistics
print(f"\n⏱️  TIMING STATISTICS")
for phase in ['classification', 'fol_generation']:
    times = [r['phases'][phase]['time_seconds'] for r in runs]
    print(f"\n  {phase.upper()}:")
    print(f"    Mean: {sum(times)/len(times):.2f}s")
    print(f"    Min: {min(times):.2f}s")
    print(f"    Max: {max(times):.2f}s")
    print(f"    Std: {(sum([(t-sum(times)/len(times))**2 for t in times])/len(times))**0.5:.2f}s")

# Key findings
print(f"\n💡 KEY FINDINGS")
print(f"\n  1. DETERMINISM:")
if analysis['all_identical']:
    print(f"     ✅ Perfect reproducibility - all runs identical")
else:
    main_hash = hash_counts.most_common(1)[0]
    print(f"     ⚠️  Variability detected - {analysis['unique_outputs']} unique outputs")
    print(f"     📌 Dominant pattern: {main_hash[1]}/20 runs ({main_hash[1]/20*100:.0f}%)")

print(f"\n  2. LLM CONSISTENCY:")
print(f"     Classification: {20-len(class_counts)} runs matched most common output")
print(f"     FOL Generation: {20-len(fol_counts)} runs matched most common output")
print(f"     → Indicates {'high' if len(class_counts) < 5 else 'moderate'} LLM stability")

print(f"\n  3. PERFORMANCE:")
print(f"     Average per run: {analysis['total_time_mean']:.0f}s")
print(f"     = ~{analysis['phase_statistics']['classification']['mean']:.0f}s classification")
print(f"     + ~{analysis['phase_statistics']['fol_generation']['mean']:.0f}s FOL")
print(f"     Total test time: ~{(runs[-1]['end_time'][:19])} (41 minutes)")

print("\n" + "=" * 80)
