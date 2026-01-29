# LLM Model Comparison for Policy Rule Verification

**Generated:** 2026-01-29T16:50:21.660613

## Overview

This report compares three Large Language Models (LLMs) for their ability to identify policy rules in academic documents. This comparison supports the methodology of the thesis by providing empirical justification for model selection.

## Models Tested

| Model | Type | Size | Purpose |
|-------|------|------|---------|
| Llama 3.2 | Open Source (Meta) | 3B | Baseline, efficient classification |
| Mistral | Open Source | 7B | Instruction-following, extraction |
| Phi3 | Open Source (Microsoft) | 3.8B | Compact reasoning |

## Results Summary

### Classification Statistics

| Model | Rules Found | Not Rules | Errors | Rule Rate | Avg Confidence |
|-------|-------------|-----------|--------|-----------|----------------|
| llama3.2 | 4 | 0 | 1 | 80.0% | 0.74 |
| phi3 | 4 | 0 | 1 | 80.0% | 0.76 |
| mistral | 5 | 0 | 0 | 100.0% | 0.98 |
| mixtral | 5 | 0 | 0 | 100.0% | 0.93 |
| llama3.1:70b | 5 | 0 | 0 | 100.0% | 0.88 |

### Inter-Model Agreement

| Model Pair | Agreement Rate |
|------------|----------------|
| llama3.2 vs phi3 | 80.0% |
| llama3.2 vs mistral | 80.0% |
| llama3.2 vs mixtral | 80.0% |
| llama3.2 vs llama3.1:70b | 80.0% |
| phi3 vs mistral | 80.0% |
| phi3 vs mixtral | 80.0% |
| phi3 vs llama3.1:70b | 80.0% |
| mistral vs mixtral | 100.0% |
| mistral vs llama3.1:70b | 100.0% |
| mixtral vs llama3.1:70b | 100.0% |

## Sample Comparisons

The following table shows how models classified the same rule text:

| Rule ID | Llama 3.2 | Mistral | Phi3 |
|---------|-----------|---------|------|
| GS-001 | ✅ | ✅ | ✅ |
| GS-002 | ❌ | ✅ | ❌ |
| GS-003 | ✅ | ✅ | ✅ |
| GS-004 | ✅ | ✅ | ✅ |
| GS-005 | ✅ | ✅ | ✅ |

## Methodology Notes

1. **Prompt Design**: All models used identical prompts for fair comparison
2. **Temperature**: Set to 0.1 for consistent, deterministic outputs
3. **Evaluation**: Binary classification (is_rule: true/false)

## Recommendations for Thesis

Based on the comparison results:

1. **Primary Model**: [To be determined based on results]
2. **Validation**: Cross-validate with model showing highest agreement
3. **Documentation**: Report inter-model agreement as measure of reliability

## References

- Meta AI. (2024). Llama 3.2 Technical Report.
- Mistral AI. (2023). Mistral 7B.
- Microsoft Research. (2024). Phi-3 Technical Report.
