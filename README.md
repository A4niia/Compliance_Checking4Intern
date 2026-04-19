# PolicyChecker — AI Policy Formalization System

An agentic LangGraph pipeline for extracting, classifying, and formalizing institutional
policy rules from PDF documents into validatable SHACL shapes. Target use: academic
research on automated compliance verification over institutional corpora.

## 🎯 What it does

Given a folder of policy PDFs, PolicyChecker runs a six-stage pipeline:

1. **Extract** — parses PDFs into sentences (`pdfplumber`)
2. **Prefilter** — heuristically filters non-rule content using deontic markers,
   section-aware weights (Brodie et al., 2006), and Searle-style speech-act
   classification
3. **Classify** — uses a local LLM (Ollama) to label each candidate as *obligation*,
   *permission*, or *prohibition*, with a second-opinion pass for uncertain cases
4. **Formalize** — converts rules to First-Order Logic (FOL) formulas using deontic
   operators `O(φ)`, `P(φ)`, `F(φ)`
5. **Generate** — translates FOL into SHACL `NodeShape`s, with a direct natural-language
   fallback for rules that resist FOL formalization
6. **Validate** — runs `pyshacl` against a gold standard test dataset

The pipeline is orchestrated as a LangGraph state machine with conditional routing
and parallel fallback branches.

## 📊 Current pipeline output (AIT corpus)

Running the pipeline on the Asian Institute of Technology policy corpus
(`institutional_policy/AIT/`, 1,531 extracted sentences):

| Stage | Output |
|---|---:|
| Sentences extracted | 1,531 |
| Candidates after prefilter | 493 |
| Rules classified (confident) | 478 |
| FOL formulas generated | 461 (96.4% parse success) |
| SHACL shapes produced | 478 |
| SHACL shapes syntactically valid | 466 (97.5%) |
| Rule-type distribution | 381 obligations · 50 prohibitions · 47 permissions |

These are the raw pipeline statistics — not accuracy metrics against a ground truth.
See [§ Evaluation](#-evaluation) below.

## 📈 Evaluation

The project includes a gold-standard evaluation harness (`evaluation/`) that aligns
pipeline-generated rules to 96 curated SHACL shapes (`shacl/shapes/ait_policy_shapes.ttl`)
and evaluates each pipeline shape against its corresponding `Pos_GSxxx` / `Neg_GSxxx`
test entities.

| Metric | Definition | Current |
|---|---|---|
| **M1** Extraction coverage | Fraction of gold rules with an aligned pipeline rule (embedding similarity ≥ 0.65) | TBD |
| **M2** Classification coverage | Fraction of aligned rules with correct deontic type | TBD |
| **M3** FOL quality | Fraction of FOL formulas with semantic (non-placeholder) predicates | TBD |
| **M4** Shape correctness (F1) | Harmonic mean of per-rule precision/recall against Pos/Neg test entities | TBD |
| **M5** Reproducibility | Identical output across clean-cache runs with fixed seed | TBD |

> **Status:** harness implementation is in progress. See
> [`POLICYCHECKER_ENHANCEMENT_PLAN.md`](POLICYCHECKER_ENHANCEMENT_PLAN.md) § 3 for
> methodology and [`ARCHITECTURE.md`](ARCHITECTURE.md) for pipeline details.

## 🗂️ Project structure

```
RuleChecker_PoCv1/
├── core/                     # PreFilter, LLM cache (SQLite), MCP server
├── evaluation/               # Gold-standard alignment & per-rule metrics (WIP)
├── institutional_policy/     # Source PDFs (AIT corpus)
├── langgraph_agent/          # Pipeline orchestration
│   ├── nodes/                # Per-stage processing (extract, classify, fol, …)
│   ├── edges/                # Conditional routing (route_classify, route_fol)
│   ├── graph.py              # Graph assembly
│   ├── state.py              # Typed state schema
│   └── run.py                # CLI entrypoint
├── shacl/                    # Authoritative shapes, ontology, TDD test data
│   ├── shapes/               # 96 curated gold-standard shapes
│   ├── ontology/             # Domain ontology (Person, Student, Faculty, …)
│   └── test_data/            # 180 Pos/Neg test entities per rule
├── output/                   # Pipeline reports & intermediate artifacts
├── tests/                    # Pytest TDD suite
├── ARCHITECTURE.md           # Pipeline design & node walkthrough
└── POLICYCHECKER_ENHANCEMENT_PLAN.md   # Active roadmap
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
PIPELINE_VERSION=2.1                 # bumped on any behavior-affecting change
```

### 3. Run the pipeline

```bash
python -m langgraph_agent.run --source ait --verbose
```

Outputs land in `output/ait/`:

- `pipeline_report.json` — summary stats and violation triage
- `classified_rules.json` — all rules with deontic type and confidence
- `fol_formulas.json` — generated FOL formulas
- `shapes_generated.ttl` — pipeline-produced SHACL shapes
- `validation_results.json` — pyshacl output against test data

### 4. Run the evaluation harness

Once the harness is implemented (see enhancement plan § 3):

```bash
python -m evaluation.align         # M1 extraction coverage
python -m evaluation.per_rule_eval # M2, M4 shape correctness
```

### 5. Run the tests

```bash
pytest                     # all tests
pytest -m prefilter        # prefilter unit tests only
pytest -m shacl            # SHACL shape syntactic tests only
```

## 🧪 Ablation studies

The pipeline supports component-level ablations for research measurement:

```bash
python -m langgraph_agent.run --source ait --ablation no-hints
python -m langgraph_agent.run --source ait --ablation no-reclassify
python -m langgraph_agent.run --source ait --ablation no-fallback
```

Output is written to `output/ait_<ablation>/`. See the enhancement plan § 7 for the
full ablation table and rationale.

## ⚠️ Current limitations

Transparency about what the pipeline does *not* yet handle well:

- **Epistemic vs. deontic "may"** — descriptive sentences like *"Research may be
  sponsored by agencies"* are sometimes misclassified as permission rules.
  Disambiguation is implemented at the prefilter level but recall is not yet 100%.
- **FOL predicate quality** — the local LLM (mistral) occasionally returns
  placeholder predicates like `O(Action(x))` instead of semantic ones like
  `O(payFee(student))`. A retry pass with a stricter prompt mitigates but does not
  eliminate this.
- **Sentence boundary detection** — PDF extraction produces some cross-item
  contamination (trailing list markers, soft-wrapped lines). An optional spaCy-based
  sentencizer is available via `EXTRACT_SPACY=1`.
- **Target-class inference** — pipeline shapes default to `ait:Person` when the
  rule subject cannot be matched to a specific ontology class, which over-broadens
  validation scope. Using `sh:targetSubjectsOf` as a fallback mitigates this.

These are tracked in the enhancement plan.

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
- [`POLICYCHECKER_ENHANCEMENT_PLAN.md`](POLICYCHECKER_ENHANCEMENT_PLAN.md) — active improvement roadmap
