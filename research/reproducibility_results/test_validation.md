# Reproducibility Test: What Actually Runs

## Executive Summary

**Answer: PARTIALLY - 2 out of 5 phases use actual LLM computation**

| Phase | Uses Real Pipeline? | What Actually Happens |
|-------|--------------------|-----------------------|
| 1. Extraction | ❌ **NO** | Loads pre-extracted JSON file |
| 2. Classification | ✅ **YES** | Real LLM calls to Mistral |
| 3. FOL Generation | ✅ **YES** | Real LLM calls to Mistral |
| 4. SHACL Translation | ✅ **YES** | Real Python logic (no LLM) |
| 5. Validation | ✅ **YES** | Real validation logic (no LLM) |

---

## Detailed Analysis

### Phase 1: Extraction ❌

**What SHOULD happen (full pipeline):**

```python
# Real pipeline
extract_from_pdfs(["AIT_Thesis_PP.pdf", ...])
  → Run OCR (Tesseract/EasyOCR)
  → Extract text blocks
  → Identify policy statements
  → Clean and normalize text
  → Return 97 rules
```

**What ACTUALLY happens (reproducibility test):**

```python
def _run_extraction_phase(self):
    # Just load pre-extracted JSON
    with open(GOLD_STANDARD_PATH, 'r', encoding='utf-8') as f:
        gold_standard = json.load(f)
    return {"count": len(gold_standard), "data": gold_standard}
```

**Why this shortcut?**

- OCR results might vary between runs (resolution, DPI, PDF renderer)
- PDF extraction is non-deterministic
- Would add 5-10 minutes per run
- **Purpose is to test LLM reproducibility**, not OCR reproducibility

**Impact:** Extraction phase takes ~0.005s instead of ~300s

---

### Phase 2: Classification ✅

**What happens:**

```python
def _run_classification_phase(self, extraction_result):
    for rule in rules:
        if self.use_mock_llm:
            # Mock: use existing annotation
            rule_type = rule.get("human_annotation", {}).get("rule_type")
        else:
            # REAL: Call actual LLM
            result = classify_rule_strict(rule.get("original_text", ""))
            rule_type = result.get("rule_type")
```

**Actual LLM call (from `populate_llm_annotations_v2.py`):**

```python
response = requests.post(
    f"{OLLAMA_HOST}/api/generate",
    json={
        "model": "mistral",
        "prompt": prompt,
        "temperature": 0.1,
        "options": {"num_predict": 800}
    }
)
```

**Verification:**

