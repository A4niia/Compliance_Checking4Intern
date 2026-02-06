# Reproducibility Test Analysis Report

**Test Run:** 2026-02-06 23:18-23:59  
**Duration:** 41 minutes  
**Total Runs:** 20  
**LLM Used:** Mistral (actual, not mock)

---

## Executive Summary

The reproducibility test reveals **moderate variability** in LLM outputs across 20 consecutive runs processing the same 97 policy rules.

### Key Metrics

| Metric | Value |
|--------|-------|
| **Total Runs** | 20 |
| **Successful Runs** | 20 (100%) |
| **Unique Final Outputs** | 6 different SHACL graphs |
| **Dominant Pattern** | 14/20 runs (70%) |
| **Reproducibility Rate** | ~70% |
| **Avg Time per Run** | 123 seconds (~2 min) |

---

## Reproducibility Analysis

### Final SHACL Hash Distribution

| Hash | Runs | Percentage | Visualization |
|------|------|------------|---------------|
| `978e8a6fdfb95776` | 14 | 70% | ████████████████████ (Dominant) |
| `46e7b1919cad752b` | 2 | 10% | ████ |
| `d3c5fd90f862695f` | 1 | 5% | ██ |
| `3306a46277d5a433` | 1 | 5% | ██ |
| `d3e49546ba792244` | 1 | 5% | ██ |
| `e4ccd70c56c5f929` | 1 | 5% | ██ |

**Finding:** One dominant pattern emerges in 70% of runs, suggesting the LLM has a "preferred" interpretation but shows variability in edge cases.

---

## Phase-by-Phase Analysis

### 1. Extraction Phase

- **Consistency:** 100% (hash: `680edbc1428ec5b8`)
- **Items extracted:** 97 rules (always consistent)
- **Conclusion:** ✅ Deterministic - no LLM involved

### 2. Classification Phase

- **Unique outputs:** 20 (100% variation!)
- **Deontic type distribution variation:**

| Run | Obligations | Permissions | Prohibitions |
|-----|------------|-------------|--------------|
| 1 | 59 | 7 | 9 |
| 2 | 59 | 9 | 8 |
| 3 | 59 | 9 | 8 |
| 4 | 59 | 8 | 10 |
| 5 | 60 | 10 | 7 |
| 6 | 60 | 9 | 8 |
| 7 | 60 | 9 | 8 |
| 8 | 58 | 9 | 9 |
| 9 | 61 | 9 | 7 |
| 10 | 60 | 8 | 8 |
| 11 | 61 | 8 | 8 |
| 12 | 59 | 8 | 9 |
| 13 | 60 | 8 | 9 |
| 14 | 60 | 8 | 9 |
| 15 | 61 | 8 | 9 |
| 16 | 61 | 8 | 8 |
| 17 | 61 | 7 | 8 |
| 18 | 60 | 8 | 8 |
| 19 | 60 | 10 | 8 |
| 20 | 60 | 9 | 8 |

**Observations:**

- Obligations: Range from 58-61 (±3 from median)
- Permissions: Range from 7-10 (±1.5 from median)
- Prohibitions: Range from 7-10 (±1.5 from median)

**Finding:** ⚠️ **Every single run produced different classifications!** This indicates **high LLM variability** in determining rule types (obligation vs permission vs prohibition).

### 3. FOL Generation Phase

- **Unique outputs:** 20 (100% variation!)
- **Formulas generated:** 97 (consistent count)
- **Avg time:** 77.29s (range: 75.0s - 79.21s)

**Finding:** ⚠️ **Every run produced different FOL formulas**, likely due to:

1. Variable classification from previous step
2. LLM variability in formula generation
3. Temperature = 0.1 is not deterministic enough

### 4. SHACL Translation Phase

- **Unique outputs:** 20 (100% variation at intermediate level)
- **Triples generated:** 590 (always consistent)
- **Process time:** <0.01s (deterministic logic)

**Finding:** Translation is deterministic, but input variability propagates through.

### 5. Validation Phase

- **Consistency:** 100% (hash: `492cb860b19c2699`)
- **All runs passed:** Yes
- **Conclusion:** ✅ Validation logic is deterministic

