# PolicyChecker — AI Policy Formalization System

An agentic LangGraph pipeline for extracting, classifying, and formalizing institutional
policy rules from PDF documents into validatable SHACL shapes. Target use: academic
research on automated compliance verification over institutional corpora.

> **Master's Thesis — Asian Institute of Technology (AIT), 2026**

## 🎯 What it does

Given a folder of policy PDFs, PolicyChecker runs a nine-stage pipeline:

1. **Extract** — parses PDFs into sentences (`pdfplumber`, optional spaCy sentencizer)
2. **Prefilter** — heuristically filters non-rule content using deontic markers,
   section-aware weights (Brodie et al., 2006), Searle-style speech-act
   classification, and epistemic vs. deontic "may" disambiguation
3. **Classify** — uses a local LLM (Ollama/Mistral) to label each candidate as
   *obligation*, *permission*, or *prohibition*, enriched with prefilter hints
   (deontic strength, speech act, section context)
4. **Reclassify** — second-opinion pass for uncertain classifications using a
   configurable secondary model
5. **Formalize** — converts rules to First-Order Logic (FOL) formulas using deontic
   operators `O(φ)`, `P(φ)`, `F(φ)`, with placeholder rejection and retry
6. **Generate (FOL-mediated)** — translates FOL into SHACL `NodeShape`s with
   confidence-weighted severity, `sh:targetSubjectsOf` fallback, and named property shapes
7. **Generate (NL fallback)** — direct natural-language-to-SHACL for rules that
   resist FOL formalization, with syntax repair loop
8. **Validate** — merges pipeline shapes with gold-standard shapes and runs `pyshacl`
   against TDD test data, with false-positive triage
9. **Report** — generates a structured JSON report with pipeline stats, violation
   triage, environment metadata, and severity breakdown

The pipeline is orchestrated as a LangGraph state machine with conditional routing,
parallel fallback branches, and full ablation support for research measurement.

## 📊 Current pipeline output (AIT corpus)

Running the pipeline on the Asian Institute of Technology policy corpus
(`institutional_policy/AIT/`, 1,531 extracted sentences):

| Stage | Output |
|---|---:|
| Sentences extracted | 1,531 |
| Candidates after prefilter | 493 |
| Rules classified (confident) | 484 |
| FOL formulas generated | 467 (96.5% parse success) |
| FOL formulas failed | 17 |
| SHACL shapes produced | 484 (473 syntactically valid, 97.7%) |
| — FOL-mediated | 467 |
| — Direct NL fallback | 17 |
| Rule-type distribution | 385 obligations · 54 prohibitions · 45 permissions |
| Validation violations | 27,045 |
| Pipeline errors | 0 |

## 📈 Evaluation

The project includes a gold-standard evaluation harness (`evaluation/`) that aligns
pipeline-generated rules to 96 curated SHACL shapes (`shacl/shapes/ait_policy_shapes.ttl`)
using multi-signal alignment (embedding similarity, TF-IDF, fuzzy matching) and
evaluates each pipeline shape against its corresponding `Pos_GSxxx` / `Neg_GSxxx`
test entities.

| Metric | Definition | Current |
|---|---|---:|
| **M1** Extraction coverage | Gold rules with aligned pipeline rule (cosine ≥ 0.65) | **91.7%** (88/96) |
| **M2** Classification accuracy | Aligned rules with correct deontic type | **84.1%** (74/88) |
| **M3** FOL quality | FOL formulas with semantic predicates | **29.8%** (139/467) |
| **M4** Shape correctness (F1) | Per-rule precision/recall against Pos/Neg test entities | **F1 = 0.000** |
| **M5** Reproducibility | Identical output across clean-cache runs with fixed seed | ⏳ Not yet tested |

> [!NOTE]
> **M4 analysis:** All 43 evaluated shapes are currently `too_strict` (correct
> structure but failing Pos entities), and 32 are `too_permissive`. This indicates the
> pipeline shapes have the right *intent* but the property paths don't precisely match
> the gold-standard test data properties. This is the primary area for improvement.