- ✅ Makes 97 HTTP requests to Ollama
- ✅ Each request sends the rule text
- ✅ Waits for LLM response
- ✅ Parses JSON output
- ✅ ~45 seconds total (proof it's real)

---

### Phase 3: FOL Generation ✅

**What happens:**

```python
def _run_fol_phase(self, classification_result):
    for item in results:
        if self.use_mock_llm:
            # Mock: simple formula
            fol = f"O({item['type']}(x))"
        else:
            # REAL: Call actual LLM
            result = generate_fol(item.get("original_text"), ollama_url)
            fol = result.get("deontic_formula")
```

**Actual LLM call (from `generate_fol_v2.py`):**

```python
# Same pattern as classification
response = requests.post(
    f"{ollama_url}/api/generate",
    json={
        "model": "mistral",
        "prompt": fol_prompt,  # More complex prompt
        "temperature": 0.1,
        ...
    }
)
```

**Verification:**

- ✅ Makes 97 HTTP requests to Ollama
- ✅ More complex prompts than classification
- ✅ Longer responses (~150 tokens vs ~50)
- ✅ ~77 seconds total (proof it's real)

---

### Phase 4: SHACL Translation ✅

**What happens:**

```python
def _run_shacl_phase(self, fol_result, run_id):
    from scripts.fol_to_shacl_v2 import make_refined_shape, PREFIXES
    
    # Python template-based generation
    shacl_output = PREFIXES
    for i, rule in enumerate(formatted_rules, 1):
        shape = make_refined_shape(rule, i)  # Pure Python logic
        shacl_output += shape
```

**Verification:**

- ✅ Uses real production function `make_refined_shape()`
- ✅ No LLM involved (deterministic logic)
- ✅ Generates actual Turtle/RDF syntax
- ✅ ~0.02 seconds (fast because it's just string operations)

---

### Phase 5: Validation ✅

**What happens:**

```python
def _run_validation_phase(self, shacl_result):
    from scripts.validate_shacl import validate_shacl_shapes
    
    validation_result = validate_shacl_shapes(shacl_file)
    return {
        "passed": validation_result.get("valid", False),
        "errors": validation_result.get("errors", [])
    }
```

**Verification:**

- ✅ Uses real production validation function
- ✅ Would call pySHACL if installed
- ✅ Currently does basic syntax check
- ✅ ~0.005 seconds

---

## Critical Question: Is This Valid Research?

### YES, because

1. **The research question is: "Is LLM-based policy formalization reproducible?"**
   - Not: "Is PDF extraction reproducible?" (we know it's not)
   - Not: "Is the full end-to-end system reproducible?" (that's a different question)

2. **The bottleneck is LLM inference, not data prep**
   - 99.9% of runtime is LLM calls
   - PDF extraction variability is orthogonal to LLM reproducibility

3. **Using gold standard input is standard practice**
   - Similar to using same dataset for ML model evaluation
   - Isolates the variable under test (LLM behavior)

4. **The test DID run actual Mistral LLM for 20 × 97 × 2 = 3,880 inferences**
   - Classification: 1,940 LLM calls
   - FOL Generation: 1,940 LLM calls
   - Total: 41 minutes of actual LLM computation

### But there's a gap

❌ **The test does NOT measure end-to-end pipeline reproducibility**

For a complete system evaluation, you would need:

```python
# Full E2E test (not implemented)
def test_full_pipeline():
    # Start with raw PDFs
    pdfs = ["AIT_Thesis_PP.pdf", ...]
    
    # Phase 1: OCR + Extraction (real)
    extracted = extract_rules_from_pdfs(pdfs)
    
    # Phase 2-5: Same as current test
    ...
```

---

## Recommendations

### For Your Thesis

**Current Test Name:** "LLM Reproducibility Test"  
**More Accurate Name:** "LLM-Based Formalization Reproducibility Test (Given Fixed Input)"

**How to frame it:**

1. **What you tested:** LLM reproducibility in classification and FOL generation
2. **What you controlled:** Input data (using gold standard)
3. **What you found:** 70% consistency in final output, 100% variability in intermediate steps
4. **What you didn't test:** OCR/extraction reproducibility (acknowledged limitation)

### For Complete System Validation

If you want to test **full pipeline reproducibility**, you need:

```python
# New test: reproducibility_test_e2e.py
def test_full_e2e_pipeline(num_runs=5):  # Fewer runs due to time
    results = []
    for i in range(num_runs):
        # Phase 1: Real PDF extraction
        extracted = run_pdf_extraction()  # ~300s
        
        # Phase 2-5: Real LLM pipeline
        final_shacl = run_llm_pipeline(extracted)  # ~120s
        
        results.append(final_shacl)
    
    # Compare all 5 outputs
    return analyze_e2e_reproducibility(results)
```

**Expected result:** Even LOWER reproducibility due to PDF extraction variance

---

## Conclusion

### What the Test Actually Does ✅

- Loads 97 pre-extracted rules (JSON)
- Makes 1,940 real LLM calls for classification
- Makes 1,940 real LLM calls for FOL generation  
- Generates SHACL shapes using production code
- Validates SHACL syntax

### What It Doesn't Do ❌

- PDF extraction/OCR
- Full end-to-end pipeline from raw documents

### Is This Valid? ✅ YES

- **For testing LLM reproducibility:** Excellent methodology
- **For testing system reproducibility:** Would need E2E test
- **For your thesis:** Clearly document the scope and limitations

### Your Results Are Still Valuable 📊

- You ran **3,880 actual LLM inferences** over 41 minutes
- You measured **real variability** in LLM outputs (70% consistency)
- You identified **classification as the main source of variance**
- You used **proper research methodology** with controlled inputs

**This is publishable research**, just frame it correctly! 🎯
