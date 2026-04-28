## AITGPT-compliance-checking

Compliance Checking Model is an agentic model pipeline that summarizes an instituion's policy rules from PDF documents to produce a SHACL validation shapes. Given a set of PDF documents, it  uses PyMuPDF to read and extract the document contents and then forward them to Ollama to classify the rules based on deontic logic (obligation, permission and prohibition). The rules are then formalized using First-Order Logic to translate into SHACL shapes for validating the student actions according to institutional policies.

### How the project is organize

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

### Project Structure
```

AITGPT-compliance-checking/
├── core/                        # Shared utilities
│   ├── prefilter.py             # Heuristic pre-filter (deontic marker detection)
│   ├── llm_cache.py             # SQLite-backed LLM response cache (prompt-versioned)
│   └── mcp_server.py            # JSON-RPC MCP server exposing 5 pipeline tools
│
├── db/                          # Database utilities
|   ├── schema.sql               # Database schema
|   ├── connection.py            # PostgreSQL connection handler
|   ├── rdf_converter.py         # RDF data converter
|   ├── seed.py                  # Database seeding script
|
├── langgraph_agent/             # Pipeline orchestration
│   ├── run.py                   # CLI entry-point (--source, --verbose, --ablation)
│   ├── graph.py                 # StateGraph assembly and conditional routing
│   ├── state.py                 # Typed PipelineState schema (TypedDict)
│   ├── llm.py                   # ChatOllama factory (seed, temperature, top_k)
│   ├── edges/
│   │   └── route_classify.py    # Conditional routing
│   └── nodes/                   # One file per pipeline stage
│       ├── extract.py           # PDF -> sentences (pdfplumber + optional spaCy)
│       ├── prefilter.py         # Wraps core/prefilter — filters non-rule candidates
│       ├── classify.py          # LLM classification with prefilter hint injection
│       ├── reclassify.py        # Second-opinion pass for uncertain rules
│       ├── fol.py               # FOL formalization with placeholder-rejection retry
│       ├── shacl.py             # FOL -> SHACL (named shapes, severity tiers)
│       ├── direct_shacl.py      # Direct NL -> SHACL fallback with syntax repair loop
│       ├── validate.py          # pyshacl validation + false-positive triage
│       └── report.py            # Structured JSON report (stats, env, violations)
│
├── evaluation/                  # Gold-standard evaluation (thesis metrics M1-M5)
│   ├── align.py                 # Multi-signal alignment: pipeline rules <-> gold shapes
│   ├── per_rule_eval.py         # Per-rule pyshacl evaluation against Pos/Neg entities
│   └── report.py                # Aggregates M1-M5 metrics, Markdown table output
│
├── shacl/                       # Authoritative knowledge artefacts
│   ├── ontology/
│   │   └── ait_policy_ontology.ttl   # Domain ontology (Person, Student, Fee, ...)
│   ├── shapes/
│   │   └── ait_policy_shapes.ttl     # 96 curated gold-standard SHACL shapes
│   └── test_data/
│       └── tdd_test_data_fixed.ttl   # Pos/Neg TDD test entities (180 per rule)
│
├── institutional_policy/        # Source PDFs (read-only input)
│   └── AIT/                     # Five AIT Policies & Procedures documents
│
├── output/                      # Pipeline reports & intermediate artifacts
│
├── web/                         # Web dashboard
│   ├── app.py                   # FastAPI application
│   ├── static/                  # CSS and JS
│   └── templates/               # HTML templates
│
├── graphdb_data/                # GraphDB data and logs
│   ├── data/                    # Settings and users
│   └── logs/                    # Execution logs
├── .example.env                 # Environment configuration template
|
└── requirements.txt             # Python dependencies
```

### Set up local/dev environment

**Prerequisites**
  |Tool|Min version|
  |----------|-----------|
  | Python | 3.10+ |
  | Ollama | 0.15.2+ |     
  | PostgreSQL | 15+ |  

Note: PostgreSQL is only needed if you use the db/ module to load entity data into
the compliance dashboard. The core pipeline (langgraph_agent/) does not require it.


**(1) Clone git repository**
``` bash
git clone https://github.com/AIT-brainlab/AITGPT-compliance-checking.git
cd AITGPT-compliance-checking
```

**(2) Create and activate virutal environment**
```bash
python -m venv .venv
```
- Linux / macOS:
``` bash
 source .venv/bin/activate
```
- Windows (PowerShell):
``` bash
.venv\Scripts\Activate.ps1
```

**(3) Install Python Dependencies**
``` bash
pip install -r requirements.txt
```

**(4) Set up environmanet**
``` bash
cp .env.example .env
```

Setting in .env:
``` bash 
  # Ollama
  OLLAMA_HOST=http://localhost:11434
  OLLAMA_MODEL=mistral
  OLLAMA_SECOND_MODEL=mistral        # override for a different second-opinion model
  OLLAMA_SEED=42                     # fixed seed -> reproducible results

  # Pipeline
  PIPELINE_VERSION=2.1-hints         # bump whenever prompts change to invalidate cache

  # Extraction
  EXTRACT_SPACY=0                    # 1 = spaCy sentencizer (requires spacy installed)

  # LLM cache
  CACHE_MAX_ENTRIES=2000

  # PostgreSQL (only needed for db/ entity loader)
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  POSTGRES_DB=ait_database
  POSTGRES_USER=myuser
  POSTGRES_PASSWORD=mypassword
```

**(5) Pull and start an Ollama**
``` bash
ollama pull mistral
```

   - In another terminal (keep it open):
``` bash
ollama serve
```

**(6) Run the pipeline**
``` bash
python -m langgraph_agent.run --source ait
```

Outputs land in `output/ait/`:

  |File|Contents|
  |----|--------|
  |pipeline_report.json|Summary stats, violation triage, environment metadata|
  |classified_rules.json|All rules with deontic type and confidence score|
  |fol_formulas.json| Generated FOL formulas per rule|
  |shapes_generated.ttl|Pipeline-produced SHACL shapes|
  |validation_results.json|pyshacl output against TDD test data|

**(7) Open website and dashboard**
``` bash
python web/app.py
```

### Deployment situation

## References

The pipeline design draws on:

- Goknil et al. (2024) — PAPEL: hierarchical filtering for policy extraction
- Brodie et al. (2006) — Section-aware classification for legal documents
- Searle (1969) — Speech Act Theory (directive / commissive / prohibitive / …)
- Governatori & Rotolo (2010) — Permission-as-exception in deontic logic
  (`deontic:overrides` in the ontology)

## License

Academic research project — AIT Master's Thesis.