---

## Timing Performance

| Phase | Mean | Min | Max | Std Dev |
|-------|------|-----|-----|---------|
| **Classification** | 45.83s | 45.16s | 49.43s | ±1.07s |
| **FOL Generation** | 77.29s | 75.00s | 79.21s | ±1.14s |
| **SHACL Translation** | <0.01s | - | - | - |
| **Total per Run** | 123.1s | 120.2s | 128.6s | ±2.1s |

**Total Test Duration:** 41 minutes 2 seconds

---

## Critical Findings

### 1. LLM Non-Determinism is the Primary Source of Variability

**Evidence:**

- Classification: 20 unique outputs (100% variation)
- FOL Generation: 20 unique outputs (100% variation)
- Extraction & Validation: 1 unique output each (100% determinism)

**Root Cause:** Even with `temperature=0.1`, Mistral LLM produces different results across runs. This is expected behavior for most LLMs.

### 2. Classification Instability

**Problematic Rules:**  
The variation in deontic type counts (O: 58-61, P: 7-10, Pr: 7-10) suggests:

- **~3-4 rules** are "borderline" and classified inconsistently
- These likely contain ambiguous deontic markers (e.g., "should", "may")
- The LLM struggles with context-dependent interpretations

**Impact:** Classification errors propagate through the entire pipeline:

```
Wrong Classification → Wrong FOL Formula → Wrong SHACL Shape
```

### 3. Cascade Effect

The variability compounds:

1. **Step 1 (Classification):** 20 different outputs
2. **Step 2 (FOL):** 20 different outputs (affected by Step 1 + own variability)
3. **Step 3 (SHACL):** Only 6 unique final outputs

**Why only 6 final outputs?**  
Different FOL formulas can lead to **semantically equivalent** SHACL shapes. For example:

- `O(submit(x, deadline))` and `Obligation(submit(x, deadline))` → same SHACL constraint
- Minor wording differences → same structure

### 4. Dominant Pattern Analysis

The most common output (`978e8a6fdfb95776`) appeared in runs:
1, 3, 4, 6, 7, 9, 10, 11, 13, 14, 15, 17, 19, 20

**Hypothesis:** This represents the LLM's "most confident" interpretation of ambiguous rules.

---

## Recommendations for Thesis

### 1. Document the Variability

**For the thesis, report:**

- "With `temperature=0.1`, Mistral achieved 70% consistency across 20 runs"
- "Classification phase showed 100% variability, with ±3 rules classified differently per run"
- "Final SHACL output converged to 6 distinct patterns, with one dominant (70%)"

### 2. Identify Problematic Rules

Analyze which specific rules caused classification disagreements:

1. Compare runs to find rules with varying classifications
2. Examine these rules for ambiguous language
3. Document as "limitations" or "edge cases"

### 3. Consider Majority Voting

For production use, run classification 3-5 times and use majority vote:

```python
classifications = [classify_rule(text) for _ in range(5)]
final = most_common(classifications)
```

### 4. Semantic Equivalence Testing

The fact that 20 different FOL outputs → 6 SHACL outputs suggests semantic equivalence. Consider:

- Manual review of the 6 unique outputs
- Verify if they are truly different or just syntactically varied

---

## Conclusion

### What Went Well ✅

- All 20 runs completed successfully
- Extraction and validation phases are 100% deterministic
- Performance is consistent (~123s ± 2s)
- One dominant pattern emerged (70% of runs)

### What Needs Attention ⚠️

- Classification is unstable (every run different)
- FOL generation inherits and amplifies variability
- ~3-4 rules are borderline cases causing inconsistency

### Thesis Implications 📝

This result is actually **valuable for the thesis** because it:

1. Demonstrates rigorous testing methodology
2. Identifies specific limitations of LLM-based approaches
3. Quantifies reproducibility (70% for final output)
4. Provides data for discussing trade-offs between automation and consistency

**Recommendation:** Frame this as a "finding" rather than a "failure" - you discovered and quantified the inherent variability in LLM-based policy formalization, which is important research output.
