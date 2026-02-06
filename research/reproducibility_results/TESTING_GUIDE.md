# Reproducibility Testing Guide

## Running Tests

### Single Test Run (Quick - 5 mins with mock)

```bash
python scripts/reproducibility_test.py --runs 5 --mock
```

### Full Test Run (Real LLM - ~40 mins)

```bash
python scripts/reproducibility_test.py --runs 20
```

### Options

- `--runs N`: Number of runs (default: 5)
- `--mock`: Use mock LLM instead of real API calls

## Analyzing Results

### Single Test Analysis

```bash
python scripts/analyze_reproducibility.py
```

Shows detailed analysis of the most recent test run.

### Compare Multiple Tests

```bash
python scripts/compare_reproducibility_tests.py
```

Compares all test runs to track improvements over time.

## Collecting Experimental Data

### Test Scenarios to Track

1. **Baseline Test** (already done)
   - 20 runs with temperature=0.1
   - Results: 70% reproducibility

2. **Temperature Variation**

   ```bash
   # Edit populate_llm_annotations_v2.py: temperature = 0.0
   python scripts/reproducibility_test.py --runs 20
   
   # Edit populate_llm_annotations_v2.py: temperature = 0.3
   python scripts/reproducibility_test.py --runs 20
   ```

3. **Different Models**

   ```bash
   # Edit both scripts to use different model
   # MODEL = "llama2" or "codellama" or "gpt-4"
   python scripts/reproducibility_test.py --runs 20
   ```

4. **Prompt Engineering**
   - Modify classification prompt
   - Test with more explicit instructions
   - Run 20 more times

### Data Collection Template

Each test should record:

- **Test ID**: `YYYYMMDD_HHMMSS`
- **Configuration**: Model, temperature, prompt version
- **Results**: JSON file in `research/reproducibility_results/`
- **Analysis**: Markdown file with insights
- **Changes Made**: What was different from baseline

### Tracking Improvements

Create a log file: `research/reproducibility_results/experiment_log.md`

```markdown
# Experiment Log

## Test 1: Baseline (2026-02-06)
- **Config**: Mistral, temp=0.1, default prompts
- **Results**: 70% reproducibility, 6 unique outputs
- **Issues**: Classification varies 100%

## Test 2: Lower Temperature (2026-02-07)
- **Config**: Mistral, temp=0.0, default prompts
- **Hypothesis**: Lower temp should increase consistency
- **Results**: [To be filled]
- **Improvement**: [Calculate change]

## Test 3: Improved Prompts (2026-02-08)
- **Config**: Mistral, temp=0.1, enhanced classification prompt
- **Changes**: Added examples of obligations/permissions/prohibitions
- **Results**: [To be filled]
- **Improvement**: [Calculate change]
```

## Output Files

Each test run creates:

### 1. Raw Data

- `reproducibility_report_YYYYMMDD_HHMMSS.json` - Complete test results

### 2. Generated SHACL

- `run_01_shapes.ttl` through `run_NN_shapes.ttl` - SHACL outputs

### 3. Analysis (manually created)

- `reproducibility_analysis.md` - Detailed analysis
- `timing_methodology.md` - Timing explanation
- `test_validation.md` - Test validation

## Key Metrics to Track

For each test, record:

1. **Reproducibility Rate**
   - Formula: `(total_runs - unique_outputs + 1) / total_runs`
   - Target: >90%

2. **Classification Consistency**
   - Unique classification outputs / total runs
   - Deontic type variance (±N)
   - Target: Same classification every run

3. **FOL Consistency**
   - Unique FOL outputs / total runs
   - Target: <5 unique outputs

4. **Performance**
   - Average time per run
   - Classification phase time
   - FOL generation phase time

5. **Error Rate**
   - Failed LLM calls / total calls
   - Fallback activations

## Hypotheses to Test

1. **H1**: Temperature=0.0 increases reproducibility
2. **H2**: More explicit prompts reduce classification variance
3. **H3**: Larger models (llama2-70b) are more consistent
4. **H4**: Providing examples in prompts improves consistency
5. **H5**: Majority voting (3 runs) eliminates variance

## Running Hypothesis Tests

```bash
# Test H1: Temperature=0.0
# 1. Edit scripts/populate_llm_annotations_v2.py line 147: temperature = 0.0
# 2. Edit scripts/generate_fol_v2.py line XX: temperature = 0.0
python scripts/reproducibility_test.py --runs 20

# Test H4: Few-shot prompts
# 1. Modify prompt in populate_llm_annotations_v2.py to include examples
python scripts/reproducibility_test.py --runs 20

# Compare results
python scripts/compare_reproducibility_tests.py
```

## Thesis Data Analysis

After collecting multiple test runs:

1. **Statistical Analysis**
   - Mean reproducibility across all tests
   - Standard deviation
   - Confidence intervals

2. **Comparison Tables**
   - Configuration vs Reproducibility
   - Configuration vs Variance
   - Configuration vs Performance

3. **Visualizations** (create separately)
   - Line graph: Reproducibility over experiments
   - Box plot: Classification variance by configuration
   - Heatmap: Hash distribution patterns

## Next Steps

1. ✅ Baseline test completed (70% reproducibility)
2. ⬜ Test with temperature=0.0
3. ⬜ Test with improved prompts
4. ⬜ Test with majority voting
5. ⬜ Statistical analysis of all results
6. ⬜ Create visualizations for thesis