> [!NOTE]
> **M3 analysis:** The low FOL quality rate (29.8%) reflects Mistral's tendency to
> generate placeholder predicates like `O(Action(x))`. The retry mechanism catches some,
> but a larger model or fine-tuned prompt would significantly improve this metric.

### Running the evaluation

```bash
python -m evaluation.align          # M1 extraction coverage → gold_alignment.json
python -m evaluation.per_rule_eval  # M4 shape correctness → per_rule_eval.json
python -m evaluation.report         # All metrics M1–M5 → console summary
python -m evaluation.report --md    # Markdown table for thesis
python -m evaluation.report --save  # Save thesis_metrics.json
```

## 🧪 Ablation studies

The pipeline supports **7 component-level ablations** for measuring the contribution
of each enhancement:

| Ablation | Flag | What it disables |
|----------|------|------------------|
| Baseline | `baseline` | Full pipeline (control) |
| No prefilter | `no-prefilter` | Skips heuristic filter, all sentences pass |
| No hints | `no-hints` | Strips prefilter hints from classifier |
| No reclassify | `no-reclassify` | Skips second-opinion pass |
| No fallback | `no-fallback` | Skips direct NL→SHACL fallback |
| No FOL retry | `no-fol-retry` | Disables placeholder rejection retry |
| No may disambig | `no-may-disambig` | Skips epistemic "may" filter |

```bash
python -m langgraph_agent.run --source ait --ablation no-hints
python -m langgraph_agent.run --source ait --ablation no-reclassify
python -m langgraph_agent.run --source ait --ablation no-fallback
```

Output is isolated to `output/ait_<ablation>/` for side-by-side comparison.

## 🗂️ Project structure

```
Compliance_Checking4Intern/
├── core/                     # PreFilter, LLM cache (SQLite), MCP server
│   ├── prefilter.py          # Heuristic filter (600+ lines, may disambiguation)
│   ├── llm_cache.py          # SQLite cache with prompt versioning
│   └── mcp_server.py         # JSON-RPC MCP compatibility layer
├── evaluation/               # Gold-standard alignment & thesis metrics
│   ├── align.py              # Multi-signal GS ↔ AIT alignment (M1)
│   ├── per_rule_eval.py      # Per-rule pyshacl evaluation (M4)
│   └── report.py             # M1–M5 thesis metrics aggregator
├── institutional_policy/     # Source PDFs (AIT corpus)
├── langgraph_agent/          # Pipeline orchestration
│   ├── nodes/                # 9 processing nodes
│   │   ├── extract.py        # PDF → sentences (pdfplumber + spaCy)
│   │   ├── prefilter.py      # Heuristic pre-filter wrapper
│   │   ├── classify.py       # LLM classification with hint injection
│   │   ├── reclassify.py     # Second-opinion reclassification
│   │   ├── fol.py            # FOL formalization with retry
│   │   ├── shacl.py          # FOL → SHACL (named shapes, severity tiers)
│   │   ├── direct_shacl.py   # NL → SHACL fallback with repair loop
│   │   ├── validate.py       # pyshacl validation with shape merging
│   │   └── report.py         # Structured report with env capture
│   ├── edges/                # Conditional routing (route_classify)
│   ├── graph.py              # Graph assembly (StateGraph)
│   ├── state.py              # Typed state schema (PipelineState)
│   ├── llm.py                # Ollama LLM configuration (seed, top_k)
│   └── run.py                # CLI with --ablation support
├── shacl/                    # Authoritative shapes, ontology, TDD test data
│   ├── shapes/               # 96 curated gold-standard shapes
│   ├── ontology/             # Domain ontology (Person, Student, Faculty, …)
│   └── test_data/            # 180 Pos/Neg test entities per rule
├── output/                   # Pipeline reports & intermediate artifacts
├── tests/                    # Pytest suite (121 tests)
│   ├── test_prefilter.py     # Core prefilter unit tests
│   ├── test_shacl_shapes.py  # Gold-standard SHACL shape validation
│   ├── test_may_disambiguation.py  # 45-sentence may eval set
│   ├── test_classify_hints.py      # Hint wiring & cache key tests
│   ├── test_align.py               # Alignment algorithm tests
│   ├── test_per_rule_eval.py       # Per-rule eval verdict tests
│   └── test_graph.py               # Graph structure tests
├── .env.example              # Environment configuration template
├── ARCHITECTURE.md           # Pipeline design & node walkthrough
└── POLICYCHECKER_ENHANCEMENT_PLAN.md   # Enhancement roadmap (completed)
```

