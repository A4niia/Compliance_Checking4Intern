#!/usr/bin/env python3
"""
Compare Multiple Reproducibility Test Runs
Tracks improvement and provides data insights across experiments
"""

import json
from pathlib import Path
from collections import Counter
from datetime import datetime

RESULTS_DIR = Path("research/reproducibility_results")


def load_test_result(json_file: Path):
    """Load a single test result JSON."""
    with open(json_file) as f:
        return json.load(f)


def compare_tests(test_files: list):
    """Compare multiple test runs and provide insights."""
    
    print("=" * 80)
    print(" " * 15 + "REPRODUCIBILITY TEST COMPARISON")
    print("=" * 80)
    
    tests = []
    for file_path in test_files:
        data = load_test_result(file_path)
        tests.append({
            'file': file_path.name,
            'date': data['test_info']['start_time'][:10],
            'total_runs': data['test_info']['total_runs'],
            'analysis': data['analysis'],
            'runs': data['runs']
        })
    
    # Sort by date
    tests.sort(key=lambda x: x['date'])
    
    print(f"\n📊 COMPARING {len(tests)} TEST RUNS\n")
    
    # Comparison Table
    print("TEST OVERVIEW:")
    print("-" * 80)
    print(f"{'Date':<12} {'Runs':<6} {'Unique':<8} {'Best %':<10} {'Avg Time':<12} {'File':<25}")
    print("-" * 80)
    
    for i, test in enumerate(tests, 1):
        unique = test['analysis']['unique_outputs']
        total = test['total_runs']
        best_pct = ((total - unique + 1) / total * 100)
        avg_time = test['analysis']['total_time_mean']
        
        print(f"{test['date']:<12} {total:<6} {unique:<8} {best_pct:>6.1f}%    {avg_time:>7.1f}s     {test['file']:<25}")
    
    print("\n")
    
    # Detailed Comparison
    print("REPRODUCIBILITY TREND:")
    print("-" * 80)
    
    for i, test in enumerate(tests, 1):
        hash_counts = Counter([r['final_shacl_hash'] for r in test['runs']])
        dominant = hash_counts.most_common(1)[0]
        
        print(f"\nTest {i} ({test['date']}):")
        print(f"  Unique outputs: {test['analysis']['unique_outputs']}")
        print(f"  Dominant pattern: {dominant[1]}/{test['total_runs']} runs ({dominant[1]/test['total_runs']*100:.0f}%)")
        print(f"  Hash distribution:")
        for hash_val, count in hash_counts.most_common(3):
            bar = "█" * int(count / test['total_runs'] * 40)
            print(f"    {hash_val[:16]}: {count:2d} {bar}")
    
    # Classification Variance Comparison
    print("\n\nCLASSIFICATION VARIANCE:")
    print("-" * 80)
    
    for i, test in enumerate(tests, 1):
        class_hashes = [r['phases']['classification']['output_hash'] for r in test['runs']]
        unique_class = len(set(class_hashes))
        
        # Get deontic type ranges
        oblig = [r['phases']['classification']['obligations'] for r in test['runs']]
        perm = [r['phases']['classification']['permissions'] for r in test['runs']]
        prohib = [r['phases']['classification']['prohibitions'] for r in test['runs']]
        
        print(f"\nTest {i} ({test['date']}):")
        print(f"  Unique classification outputs: {unique_class}/{test['total_runs']}")
        print(f"  Obligations range: {min(oblig)}-{max(oblig)} (±{max(oblig)-min(oblig)})")
        print(f"  Permissions range: {min(perm)}-{max(perm)} (±{max(perm)-min(perm)})")
        print(f"  Prohibitions range: {min(prohib)}-{max(prohib)} (±{max(prohib)-min(prohib)})")
    
    # Timing Comparison
    print("\n\nTIMING COMPARISON:")
    print("-" * 80)
    
    for i, test in enumerate(tests, 1):
        phases = test['analysis']['phase_statistics']
        print(f"\nTest {i} ({test['date']}):")
        print(f"  Classification: {phases['classification']['mean']:.1f}s (±{phases['classification']['max']-phases['classification']['min']:.1f}s)")
        print(f"  FOL Generation: {phases['fol_generation']['mean']:.1f}s (±{phases['fol_generation']['max']-phases['fol_generation']['min']:.1f}s)")
        print(f"  Total avg: {test['analysis']['total_time_mean']:.1f}s")
    
    # Improvement Analysis
    if len(tests) > 1:
        print("\n\nIMPROVEMENT ANALYSIS:")
        print("-" * 80)
        
        first = tests[0]
        latest = tests[-1]
        
        first_repro = (first['total_runs'] - first['analysis']['unique_outputs'] + 1) / first['total_runs'] * 100
        latest_repro = (latest['total_runs'] - latest['analysis']['unique_outputs'] + 1) / latest['total_runs'] * 100
        
        print(f"\nFrom {first['date']} to {latest['date']}:")
        print(f"  Reproducibility: {first_repro:.1f}% → {latest_repro:.1f}% ({latest_repro-first_repro:+.1f}%)")
        print(f"  Avg time: {first['analysis']['total_time_mean']:.1f}s → {latest['analysis']['total_time_mean']:.1f}s ({latest['analysis']['total_time_mean']-first['analysis']['total_time_mean']:+.1f}s)")
        print(f"  Unique outputs: {first['analysis']['unique_outputs']} → {latest['analysis']['unique_outputs']}")
        
        if latest_repro > first_repro:
            print("\n  ✅ Reproducibility IMPROVED")
        elif latest_repro < first_repro:
            print("\n  ⚠️  Reproducibility DECREASED")
        else:
            print("\n  ➡️  Reproducibility UNCHANGED")
    
    print("\n" + "=" * 80)


def generate_insights(test_files: list):
    """Generate insights for thesis writing."""
    
    tests = [load_test_result(f) for f in test_files]
    
    insights = {
        'total_tests': len(tests),
        'total_llm_inferences': sum(t['test_info']['total_runs'] * 97 * 2 for t in tests),
        'reproducibility_range': [],
        'variance_patterns': []
    }
    
    for test in tests:
        unique = test['analysis']['unique_outputs']
        total = test['test_info']['total_runs']
        repro = (total - unique + 1) / total * 100
        insights['reproducibility_range'].append(repro)
    
    print(f"\n📈 THESIS INSIGHTS")
    print("=" * 80)
    print(f"Total experiments: {insights['total_tests']}")
    print(f"Total LLM inferences: {insights['total_llm_inferences']:,}")
    print(f"Reproducibility range: {min(insights['reproducibility_range']):.1f}% - {max(insights['reproducibility_range']):.1f}%")
    print(f"Average reproducibility: {sum(insights['reproducibility_range'])/len(insights['reproducibility_range']):.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    # Find all test result JSONs
    result_files = sorted(RESULTS_DIR.glob("reproducibility_report_*.json"))
    
    if len(result_files) == 0:
        print("No test result files found in", RESULTS_DIR)
        sys.exit(1)
    
    print(f"Found {len(result_files)} test result(s)\n")
    
    if len(result_files) == 1:
        print("Only one test found. Run more tests to compare!")
        print(f"\nTo run another test:")
        print(f"  python scripts/reproducibility_test.py --runs 20")
    else:
        compare_tests(result_files)
        print("\n")
        generate_insights(result_files)