## 🚀 Quick start

### 1. Dependencies

```bash
pip install -r requirements.txt
```

A local **Ollama** instance is required for LLM inference:

```bash
# macOS / Linux installer: https://ollama.com/download
ollama pull mistral
ollama serve   # leave running in a separate terminal
```

### 2. Environment

```bash
cp .env.example .env
```

Key settings (see `.env.example` for full list):

```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_SECOND_MODEL=mistral          # override with a different model for second-opinion
OLLAMA_SEED=42                       # required for reproducibility
PIPELINE_VERSION=2.1-hints           # bumped on any behavior-affecting change
```

### 3. Run the pipeline

```bash
python -m langgraph_agent.run --source ait --verbose
```

Outputs land in `output/ait/`:

- `pipeline_report.json` — summary stats, violation triage, and environment metadata
- `classified_rules.json` — all rules with deontic type and confidence
- `fol_formulas.json` — generated FOL formulas
- `shapes_generated.ttl` — pipeline-produced SHACL shapes
- `validation_results.json` — pyshacl output against test data

### 4. Run the tests

```bash
pytest                     # all 121 tests
pytest -m prefilter        # prefilter unit tests only
pytest -m shacl            # SHACL shape syntactic tests only
pytest tests/test_may_disambiguation.py  # May disambiguation eval set
```

## ⚠️ Current limitations

Transparency about what the pipeline does *not* yet handle well:

- **FOL predicate quality (M3 = 29.8%)** — the local LLM (Mistral 7B) frequently returns
  placeholder predicates like `O(Action(x))` instead of semantic ones like
  `O(payFee(student))`. The retry mechanism mitigates but does not eliminate this.
  A larger model or domain-specific fine-tuning would significantly improve M3.
- **Shape correctness (M4 = 0.000 F1)** — pipeline shapes are structurally valid but
  the property paths don't precisely match the gold-standard test data properties,
  causing all shapes to be classified as `too_strict` or `too_permissive`.
- **Epistemic vs. deontic "may"** — disambiguation is implemented at the prefilter level
  with 80%+ accuracy on the eval set, but recall is not yet 100%.
- **Sentence boundary detection** — PDF extraction produces some cross-item
  contamination. An optional spaCy sentencizer is available via `EXTRACT_SPACY=1`.
- **Target-class inference** — fallback to `sh:targetSubjectsOf` for `Person`-class
  shapes reduces over-broadening but doesn't eliminate it entirely.

## 🔧 Additional tools

- **MCP server** (`core/mcp_server.py`) — exposes single-rule verification over
  JSON-RPC for integration with MCP-compatible clients:

  ```bash
  python -m core.mcp_server --mcp          # stdio MCP mode
  python -m core.mcp_server                # interactive REPL
  ```

- **LLM cache** (`core/llm_cache.py`) — SQLite-backed deterministic cache for
  LLM responses. Cache keys include prompt version, so prompt edits invalidate
  stale entries automatically. Clear with:

  ```bash
  rm cache/llm_cache.db     # macOS/Linux
  Remove-Item cache\llm_cache.db   # Windows
  ```

## 📚 References

The pipeline design draws on:

- Goknil et al. (2024) — PAPEL: hierarchical filtering for policy extraction
- Brodie et al. (2006) — Section-aware classification for legal documents
- Searle (1969) — Speech Act Theory (directive / commissive / prohibitive / …)
- Governatori & Rotolo (2010) — Permission-as-exception in deontic logic
  (`deontic:overrides` in the ontology)

## 📝 License

Academic research project — AIT Master's Thesis.

## 🔗 Further reading

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — pipeline design, node walkthrough, state schema
- [`POLICYCHECKER_ENHANCEMENT_PLAN.md`](POLICYCHECKER_ENHANCEMENT_PLAN.md) — enhancement roadmap (completed)
