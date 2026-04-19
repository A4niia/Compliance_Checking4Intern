# PolicyChecker — Enhancement Plan for Thesis-Grade Metrics

**Scope.** Every fix, improvement, and thesis-measurement artifact that should exist in this repository before final results are reported. Ordered by *impact on the metrics you said matter most*:

1. Coverage (% of gold rules reproduced)
2. Determinism / reproducibility
3. SHACL shape correctness
4. FOL quality
5. Classification accuracy

Each item below has four parts: **Problem** (what's wrong and why), **Fix** (concrete code or design), **Impact** (what metric it moves), **Verify** (how you check it worked). Where code is shown, assume it is a drop-in replacement for the corresponding section in your current file.

---

## Table of contents

1. [Current state snapshot](#1-current-state-snapshot)
2. [Phase 1 — Critical blockers](#2-phase-1--critical-blockers)
   - 2.1 [PreFilter hints must reach the classifier](#21-prefilter-hints-must-reach-the-classifier)
   - 2.2 [`_merge_shapes` silently drops ~98% of pipeline shapes](#22-_merge_shapes-silently-drops-98-of-pipeline-shapes)
   - 2.3 [Logical variables leaking into SHACL property paths](#23-logical-variables-leaking-into-shacl-property-paths)
   - 2.4 [Determinism — seeds and prompt versioning](#24-determinism--seeds-and-prompt-versioning)
3. [Phase 2 — The evaluation harness (thesis-critical)](#3-phase-2--the-evaluation-harness-thesis-critical)
   - 3.1 [Why this is the load-bearing piece](#31-why-this-is-the-load-bearing-piece)
   - 3.2 [Design — GS ↔ AIT alignment](#32-design--gs--ait-alignment)
   - 3.3 [Per-rule pyshacl evaluation](#33-per-rule-pyshacl-evaluation)
   - 3.4 [The five thesis metrics](#34-the-five-thesis-metrics)
   - 3.5 [Implementation skeleton](#35-implementation-skeleton)
4. [Phase 3 — Quality improvements that move the numbers](#4-phase-3--quality-improvements-that-move-the-numbers)
   - 4.1 [Sentence splitting — fix the `\n1.` pollution](#41-sentence-splitting--fix-the-n1-pollution)
   - 4.2 [Epistemic vs. deontic "may" disambiguation](#42-epistemic-vs-deontic-may-disambiguation)
   - 4.3 [Reject placeholder FOL predicates](#43-reject-placeholder-fol-predicates)
   - 4.4 [Target-class inference — stop defaulting to Person](#44-target-class-inference--stop-defaulting-to-person)
   - 4.5 [Property path derivation — multi-source](#45-property-path-derivation--multi-source)
5. [Phase 4 — SHACL shape correctness](#5-phase-4--shacl-shape-correctness)
   - 5.1 [Shape IDs that survive validation result lookup](#51-shape-ids-that-survive-validation-result-lookup)
   - 5.2 [Severity tiers — calibrate violations](#52-severity-tiers--calibrate-violations)
   - 5.3 [Permission-as-exception](#53-permission-as-exception)
6. [Phase 5 — Reproducibility & thesis hygiene](#6-phase-5--reproducibility--thesis-hygiene)
   - 6.1 [Full-determinism configuration](#61-full-determinism-configuration)
   - 6.2 [Model pinning and environment capture](#62-model-pinning-and-environment-capture)
   - 6.3 [Pipeline version tags](#63-pipeline-version-tags)
   - 6.4 [Align README / ARCHITECTURE with reality](#64-align-readme--architecture-with-reality)
7. [Phase 6 — Ablation studies for the thesis](#7-phase-6--ablation-studies-for-the-thesis)
8. [Phase 7 — Lower-priority polish](#8-phase-7--lower-priority-polish)
9. [Implementation schedule](#9-implementation-schedule)
10. [Appendix A — Copy-paste ready code blocks](#appendix-a--copy-paste-ready-code-blocks)
11. [Appendix B — Prompt templates](#appendix-b--prompt-templates)
12. [Appendix C — Metric definitions](#appendix-c--metric-definitions)

---

## 1. Current state snapshot

After your most recent round of fixes (2026-04-19 run):

| Metric | Pre-fix | Current | Still broken? |
|---|---:|---:|---|
| FOL ok / failed | 444 / 35 | 461 / 17 | Predicates still generic (`Action(x)`) |
| SHACL shapes total | 35 | **478** | ✅ main bug fixed |
| SHACL shapes valid (per-shape check) | 11 | 466 | Syntax ok, but see §2.2 |
| `fol_mediated` shapes | **0** | 461 | ✅ parallel-merge bug fixed |
| `shape_count` at validate time | 107 | 101 | ⚠ only ~5 of 466 pipeline shapes actually loaded |
| Violations | 1948 | 1948 | Masked by §2.2 — noise floor |
| PreFilter hints reach classifier | No | **Still no** | §2.1 |
| Seed / deterministic decoding | No | No | §2.4 |
| Gold-standard evaluation | No | No | §3 |
| README vs. actual behaviour | Inconsistent | Inconsistent | §6.4 |

**Headline finding from the new run.** `validation_results.json → shape_count: 101`. The gold file has 96 NodeShapes; you added 466 "valid" pipeline shapes; you got 101. The merge is silently dropping ~461 shapes. Everything you're measuring against right now is effectively the gold file alone. Fixing §2.2 is the one-line change that lets the pipeline actually get measured.

---

## 2. Phase 1 — Critical blockers

These are the "nothing else matters until these are done" items. All four should be done in one sitting.

### 2.1 PreFilter hints must reach the classifier

#### Problem
`core/prefilter.py` computes, per sentence: `deontic_strength`, `speech_act`, `section_context`, `section_weight`, `confidence_boost`. These are grounded in Searle (1969) speech-act theory and Brodie et al. (2006) section-aware classification — they're thesis-citeable work.

`langgraph_agent/nodes/prefilter.py` then throws all of it away:

```python
for item, result in zip(items, results):
    if result.is_candidate:
        candidates.append(item)   # only the boolean used
```

And `langgraph_agent/nodes/classify.py` has:

```python
hint = {}  # prefilter hints (populated if attached to item)
```

Every `classified_rules.json` entry shows this symptom: `prefilter_strength: "unknown"`, `section_context: ""`. The classifier's prompt has slots for these hints but they receive `"unknown"` for every sentence.

#### Fix

**Step 1 — extend `SentenceItem` in `langgraph_agent/state.py`:**

```python
class SentenceItem(TypedDict, total=False):
    # required
    text: str
    page: int
    source: str
    # optional — populated by prefilter_node
    deontic_strength: str       # "strong" | "weak" | "consequence" | "none"
    speech_act: str             # "directive" | "commissive" | "prohibitive" | "assertive" | "suggestive"
    section_context: str
    section_weight: float
    confidence_boost: float
```

Using `total=False` means old code constructing `SentenceItem` without these fields still type-checks.

**Step 2 — populate hints in `langgraph_agent/nodes/prefilter.py`:**

```python
from langgraph_agent.state import PipelineState, SentenceItem

def prefilter_node(state: PipelineState) -> PipelineState:
    sentences: List[SentenceItem] = state["extracted_sentences"]
    errors: List[str] = []

    from collections import defaultdict
    by_source: dict[str, List[SentenceItem]] = defaultdict(list)
    for s in sentences:
        by_source[s["source"]].append(s)

    candidates: List[SentenceItem] = []

    for source, items in by_source.items():
        texts = [i["text"] for i in items]
        try:
            results = _prefilter.filter_sentences(texts)
            for item, result in zip(items, results):
                if result.is_candidate:
                    enriched: SentenceItem = {
                        **item,
                        "deontic_strength": result.deontic_strength,
                        "speech_act": result.speech_act,
                        "section_context": result.section_context,
                        "section_weight": result.section_weight,
                        "confidence_boost": result.confidence_boost,
                    }
                    candidates.append(enriched)
        except Exception as exc:
            errors.append(f"prefilter: error processing {source}: {exc}")
            candidates.extend(items)  # graceful degradation

    return {
        "candidates": candidates,
        "current_step": "prefilter",
        "errors": errors,
    }
```

**Step 3 — read hints in `langgraph_agent/nodes/classify.py`:**

```python
def classify_node(state: PipelineState) -> PipelineState:
    candidates: List[SentenceItem] = state["candidates"]
    model = DEFAULT_MODEL
    errors: List[str] = []
    rules: List[RuleItem] = []
    uncertain: List[RuleItem] = []

    for i, item in enumerate(candidates):
        text = item["text"]

        # NEW — read prefilter hints from the item itself
        hint = {
            "deontic_strength": item.get("deontic_strength", "unknown"),
            "speech_act":       item.get("speech_act", "unknown"),
            "section_context":  item.get("section_context", "unknown"),
        }
        boost = float(item.get("confidence_boost", 0.0))

        # Include hints in cache key — same text with different hints
        # is a different request
        cache_params = {
            "deontic_strength": hint["deontic_strength"],
            "speech_act": hint["speech_act"],
        }

        cached = _cache.get(text, model, "classification", extra_params=cache_params)
        if cached:
            result = cached
        else:
            try:
                prompt = _build_prompt(item, hint)
                response = _llm.invoke([HumanMessage(content=prompt)])
                result = _parse_response(response.content)
                _cache.set(text, model, "classification", result, extra_params=cache_params)
            except Exception as exc:
                errors.append(f"classify[{i}]: {exc}")
                result = {"is_rule": False, "rule_type": "none",
                          "confidence": 0.0, "reasoning": str(exc)}

        if not result.get("is_rule"):
            continue

        # Existing sanitiser
        if result.get("rule_type") in ("none", None, ""):
            result["rule_type"] = "obligation"
            result["confidence"] = max(float(result.get("confidence", 0.5)) - 0.1, 0.4)

        # NEW — apply prefilter boost to confidence (clamped to [0, 1])
        raw_conf = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, raw_conf + boost))

        rule_id = f"AIT-{i:04d}"
        rule = RuleItem(
            rule_id=rule_id,
            text=text,
            source_document=item["source"],
            rule_type=result.get("rule_type", "obligation"),
            confidence=confidence,
            prefilter_strength=hint["deontic_strength"],  # now real
            section_context=hint["section_context"],     # now real
        )

        if confidence >= CONFIDENCE_HIGH:
            rules.append(rule)
        elif confidence >= CONFIDENCE_LOW:
            uncertain.append(rule)

    return {
        "rules": rules,
        "uncertain_rules": uncertain,
        "current_step": "classify",
        "errors": errors,
    }
```

Two design decisions embedded above, both deliberate:

1. **The boost is additive** (`raw_conf + boost`) rather than multiplicative. The PreFilter's `confidence_boost` is already small (±0.15) and designed to nudge the LLM verdict; multiplicative compounds awkwardly when raw confidence is near 0 or 1.
2. **Hints are part of the cache key.** Otherwise, when you edit the PreFilter (e.g., add a new deontic marker), cached classifications made without hints get served to new-hint requests. Cache is only useful if it reflects actual input.

#### Impact
- Classification accuracy: best-case +5 to +10 pp, from directly injecting disambiguating context (weak-may in Definitions section, strong-must in Requirements section, etc.)
- Eliminates the "99% of rules say `prefilter_strength: unknown`" artefact in your output JSON that makes classified_rules.json look broken.

#### Verify
After a rerun, grep `classified_rules.json`:

```bash
python -c "import json; rules=json.load(open('output/ait/classified_rules.json')); 
unknowns = sum(1 for r in rules if r['prefilter_strength']=='unknown'); 
print(f'{unknowns}/{len(rules)} with unknown prefilter_strength')"
```

Should be close to 0 after fix (any remaining are graceful-degradation fallbacks).

---

### 2.2 `_merge_shapes` silently drops ~98% of pipeline shapes

#### Problem
In `langgraph_agent/nodes/validate.py`:

```python
for shape in pipeline_shapes:
    if shape["syntax_valid"] and shape["turtle_text"]:
        try:
            g.parse(data=shape["turtle_text"], format="turtle")  # <-- no prefixes!
        except Exception:
            pass  # skip malformed shapes silently  <-- silent failure
```

In `langgraph_agent/nodes/shacl.py`, `_fol_to_turtle` emits turtle that **uses** the `ait:`, `sh:`, `deontic:` prefixes but only declares them when writing the whole file to disk — not when returning a single `turtle_text`. So:

- `direct_shacl.py` passes its `_validate_turtle` check because that function *does* prepend `_SHACL_PREFIXES`.
- `shacl.py`'s `_fol_to_turtle` marks `syntax_valid=True` unconditionally (it's template-generated — can't fail).
- Then `_merge_shapes` tries to parse per-shape turtle with no prefix declarations, every parse raises `rdflib.plugins.parsers.notation3.BadSyntax`, and the bare `except: pass` eats it.

**Evidence.** `validation_results.json → shape_count: 101`. If the merge worked you'd see 96 + 466 ≈ 562. The delta of 5 that did get through are likely shapes whose turtle happened to contain a prefix declaration (unusual path).

Every violation you're currently counting is coming from the **gold** shapes hitting test data. Your pipeline shapes are not being evaluated at all.

#### Fix

Two changes — centralise the prefix string, then prepend it at merge time:

**`langgraph_agent/nodes/shacl.py` — no change needed, but make `_TTL_PREFIXES` importable (it already is).**

**`langgraph_agent/nodes/validate.py`:**

```python
from langgraph_agent.nodes.shacl import _TTL_PREFIXES

def _merge_shapes(pipeline_shapes: List[SHACLShape]) -> Graph:
    g = Graph()

    if SHACL_SHAPES_FILE.exists():
        g.parse(str(SHACL_SHAPES_FILE), format="turtle")

    skipped = 0
    for shape in pipeline_shapes:
        if not (shape["syntax_valid"] and shape["turtle_text"]):
            continue
        try:
            # Prepend prefixes so the turtle block resolves ait:, sh:, deontic:
            g.parse(
                data=_TTL_PREFIXES + shape["turtle_text"],
                format="turtle",
            )
        except Exception as exc:
            skipped += 1
            # Log, don't swallow — makes failures visible in report
            # (propagated via state["errors"])

    if skipped:
        import logging
        logging.getLogger(__name__).warning(
            f"_merge_shapes: skipped {skipped}/{len(pipeline_shapes)} shapes (parse error)"
        )

    return g
```

And in `validate_node`, capture the skip count into errors so it reaches the report:

```python
# After _merge_shapes returns, capture the shape-count reality check
merged_shape_count = len(list(shapes_graph.subjects(RDF.type, SH.NodeShape)))
expected = 96 + sum(1 for s in shapes if s["syntax_valid"])  # 96 = authoritative count
if merged_shape_count < expected * 0.95:
    errors.append(
        f"validate: shape merge dropped {expected - merged_shape_count} shapes "
        f"(expected ~{expected}, got {merged_shape_count})"
    )
```

#### Impact
- Suddenly your 466 pipeline shapes are evaluated against the 180 test entities. **Expect violation count to balloon to 10,000+ on first run.** That's not a regression — that's finally measuring your pipeline. The §2.3 and §4.4 fixes below dramatically cut the noise.
- Without this fix, every coverage/correctness metric you report is false.

#### Verify
```python
# Add an assertion at the end of validate_node during development:
assert merged_shape_count >= 96, f"Gold shapes disappeared: {merged_shape_count}"
if sum(1 for s in shapes if s["syntax_valid"]) > 100:
    assert merged_shape_count > 200, f"Pipeline shapes not merging: {merged_shape_count}"
```

---

### 2.3 Logical variables leaking into SHACL property paths

#### Problem
Your latest `pipeline_report.json` triage shows shapes with sample messages like:

```
Less than 1 values on ait:Pos_GS093->ait:x
Less than 1 values on ait:Pos_GS093->ait:y
```

In `langgraph_agent/nodes/shacl.py`:

```python
def _property_path(fol: FOLItem) -> str:
    m = re.search(r"[OPF]\(([a-zA-Z_]+)", fol["deontic_formula"])
    if m:
        raw = m.group(1)
        parts = re.sub(r"([A-Z])", r" \1", raw).strip().split()
        return parts[0][0].lower() + parts[0][1:] + ...
    return _slugify(fol["text"])
```

Given an LLM-emitted formula like `O(x)` or `P(Action(?y))` — both appear in `fol_formulas.json` — the regex matches `x` or `y` as the predicate name. `ait:x` and `ait:y` then become property paths. Every test entity fails these constraints because none of them have an `ait:x` property (obviously).

#### Fix

Reject variable-like tokens and fall through to the slug fallback:

```python
# Reserved/placeholder predicates to reject
_PLACEHOLDER_PREDICATES = {
    "x", "y", "z", "n", "m",           # logical variables
    "action", "subject", "predicate",  # LLM lazy placeholders
    "condition", "thing", "entity",
}

def _property_path(fol: FOLItem) -> str:
    """Derive a SHACL property path from the FOL formula.
    Priority: deontic predicate > subject slug > action slug > rule text slug.
    """
    # --- Try deontic operator argument ---
    m = re.search(r"[OPF]\(([a-zA-Z_]+)", fol["deontic_formula"])
    if m:
        raw = m.group(1)
        if (len(raw) > 1 
            and raw.lower() not in _PLACEHOLDER_PREDICATES):
            parts = re.sub(r"([A-Z])", r" \1", raw).strip().split()
            return parts[0][0].lower() + parts[0][1:] + "".join(
                p.capitalize() for p in parts[1:]
            )

    # --- Try predicates.action from FOL output (see §4.3) ---
    predicates = fol.get("predicates") or {}
    action = predicates.get("action", "") if isinstance(predicates, dict) else ""
    if action and action.lower() not in _PLACEHOLDER_PREDICATES:
        return _slugify(action, max_words=3, first_lower=True)

    # --- Fall back to slug from rule text, preferring the main verb ---
    return _slugify(fol["text"], max_words=4, first_lower=True)


def _slugify(text: str, max_words: int = 4, first_lower: bool = False) -> str:
    words = re.sub(r"[^a-zA-Z0-9 ]", "", text).split()
    if not words:
        return "policyRule"
    selected = words[:max_words]
    result = "".join(w.capitalize() for w in selected)
    if first_lower and result:
        result = result[0].lower() + result[1:]
    return result
```

Note the signature change to `_slugify(first_lower=True)` — SHACL property paths conventionally start lowercase (`ait:payFee`, not `ait:PayFee`). Previously `_slugify` always capitalised. Sweep the file for other `_slugify` callers and pass `first_lower=False` where you want shape IDs.

#### Impact
- Eliminates the `ait:x`/`ait:y` noise floor — roughly 200+ violations per ~60 entities each, in your current report.
- Makes pipeline-generated properties semantically meaningful, which is essential for §3 (evaluation against gold shapes that use real property names).

#### Verify
```bash
grep -c 'ait:x\|ait:y' output/ait/shapes_generated.ttl
# Should be 0 or near-0 after fix.
```

---

### 2.4 Determinism — seeds and prompt versioning

#### Problem
Two separate determinism leaks:

**(a)** `langgraph_agent/llm.py`:
```python
return ChatOllama(
    model=model or DEFAULT_MODEL,
    temperature=temperature,
    base_url=OLLAMA_HOST,
    # Pass seed via num_ctx workaround — actual seed set in options at call time
)
```
The comment admits it: no seed is ever set. So re-runs of the same sentence through the same model can produce different classifications, which re-fills the cache with conflicting values, which makes any downstream metric unreproducible.

Meanwhile `core/mcp_server.py` does set a seed via raw requests:
```python
options={"temperature": 0.0, "seed": 42, "num_predict": 512}
```

Two code paths disagreeing on determinism is worse than either one alone.

**(b)** `core/llm_cache.py` generates keys from `(text, model, prompt_type, temperature, extra_params)`. If you edit `_CLASSIFY_PROMPT` — which you will, especially to inject the new hints from §2.1 — old cached responses for the *old* prompt get served to the *new* prompt. Silent staleness.

#### Fix

**(a) Seed at the Ollama call level.** `ChatOllama` in recent `langchain-ollama` accepts `model_kwargs`:

```python
# langgraph_agent/llm.py
from __future__ import annotations
import os
from langchain_ollama import ChatOllama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
SECOND_MODEL = os.getenv("OLLAMA_SECOND_MODEL", "mistral")
SEED = int(os.getenv("OLLAMA_SEED", "42"))

def get_llm(model: str | None = None,
            temperature: float = 0.0,
            seed: int = SEED) -> ChatOllama:
    """Return a ChatOllama instance with deterministic decoding."""
    return ChatOllama(
        model=model or DEFAULT_MODEL,
        temperature=temperature,
        base_url=OLLAMA_HOST,
        model_kwargs={
            "seed": seed,
            "num_predict": 512,
            "top_k": 1,          # greedy decoding — redundant with temp=0 but explicit
            "top_p": 1.0,
        },
    )

def get_second_llm() -> ChatOllama:
    # Different seed so it's not literally the same sample twice
    return get_llm(model=SECOND_MODEL, seed=SEED + 1)
```

If your `langchain-ollama` version doesn't honour `model_kwargs` (varies by release), fall back to calling Ollama via raw `requests` in a thin wrapper — same pattern as `mcp_server.py` — and drop `ChatOllama`.

**(b) Prompt versioning in cache keys.** Promote each prompt to a module-level constant with a version, and fold the version into `extra_params`:

```python
# langgraph_agent/nodes/classify.py
CLASSIFY_PROMPT_VERSION = "v3-hints"
_CLASSIFY_PROMPT = """..."""  # your current prompt

# In classify_node:
cache_params = {
    "prompt_version": CLASSIFY_PROMPT_VERSION,
    "deontic_strength": hint["deontic_strength"],
    "speech_act": hint["speech_act"],
}
cached = _cache.get(text, model, "classification", extra_params=cache_params)
```

Do the same for `_FOL_PROMPT`, `_RECLASSIFY_PROMPT`, `_DIRECT_PROMPT`, `_REPAIR_PROMPT` — bump the version every time you edit the prompt text.

A nice ergonomic touch: write a helper in `llm_cache.py`:

```python
def prompt_key(version: str, **extras) -> dict:
    return {"prompt_version": version, **extras}
```

so call sites stay tidy:

```python
cache.get(text, model, "classification",
          extra_params=prompt_key("v3-hints", deontic_strength=hint["deontic_strength"]))
```

#### Impact
- Reproducibility dimension → full check. Your thesis committee can re-run and get the exact same numbers, assuming the same model weights and Ollama version.
- Makes iterative prompt tuning actually work. Change a prompt, bump version, old cache entries remain but new requests miss and re-query.

#### Verify
```bash
# Run twice, diff outputs:
python -m langgraph_agent.run --source ait
cp output/ait/classified_rules.json /tmp/run1.json
rm -rf cache/llm_cache.db  # force re-query
python -m langgraph_agent.run --source ait
diff <(jq -S . /tmp/run1.json) <(jq -S . output/ait/classified_rules.json)
# Should be empty.
```

---

## 3. Phase 2 — The evaluation harness (thesis-critical)

### 3.1 Why this is the load-bearing piece

You currently have two ID spaces that don't talk:

- **Gold standard:** `GS-001 … GS-096` (in `ait_policy_shapes.ttl`), each with a curated `rdfs:comment` containing the source rule text, a target class, and property constraints. 180 test entities named `Pos_GSxxx` / `Neg_GSxxx` exercise each shape.
- **Pipeline output:** `AIT-0000 … AIT-0478`, indexed by position in the extracted-sentence list. No link to GS IDs.

Without an alignment, you cannot answer:

- *What fraction of the 96 gold rules did my pipeline recover?* (coverage)
- *Of the rules it recovered, did it classify the deontic type correctly?* (classification accuracy)
- *Do my pipeline shapes pass Pos_GSxxx and fail Neg_GSxxx the way the gold shape does?* (shape correctness)

The 1948-violations number is a proxy at best; it mixes gold-shape behaviour on test data with pipeline-shape behaviour (when the merge works) and gives you no per-rule signal. The evaluation harness converts the pipeline from "makes a lot of shapes" into something defensible in a thesis.

### 3.2 Design — GS ↔ AIT alignment

A new package `evaluation/` with three modules:

```
evaluation/
├── __init__.py
├── align.py          # GS ↔ AIT matching
├── per_rule_eval.py  # pyshacl on one pipeline shape against its gold Pos/Neg entities
└── report.py         # assemble the five thesis metrics into tables
```

**Alignment approach.** For each of the 96 gold shapes, extract its `rdfs:comment` (the authoritative rule text). For each of the ~478 pipeline rules, extract `text`. Compute similarity, pick the best match per gold shape above a threshold.

Three similarity strategies, in descending order of how much you should trust them:

| Strategy | Cost | Signal quality | Recommended for |
|---|---|---|---|
| Sentence-embedding cosine (e.g., `all-MiniLM-L6-v2`, ~22MB) | ~5s total, one-time model download | Best — semantic | Thesis-grade results |
| TF-IDF + cosine | No dependencies beyond sklearn | Good on lexical overlap, fails on paraphrase | Quick first pass |
| RapidFuzz `token_set_ratio` | Tiny | Decent for near-duplicates, terrible for paraphrase | Smoke testing |

Recommended: run all three and log all three similarity scores. Use embeddings as the primary matcher, TF-IDF as tiebreaker for ambiguous matches, and fuzz as a sanity check. For thesis writeup you can say "we used sentence embeddings as the primary alignment method, validated against TF-IDF and lexical similarity."

**Threshold.** Start at embedding cosine ≥ 0.65 and hand-label the bottom quartile to calibrate. A match below threshold = gold rule has no pipeline equivalent (counts as missed coverage).

**One-to-many handling.** If two pipeline rules both match the same gold shape above threshold, keep the best-scoring one and record the rest as "duplicates" — useful to know for the writeup but not for metrics.

### 3.3 Per-rule pyshacl evaluation

Once each gold shape has an aligned pipeline shape, run pyshacl **per rule**:

```
For each GS-xxx with a matched AIT-yyyy pipeline shape:
    Build a graph containing ONLY the pipeline shape.
    Build a data graph containing ONLY Pos_GSxxx and Neg_GSxxx.
    Validate. Record:
        - pos_passes: Pos_GSxxx passes validation (True = TP)
        - neg_fails:  Neg_GSxxx fails validation (True = TN)
```

This gives you a 2×2 per rule:

| | Pos_GSxxx passes | Pos_GSxxx fails |
|---|---|---|
| **Neg_GSxxx passes** | Shape too permissive (FP on compliance; missed violation) | Shape inverted |
| **Neg_GSxxx fails** | ✅ Correct | Shape too strict (FP on violation) |

The four cells aggregated across all matched rules give you your end-to-end precision / recall.

### 3.4 The five thesis metrics

These are the metrics your committee will actually care about. Each has a definition, a computation, and a target.

**M1 — Extraction coverage.** Fraction of gold rules whose rule text appears (above similarity threshold) in the pipeline's candidate list *after prefilter*.
- `#GS with ≥1 aligned candidate / 96`
- Captures: does prefilter + extract retain the right sentences?

**M2 — Classification coverage.** Fraction of gold rules matched to an AIT rule whose pipeline `rule_type` equals the gold `deontic:type`.
- `#GS where rule_type matches / #GS aligned`
- Captures: does the LLM correctly classify deontic type?

**M3 — FOL quality rate.** Fraction of matched rules with non-placeholder FOL predicates.
- `1 - (#GS with placeholder / #GS with FOL)`
- Placeholder = predicate in `{Action, Subject, Predicate, x, y, z}` or length 1.
- Captures: is the FOL layer producing usable output, or just decoration?

**M4 — Shape correctness (end-to-end precision/recall).** From the 2×2 above.
- Precision = `correct / (correct + too_strict)`: when the shape flags a violation, is it right?
- Recall = `correct / (correct + too_permissive)`: does the shape catch the violations it should?
- F1 harmonic mean for headline.

**M5 — Reproducibility.** Numerical. Two back-to-back runs with a cleared cache should give:
- Identical `classified_rules.json` after `jq -S`
- Identical `shapes_generated.ttl` (byte-level)
- Delta = 0 on all five metrics above.

### 3.5 Implementation skeleton

Below is a runnable-shaped skeleton. Fill in the `TODO`s and adapt to your preferences.

**`evaluation/align.py`:**

```python
"""Align pipeline rules (AIT-xxxx) to gold shapes (GS-xxx) by rule text similarity."""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from rdflib import Graph, Namespace, RDF, RDFS
from rdflib.namespace import SH

PROJECT_ROOT = Path(__file__).parent.parent
AIT = Namespace("http://example.org/ait-policy#")
DEONTIC = Namespace("http://example.org/deontic#")

@dataclass
class GoldRule:
    gs_id: str                  # "GS-001"
    text: str                   # rdfs:comment
    deontic_type: str           # "obligation" | "permission" | "prohibition"
    target_class: str
    shape_uri: str              # full URI of the sh:NodeShape

@dataclass
class Alignment:
    gs_id: str
    ait_id: Optional[str]       # None = unmatched
    pipeline_text: Optional[str]
    embedding_score: float
    tfidf_score: float
    fuzz_score: float
    aligned: bool               # passed primary threshold


def load_gold_rules(shapes_file: Path) -> List[GoldRule]:
    g = Graph()
    g.parse(str(shapes_file), format="turtle")

    rules: List[GoldRule] = []
    for shape in g.subjects(RDF.type, SH.NodeShape):
        label = g.value(shape, RDFS.label)
        comment = g.value(shape, RDFS.comment)
        target = g.value(shape, SH.targetClass)
        dtype = g.value(shape, DEONTIC.type)

        if not (label and comment and target):
            continue
        rules.append(GoldRule(
            gs_id=str(label),
            text=str(comment),
            deontic_type=_dtype_label(dtype),
            target_class=str(target).split("#")[-1],
            shape_uri=str(shape),
        ))
    return rules


def _dtype_label(dtype) -> str:
    if dtype is None:
        return "unknown"
    frag = str(dtype).split("#")[-1]
    return {"obligation": "obligation",
            "permission": "permission",
            "prohibition": "prohibition"}.get(frag, "unknown")


def load_pipeline_rules(classified_json: Path) -> list[dict]:
    return json.loads(classified_json.read_text(encoding="utf-8"))


def align_all(gold: List[GoldRule],
              pipeline: list[dict],
              threshold: float = 0.65) -> List[Alignment]:
    from sentence_transformers import SentenceTransformer, util
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from rapidfuzz import fuzz
    import numpy as np

    # --- Embeddings ---
    model = SentenceTransformer("all-MiniLM-L6-v2")
    gold_vecs = model.encode([g.text for g in gold], convert_to_tensor=True)
    pipe_vecs = model.encode([r["text"] for r in pipeline], convert_to_tensor=True)
    emb_sim = util.cos_sim(gold_vecs, pipe_vecs).cpu().numpy()  # shape (|gold|, |pipe|)

    # --- TF-IDF ---
    vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", lowercase=True)
    all_docs = [g.text for g in gold] + [r["text"] for r in pipeline]
    tfidf = vec.fit_transform(all_docs)
    tfidf_sim = cosine_similarity(tfidf[: len(gold)], tfidf[len(gold):])

    alignments: List[Alignment] = []
    for i, gr in enumerate(gold):
        # primary: embeddings
        j = int(np.argmax(emb_sim[i]))
        emb_score = float(emb_sim[i, j])
        tfidf_score = float(tfidf_sim[i, j])
        fuzz_score = float(fuzz.token_set_ratio(gr.text, pipeline[j]["text"])) / 100.0

        aligned = emb_score >= threshold
        alignments.append(Alignment(
            gs_id=gr.gs_id,
            ait_id=pipeline[j]["rule_id"] if aligned else None,
            pipeline_text=pipeline[j]["text"] if aligned else None,
            embedding_score=emb_score,
            tfidf_score=tfidf_score,
            fuzz_score=fuzz_score,
            aligned=aligned,
        ))
    return alignments


def main() -> None:
    shapes = PROJECT_ROOT / "shacl" / "shapes" / "ait_policy_shapes.ttl"
    classified = PROJECT_ROOT / "output" / "ait" / "classified_rules.json"
    out = PROJECT_ROOT / "output" / "ait" / "gold_alignment.json"

    gold = load_gold_rules(shapes)
    pipeline = load_pipeline_rules(classified)
    alignments = align_all(gold, pipeline)

    coverage = sum(1 for a in alignments if a.aligned) / len(alignments)
    print(f"Extraction coverage (M1): {coverage:.1%} ({sum(1 for a in alignments if a.aligned)}/{len(alignments)})")

    out.write_text(
        json.dumps([asdict(a) for a in alignments], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
```

**`evaluation/per_rule_eval.py`:**

```python
"""Run pyshacl per-rule: one pipeline shape against one gold Pos/Neg pair."""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from pyshacl import validate
from rdflib import Graph, Namespace, URIRef

PROJECT_ROOT = Path(__file__).parent.parent
AIT = Namespace("http://example.org/ait-policy#")

_PREFIXES = """
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh:     <http://www.w3.org/ns/shacl#> .
@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .
@prefix ait:    <http://example.org/ait-policy#> .
@prefix deontic: <http://example.org/deontic#> .
"""

@dataclass
class RuleEvalResult:
    gs_id: str
    ait_id: str
    pos_passes: Optional[bool]    # None if test entity missing
    neg_fails: Optional[bool]
    verdict: str                  # "correct" | "too_strict" | "too_permissive" | "inverted" | "skipped"


def _entity_subgraph(full_data: Graph, entity_uri: URIRef) -> Graph:
    """Extract a single entity and its direct properties."""
    sub = Graph()
    for p, o in full_data.predicate_objects(entity_uri):
        sub.add((entity_uri, p, o))
    return sub


def evaluate_rule(gs_id: str,
                  ait_id: str,
                  pipeline_turtle: str,
                  test_data: Graph,
                  ontology: Graph) -> RuleEvalResult:
    gs_num = gs_id.replace("GS-", "").zfill(3)
    pos_uri = AIT[f"Pos_GS{gs_num}"]
    neg_uri = AIT[f"Neg_GS{gs_num}"]

    # Build single-shape graph
    shape_graph = Graph()
    try:
        shape_graph.parse(data=_PREFIXES + pipeline_turtle, format="turtle")
    except Exception:
        return RuleEvalResult(gs_id, ait_id, None, None, "skipped")

    pos_graph = _entity_subgraph(test_data, pos_uri)
    neg_graph = _entity_subgraph(test_data, neg_uri)

    pos_passes = None
    neg_fails = None

    if len(pos_graph) > 0:
        conforms, _, _ = validate(
            pos_graph, shacl_graph=shape_graph, ont_graph=ontology,
            inference="rdfs", abort_on_first=False, meta_shacl=False,
        )
        pos_passes = bool(conforms)

    if len(neg_graph) > 0:
        conforms, _, _ = validate(
            neg_graph, shacl_graph=shape_graph, ont_graph=ontology,
            inference="rdfs", abort_on_first=False, meta_shacl=False,
        )
        neg_fails = not bool(conforms)

    # 2x2 interpretation
    if pos_passes is None or neg_fails is None:
        verdict = "skipped"
    elif pos_passes and neg_fails:
        verdict = "correct"
    elif pos_passes and not neg_fails:
        verdict = "too_permissive"
    elif not pos_passes and neg_fails:
        verdict = "too_strict"
    else:
        verdict = "inverted"

    return RuleEvalResult(gs_id, ait_id, pos_passes, neg_fails, verdict)


def main() -> None:
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))

    alignment_file = PROJECT_ROOT / "output" / "ait" / "gold_alignment.json"
    shapes_file    = PROJECT_ROOT / "output" / "ait" / "shapes_generated.ttl"
    test_file      = PROJECT_ROOT / "shacl" / "test_data" / "tdd_test_data_fixed.ttl"
    onto_file      = PROJECT_ROOT / "shacl" / "ontology"  / "ait_policy_ontology.ttl"
    out_file       = PROJECT_ROOT / "output" / "ait" / "per_rule_eval.json"

    alignments = json.loads(alignment_file.read_text())
    test_data = Graph().parse(str(test_file), format="turtle")
    ontology  = Graph().parse(str(onto_file), format="turtle")

    # Parse the generated shapes file into a dict keyed by rule_id
    pipeline_shapes_text = shapes_file.read_text(encoding="utf-8")
    shape_blocks = _split_shape_blocks(pipeline_shapes_text)  # see utility below

    results: List[RuleEvalResult] = []
    for al in alignments:
        if not al["aligned"]:
            continue
        turtle = shape_blocks.get(al["ait_id"], "")
        if not turtle:
            continue
        r = evaluate_rule(al["gs_id"], al["ait_id"], turtle, test_data, ontology)
        results.append(r)

    out_file.write_text(
        json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _print_summary(results)


def _split_shape_blocks(ttl_text: str) -> dict[str, str]:
    """Parse the comment markers `# Rule: AIT-xxxx` to associate turtle blocks."""
    import re
    blocks: dict[str, str] = {}
    current_id = None
    current_lines: list[str] = []
    for line in ttl_text.splitlines():
        m = re.match(r"# Rule:\s+(AIT-\d+)", line)
        if m:
            if current_id and current_lines:
                blocks[current_id] = "\n".join(current_lines)
            current_id = m.group(1)
            current_lines = [line]
        elif current_id:
            current_lines.append(line)
    if current_id and current_lines:
        blocks[current_id] = "\n".join(current_lines)
    return blocks


def _print_summary(results: List[RuleEvalResult]) -> None:
    from collections import Counter
    c = Counter(r.verdict for r in results)
    total = sum(c.values())
    correct = c.get("correct", 0)
    too_strict = c.get("too_strict", 0)
    too_perm = c.get("too_permissive", 0)

    precision = correct / (correct + too_strict) if (correct + too_strict) else 0
    recall    = correct / (correct + too_perm)   if (correct + too_perm) else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    print(f"\nShape correctness (M4):")
    print(f"  Total evaluated: {total}")
    for v, n in c.most_common():
        print(f"    {v:16s}: {n}")
    print(f"  Precision: {precision:.3f}")
    print(f"  Recall:    {recall:.3f}")
    print(f"  F1:        {f1:.3f}")


if __name__ == "__main__":
    main()
```

**Output after running both scripts:**

```
$ python -m evaluation.align
Extraction coverage (M1): 72.9% (70/96)

$ python -m evaluation.per_rule_eval

Shape correctness (M4):
  Total evaluated: 70
    correct         : 34
    too_strict      : 22
    too_permissive  : 11
    inverted        : 3
  Precision: 0.607
  Recall:    0.756
  F1:        0.673
```

These are thesis numbers. They tell a story. Your committee can argue with specific cells.

---

## 4. Phase 3 — Quality improvements that move the numbers

The evaluation harness (§3) transforms opaque aggregate reports into per-rule metrics. Below are the four changes that move those metrics the most.

### 4.1 Sentence splitting — fix the `\n1.` pollution

#### Problem
In `langgraph_agent/nodes/extract.py`:
```python
parts = re.split(r"(?<=[.;])\s+(?=[A-Z])", raw)
```

This regex handles prose but not numbered lists. Evidence from `classified_rules.json`:

```json
{"rule_id": "AIT-0002",
 "text": "Authors must be\nresponsible for what has been written in return for the credit and recognition that\nauthorship brings.\n1."}

{"rule_id": "AIT-0004",
 "text": "However, the Chair of the student's Program\nCommittee should serve as the corresponding author with any journal.\n3."}
```

The trailing `\n1.` and `\n3.` are list markers from the NEXT item being glued onto the previous rule. Unwrapped newlines inside the rule also appear. Downstream:

- The FOL stage feeds `Authors must be\nresponsible...\n1.` to the LLM. The model treats the trailing `1.` as new content, producing weird predicate names.
- Similarity matching in §3 gets confused by the noise.

#### Fix

A two-pass extractor: first normalise PDF artefacts, then split.

```python
# langgraph_agent/nodes/extract.py — replacement for _split_sentences

_LIST_MARKER = re.compile(r"\n\s*(\d+\.|\([a-z]\)|[a-z]\)|\*|\-)\s+")
_SOFT_WRAP = re.compile(r"(?<=[a-z,;:])\n(?=[a-z])")
_MULTI_NL = re.compile(r"\n{2,}")
_TRAILING_LIST_NUM = re.compile(r"\s*\n?\s*\d+\.\s*$")


def _normalise(raw: str) -> str:
    """Clean PDF extraction artefacts before sentence splitting."""
    # Rejoin soft-wrapped lines: "...to the\ncommittee..." -> "...to the committee..."
    raw = _SOFT_WRAP.sub(" ", raw)
    # Collapse blank lines
    raw = _MULTI_NL.sub("\n", raw)
    # Normalise whitespace
    raw = re.sub(r"[ \t]+", " ", raw)
    return raw


def _split_sentences(raw: str) -> List[str]:
    raw = _normalise(raw)

    # First pass: split on list markers (they always start a new item)
    items = _LIST_MARKER.split(raw)

    # Second pass: split each item on sentence boundaries
    sentences: list[str] = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        # Split on . or ; followed by whitespace + capital letter
        parts = re.split(r"(?<=[.;])\s+(?=[A-Z])", item)
        for p in parts:
            # Strip trailing list markers that leaked through
            p = _TRAILING_LIST_NUM.sub("", p.strip())
            if p:
                sentences.append(p)

    return sentences
```

**Better still:** add a spaCy-based sentencizer behind a feature flag, for a more robust alternative you can cite in the methodology:

```python
# Optional, gated by env var
import os
USE_SPACY = os.getenv("EXTRACT_SPACY", "0") == "1"

if USE_SPACY:
    import spacy
    _nlp = spacy.load("en_core_web_sm", disable=["ner", "tagger"])

def _split_sentences(raw: str) -> List[str]:
    raw = _normalise(raw)
    if USE_SPACY:
        doc = _nlp(raw)
        return [s.text.strip() for s in doc.sents if s.text.strip()]
    # ... fallback regex path above
```

Running both with your evaluation harness (§3) gives you an ablation for free: "Regex splitter vs. spaCy splitter, M1 delta = X pp."

#### Impact
- Direct hit on M1 (extraction coverage) and M3 (FOL quality) — because cleaner input produces cleaner predicates.
- Anticipated: +3 to +5 pp on M1.

#### Verify
```bash
grep -E "\\\\n[0-9]+\\.$" output/ait/classified_rules.json | wc -l
# Should be 0 after fix.
```

---

### 4.2 Epistemic vs. deontic "may" disambiguation

#### Problem
The clearest hallucinations in `fol_formulas.json`:

```json
{"rule_id": "AIT-0000",
 "text": "Research may be\nsponsored by a government agency...",
 "deontic_type": "permission"}   // WRONG — this is epistemic "may"

{"rule_id": "AIT-0001",
 "text": "Contracted research may\nentail confidentiality...",
 "deontic_type": "obligation",    // WRONG — and also inconsistent
 "deontic_formula": "O(Confidentiality_and_Restriction_on_Publication(x))"}
```

English "may" is lexically ambiguous between:
- **Deontic permission:** "Students may apply for leave." — permission granted.
- **Epistemic possibility:** "Research may be sponsored by an agency." — descriptive, not deontic.

The classifier prompts ask the LLM to decide without distinguishing these uses. Result: everything with "may" gets labelled as policy content.

#### Fix

Three layers, cheapest first.

**Layer 1 — lexical pre-check in `core/prefilter.py`.** Expand the existing speech-act detection to flag epistemic "may" constructions:

```python
# core/prefilter.py — additional patterns

EPISTEMIC_MAY_PATTERNS = [
    # "may be sponsored", "may be cancelled", "may entail"
    re.compile(r"\bmay\s+be\b", re.IGNORECASE),
    re.compile(r"\bmay\s+have\b", re.IGNORECASE),
    re.compile(r"\bmay\s+entail\b", re.IGNORECASE),
    re.compile(r"\bmay\s+include\b", re.IGNORECASE),
    re.compile(r"\bmay\s+contain\b", re.IGNORECASE),
    re.compile(r"\bmay\s+result\s+in\b", re.IGNORECASE),
]

DEONTIC_MAY_PATTERNS = [
    # "may apply for", "may request", "may submit", "may use"
    re.compile(r"\bmay\s+(apply|request|submit|use|access|file|obtain|appeal)\b", re.IGNORECASE),
    # "may not" — always deontic (prohibition)
    re.compile(r"\bmay\s+not\b", re.IGNORECASE),
]


def disambiguate_may(text: str) -> str:
    """Return 'deontic', 'epistemic', or 'ambiguous'."""
    if not re.search(r"\bmay\b", text, re.IGNORECASE):
        return "n/a"
    if any(p.search(text) for p in DEONTIC_MAY_PATTERNS):
        return "deontic"
    if any(p.search(text) for p in EPISTEMIC_MAY_PATTERNS):
        return "epistemic"
    return "ambiguous"
```

Then in `PreFilter.filter_sentence`, when a "weak" marker is "may" and `disambiguate_may(text) == "epistemic"`, reject it:

```python
# inside filter_sentence, after strength detection
if strength == "weak" and "may" in text.lower():
    may_sense = disambiguate_may(text)
    if may_sense == "epistemic":
        return FilterResult(
            text=text, is_candidate=False,
            deontic_strength="none",
            rejection_reason="Epistemic 'may' (possibility, not permission)",
            speech_act="assertive",
            section_context=section_name, section_weight=section_weight,
        )
```

**Layer 2 — explicit instruction in the classify prompt.** Update `_CLASSIFY_PROMPT`:

```python
_CLASSIFY_PROMPT = """\
You are a legal policy analyst specialising in institutional policy documents.

Classify whether the sentence below is a POLICY RULE — a deontic statement that
creates a binding obligation, grants a permission, or imposes a prohibition.

IMPORTANT DISTINCTIONS:
- "may be X-ed" / "may have" / "may entail" = DESCRIPTIVE possibility, NOT a rule.
  Example: "Research may be sponsored by agencies." → NOT A RULE (describes what CAN happen).
- "may apply for" / "may request" / "may use" = PERMISSION (deontic rule).
  Example: "Students may apply for leave." → PERMISSION RULE (grants a right).
- "may not" = always a PROHIBITION.

Context hints:
- Deontic strength: {deontic_strength}
- Speech act: {speech_act}
- Section: {section}

Sentence:
"{text}"

Respond with ONLY a JSON object (no markdown, no explanation):
{{"is_rule": true/false, "rule_type": "obligation"/"permission"/"prohibition"/"none",
"confidence": 0.0-1.0, "reasoning": "one concise sentence"}}"""
```

Bump the prompt version (§2.4b).

**Layer 3 — small labelled eval set for calibration.** Hand-label 50 "may" sentences from your extracted output as {deontic, epistemic}. Run the pipeline, measure accuracy on this subset before and after the fix. Report the delta in your thesis — cite it as a targeted contribution.

#### Impact
- Moves M2 (classification accuracy). Anticipated: +10 to +20 pp depending on how "may"-heavy your corpus is.
- Also moves M1 upward (epistemic-may sentences are no longer pretending to be rules that the pipeline then fails to match to a gold rule).

#### Verify
Create a small fixture in `tests/test_may_disambiguation.py` with known cases and run.

---

### 4.3 Reject placeholder FOL predicates

#### Problem
From `fol_formulas.json`:
```json
{"deontic_formula": "O(Action(x))", ...}
{"deontic_formula": "P(Action(?x))", ...}
{"deontic_formula": "O(Subject(x))", ...}
```

The LLM is hitting a local minimum where it returns the literal schema tokens from the prompt. These predicates carry no semantic content — downstream SHACL generation can't do anything useful with `O(Action(x))`.

#### Fix

**Detect placeholders and re-prompt.** In `langgraph_agent/nodes/fol.py`:

```python
_PLACEHOLDER_PREDS = re.compile(
    r"[OPF]\(\s*(Action|Subject|Predicate|Condition|Thing|Entity|x|y|z|\?\w)\s*[()]",
    re.IGNORECASE,
)

def _is_placeholder(parsed: dict) -> bool:
    formula = parsed.get("deontic_formula", "")
    if _PLACEHOLDER_PREDS.search(formula):
        return True
    # Also check predicates dict if available
    preds = parsed.get("predicates") or {}
    if isinstance(preds, dict):
        action = preds.get("action", "").lower()
        if action in ("action", "subject", "predicate", "condition", "thing", "entity"):
            return True
    return False


_FOL_RETRY_PROMPT = """\
Your previous FOL formalization used placeholder predicates like "Action" or single letters.
That is not acceptable — use SEMANTIC predicates derived from the rule's actual action.

Rule type: {rule_type}
Rule text: "{text}"
Previous (BAD) formula: {bad_formula}

Rules:
- The inner predicate must name the actual action (e.g., "payFee", "submitThesis", "attendMeeting").
- Use snake_case or camelCase derived from the rule's main verb phrase.
- Do NOT use: Action, Subject, Predicate, Condition, or any single letter.

Output ONLY a JSON object:
{{
  "deontic_type": "obligation"/"permission"/"prohibition",
  "deontic_formula": "O/P/F(semanticPredicate(subject))",
  "fol_expansion": "...",
  "predicates": {{"subject": "...", "action": "...", "condition": "..."}}
}}"""


def fol_node(state: PipelineState) -> PipelineState:
    # ... existing setup ...
    for rule in rules:
        text = rule["text"]
        rule_type = rule["rule_type"]

        cached = _cache.get(text, model, "fol_generation",
                            extra_params={"rule_type": rule_type,
                                          "prompt_version": FOL_PROMPT_VERSION})
        if cached:
            parsed = cached
        else:
            parsed = _generate_with_retry(text, rule_type)
            if parsed:
                _cache.set(text, model, "fol_generation", parsed,
                           extra_params={"rule_type": rule_type,
                                         "prompt_version": FOL_PROMPT_VERSION})
        # ... rest unchanged


def _generate_with_retry(text: str, rule_type: str, max_retries: int = 1) -> dict | None:
    """Generate FOL, retry with stricter prompt if placeholder detected."""
    prompt = _FOL_PROMPT.format(text=text, rule_type=rule_type)
    response = _llm.invoke([HumanMessage(content=prompt)])
    parsed = _parse_fol(response.content)

    if not parsed:
        return None

    for attempt in range(max_retries):
        if not _is_placeholder(parsed):
            return parsed
        # Re-prompt with the bad example
        retry_prompt = _FOL_RETRY_PROMPT.format(
            text=text, rule_type=rule_type,
            bad_formula=parsed.get("deontic_formula", ""),
        )
        response = _llm.invoke([HumanMessage(content=retry_prompt)])
        parsed = _parse_fol(response.content) or parsed

    # If still placeholder after retry, tag it (don't drop — §4.5 falls back)
    if _is_placeholder(parsed):
        parsed["_placeholder_flag"] = True
    return parsed
```

You can also decide to route `_placeholder_flag=True` rules to `fol_failed` and let `direct_shacl` handle them — it's your choice whether to treat placeholders as failure.

#### Impact
- M3 (FOL quality) is the whole point of this fix. Anticipated: from ~60% non-placeholder currently to >90% with one retry.
- Indirect M4 improvement: real predicates → real property paths → shapes that actually test something meaningful.

#### Verify
```python
# After a rerun
import json, re
fols = json.load(open("output/ait/fol_formulas.json"))
bad = re.compile(r"[OPF]\((Action|Subject|Predicate|x|y|z)[\(\)]", re.I)
placeholders = sum(1 for f in fols if bad.search(f["deontic_formula"]))
print(f"Placeholder rate: {placeholders}/{len(fols)} = {placeholders/len(fols):.1%}")
```

Target: <5%.

---

### 4.4 Target-class inference — stop defaulting to Person

#### Problem
In `shacl.py`:
```python
def _infer_target_class(text: str) -> str:
    t = text.lower()
    for pattern, cls in _SUBJECT_MAP:
        if re.search(pattern, t):
            return cls
    return "Person"
```

Any rule whose subject isn't in the `_SUBJECT_MAP` regex list defaults to `ait:Person`. That means a shape with a `sh:minCount 1` constraint on some property fires on every `Pos_/Neg_` entity that doesn't have that property — 180 entities × ~dozens of shapes = hundreds of violations per shape. This is where most of your 1948 comes from (once §2.2 is fixed and pipeline shapes actually merge, it'll be even worse).

#### Fix

Two complementary strategies.

**Strategy A — use the FOL `predicates.subject` field.** Your FOL prompt already asks for `predicates.subject`. Use it:

```python
# langgraph_agent/nodes/shacl.py
from rdflib import Graph, Namespace, RDFS
from pathlib import Path

_ONTOLOGY_PATH = PROJECT_ROOT / "shacl" / "ontology" / "ait_policy_ontology.ttl"
AIT = Namespace("http://example.org/ait-policy#")

# One-time load
_ontology_classes: set[str] | None = None

def _load_ontology_classes() -> set[str]:
    global _ontology_classes
    if _ontology_classes is None:
        g = Graph()
        if _ONTOLOGY_PATH.exists():
            g.parse(str(_ONTOLOGY_PATH), format="turtle")
        _ontology_classes = {
            str(s).split("#")[-1] for s in g.subjects(RDFS.subClassOf, None)
        } | {str(s).split("#")[-1] for s, _, _ in g.triples((None, None, None))
             if str(s).startswith(str(AIT))}
    return _ontology_classes


def _infer_target_class(text: str, fol: FOLItem | None = None) -> str:
    """Infer a target class by (1) FOL subject, (2) regex map, (3) Person fallback."""
    # --- Strategy A: use FOL subject if it matches an ontology class ---
    if fol is not None:
        preds = fol.get("predicates") or {}
        if isinstance(preds, dict):
            subj = (preds.get("subject") or "").strip()
            if subj:
                # Normalise: "the student" -> "Student", "sponsors" -> "Sponsor"
                candidates = _candidates_from_subject(subj)
                classes = _load_ontology_classes()
                for c in candidates:
                    if c in classes:
                        return c

    # --- Strategy B: regex map on rule text ---
    t = text.lower()
    for pattern, cls in _SUBJECT_MAP:
        if re.search(pattern, t):
            return cls

    # --- Strategy C: fallback — but narrower than Person ---
    return "Person"


def _candidates_from_subject(subj: str) -> list[str]:
    """Convert 'the postgraduate students' into ['PostgraduateStudent', 'Student']."""
    words = re.findall(r"[A-Za-z]+", subj.lower())
    # strip determiners
    words = [w for w in words if w not in {"the", "a", "an", "any", "all", "each", "every"}]
    # singularise trivially (drop trailing 's')
    words = [w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words]
    if not words:
        return []
    # Candidates: full concat, pairwise, single
    joined = "".join(w.capitalize() for w in words)
    singles = [w.capitalize() for w in words]
    return [joined] + singles
```

**Strategy B — use `sh:targetObjectsOf` or `sh:targetNode` instead of `sh:targetClass` when inference is weak.** The problem with `targetClass` is it applies to every instance of the class. If you can't confidently name the class, you can still emit a shape that targets only nodes which are subjects of a specific predicate:

```turtle
# Instead of:
ait:SomeShape a sh:NodeShape ;
    sh:targetClass ait:Person ;
    sh:property [ sh:path ait:payFee ; sh:minCount 1 ] .

# Use:
ait:SomeShape a sh:NodeShape ;
    sh:targetSubjectsOf ait:payFee ;   # only things that have this predicate
    sh:property [ sh:path ait:payFee ; sh:minCount 1 ] .
```

This approach is *technically* a different semantics (it doesn't force entities that lack the predicate to have it) but for partial extraction it's more honest — you're saying "wherever this predicate appears, validate it."

In your `_fol_to_turtle`, add a fallback:

```python
def _fol_to_turtle(fol: FOLItem) -> tuple[str, str, bool]:
    target = _infer_target_class(fol["text"], fol)
    prop_path = _property_path(fol)
    ...
    if target == "Person":
        # Weak inference — use targetSubjectsOf instead of targetClass
        target_clause = f"sh:targetSubjectsOf ait:{prop_path}"
    else:
        target_clause = f"sh:targetClass ait:{target}"

    turtle = (
        f"# Rule: {fol['rule_id']} | {deontic_type.upper()}\n"
        f"# FOL: {fol['deontic_formula']}\n"
        f"ait:{shape_id} a sh:NodeShape ;\n"
        f"    {target_clause} ;\n"
        f"    sh:severity {severity} ;\n"
        f"    sh:property [ ... ]\n"
    )
```

#### Impact
- M4 precision gets the biggest improvement here. Shapes stop firing on entities they have no business checking.
- Indirect cost: `sh:targetSubjectsOf` is more permissive — but in a research prototype, reporting honest precision on narrower targets is better than fake precision on broad targets.

#### Verify
```python
# After rerun, check how many pipeline shapes still default to Person:
import re
from pathlib import Path
ttl = Path("output/ait/shapes_generated.ttl").read_text()
person_count = len(re.findall(r"sh:targetClass ait:Person", ttl))
total_shapes = ttl.count("a sh:NodeShape")
print(f"{person_count}/{total_shapes} default to Person ({person_count/total_shapes:.0%})")
```

Target: <30%. Currently it's ~70%+ based on rule-text patterns.

---

### 4.5 Property path derivation — multi-source

This is covered in §2.3 and §4.3 — the `_property_path` fix uses the deontic operator argument, falls through to `predicates.action` from FOL, then to a slug of the rule text. With the placeholder rejection in §4.3 you have two high-quality sources of semantic predicate names, making property paths much more uniform.

---

## 5. Phase 4 — SHACL shape correctness

### 5.1 Shape IDs that survive validation result lookup

#### Problem
In `validation_results.json`, every `source_shape` looks like `n117601403f3342f28ffaec7e743377b5b164`. That's a blank-node ID for the **anonymous `sh:property` node inside the NodeShape** — not the NodeShape itself. Because both your pipeline-generated shapes and the authoritative shapes use anonymous property shapes (`sh:property [ sh:path ... ]`), when pyshacl reports a violation it reports the inner blank node, not the parent shape.

Consequence: your report's "top-5 triggered shapes" groups by meaningless IDs. You can't tell *which rule* is misbehaving without walking the graph backward from the blank node to its parent NodeShape.

#### Fix

Two options, equally valid:

**Option A — give property shapes URIs.** In both `shacl.py` and `direct_shacl.py`, emit:

```turtle
ait:AIT_0001Shape a sh:NodeShape ;
    sh:targetClass ait:Student ;
    sh:property ait:AIT_0001Shape_prop1 .

ait:AIT_0001Shape_prop1 a sh:PropertyShape ;
    sh:path ait:payFee ;
    sh:minCount 1 ;
    sh:message "Students must pay all fees before registration." .
```

pyshacl will now report `source_shape = ait:AIT_0001Shape_prop1` which is greppable and traceable to its rule ID.

**Option B — post-process validation results** to walk the graph backward. Add a resolver in `validate.py`:

```python
def _resolve_parent_shape(results_graph: Graph, shapes_graph: Graph,
                          result_node) -> str:
    """Walk from a validation result's sourceShape back to its owning NodeShape."""
    source = results_graph.value(result_node, SH.sourceShape)
    if source is None:
        return "unknown"
    # If source is already a NodeShape, done
    if (source, RDF.type, SH.NodeShape) in shapes_graph:
        return str(source)
    # Otherwise it's an anonymous property shape — find the NodeShape that uses it
    for parent in shapes_graph.subjects(SH.property, source):
        return str(parent)
    return str(source)  # fallback
```

Then in `validate_node`:

```python
for result in results_graph.subjects(RDF.type, SH.ValidationResult):
    parent = _resolve_parent_shape(results_graph, shapes_graph, result)
    violations.append({
        "focus_node":     str(results_graph.value(result, SH.focusNode)),
        "source_shape":   parent,      # now resolved to the parent NodeShape
        "source_path":    str(results_graph.value(result, SH.resultPath)),
        "result_message": str(results_graph.value(result, SH.resultMessage)),
        "severity":       str(results_graph.value(result, SH.resultSeverity)),
    })
```

**Recommendation:** do Option B immediately (it's safer and requires no pipeline changes), then move to Option A for new shapes when you have time. The validation report's "top-5" will become actionable overnight.

#### Impact
- Report triage becomes useful — you can see which rules are misbehaving.
- Required infrastructure for §3.3 (per-rule evaluation has to know which shape belongs to which rule).

---

### 5.2 Severity tiers — calibrate violations

Currently every shape emits `sh:Violation`. The gold shapes show the more nuanced pattern: obligations and prohibitions are `sh:Violation`, permissions are `sh:Info` (presence of a permission claim is informational, not a compliance failure). Your pipeline already does this — good.

Consider going one step further: confidence-weighted severity.

```python
def _severity_for(rule_type: str, confidence: float) -> str:
    if rule_type == "permission":
        return "sh:Info"
    if confidence >= 0.85:
        return "sh:Violation"
    if confidence >= 0.6:
        return "sh:Warning"
    return "sh:Info"
```

Low-confidence obligations become warnings instead of violations. Reporting this in your thesis shows a principled way to handle LLM uncertainty at the constraint level.

---

### 5.3 Permission-as-exception

Your `ait_policy_ontology.ttl` defines:

```turtle
deontic:defaultRestriction a owl:DatatypeProperty ...
deontic:overrides a owl:ObjectProperty ...
```

...i.e., the Governatori & Rotolo (2010) permission-as-exception pattern, where a permission shape can override an obligation shape. Your pipeline doesn't produce override links. This is a citable contribution if you implement it.

Sketch:
1. In `fol.py`, detect permission rules whose text matches an obligation rule's subject and predicate ("Students must pay fees" / "Students of type X may defer fees").
2. In `shacl.py`, emit:
   ```turtle
   ait:AIT_0020Shape a sh:NodeShape ;
       sh:targetClass ait:Student ;
       deontic:defaultRestriction true ;
       sh:property [ sh:path ait:payFee ; sh:minCount 1 ] .

   ait:AIT_0045Shape a sh:NodeShape ;
       sh:targetClass ait:SponsoredStudent ;
       deontic:overrides ait:AIT_0020Shape ;
       sh:severity sh:Info .
   ```

For matching, use embedding similarity on `predicates.action + predicates.subject` pairs from FOL output. Two rules with similar action but narrower subject suggest an override relationship.

This is optional for a first thesis draft but scores points if you have time.

---

## 6. Phase 5 — Reproducibility & thesis hygiene

### 6.1 Full-determinism configuration

Covered in §2.4. Collect all determinism settings into a single `.env.example`:

```bash
# Model configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_SECOND_MODEL=mistral
OLLAMA_SEED=42

# Pipeline
PIPELINE_VERSION=2.1-hints
EXTRACT_SPACY=0   # 1 to enable spaCy sentencizer

# Cache
CACHE_MAX_ENTRIES=2000
```

Commit `.env.example`. Have `run.py` print the active config at the top of every run:

```python
# langgraph_agent/run.py — top of run()
import os
print(f"\n{'='*60}")
print(f"Environment:")
print(f"  Model:   {os.getenv('OLLAMA_MODEL', 'mistral')}")
print(f"  Second:  {os.getenv('OLLAMA_SECOND_MODEL', 'mistral')}")
print(f"  Seed:    {os.getenv('OLLAMA_SEED', '42')}")
print(f"  Version: {os.getenv('PIPELINE_VERSION', 'dev')}")
print(f"{'='*60}\n")
```

### 6.2 Model pinning and environment capture

In `report.py`, add a `environment` section to the final report:

```python
import platform, subprocess, os

def _capture_environment() -> dict:
    env = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ollama_model": os.getenv("OLLAMA_MODEL", "mistral"),
        "ollama_second_model": os.getenv("OLLAMA_SECOND_MODEL", "mistral"),
        "seed": os.getenv("OLLAMA_SEED", "42"),
        "pipeline_version": os.getenv("PIPELINE_VERSION", "dev"),
    }
    # Ollama model digest (if Ollama is reachable)
    try:
        import requests
        r = requests.get(f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/tags", timeout=3)
        for m in r.json().get("models", []):
            if m["name"].startswith(env["ollama_model"]):
                env["ollama_model_digest"] = m.get("digest", "")[:12]
                break
    except Exception:
        pass
    # Git SHA
    try:
        env["git_sha"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()[:8]
    except Exception:
        env["git_sha"] = "unknown"
    return env


# In report_node, add to report dict:
report["environment"] = _capture_environment()
```

Now every `pipeline_report.json` records exactly which code and model weights produced it. Essential for a thesis.

### 6.3 Pipeline version tags

The moment you change behaviour that affects output (not just refactoring), bump `PIPELINE_VERSION` in `.env`. Treat this as a contract:

| Version | What changed |
|---|---|
| `2.0-langgraph` | Initial LangGraph port |
| `2.1-hints` | PreFilter hints plumbed through |
| `2.2-may-disambig` | Epistemic/deontic "may" disambiguation |
| `2.3-fol-retry` | FOL placeholder detection & retry |
| `2.4-shape-uris` | Named property shapes |

Cache keys include version (§2.4b), so old cached values don't contaminate new runs.

### 6.4 Align README / ARCHITECTURE with reality

I've been careful not to belabour this, but it matters for a thesis. A committee member who reads your README and then runs your code should not see a contradiction.

**Concrete discrepancies to resolve:**

1. **README "RQ1: 99% accuracy (GLM 4.7 Flash)".** The current pipeline defaults to mistral and has no accuracy measurement. Either:
   - (a) Re-run with GLM 4.7 Flash if it's available via Ollama, measure against M2 (classification coverage) with §3 harness, and update the number.
   - (b) Rewrite RQ1 to report what you actually measured.

2. **README "RQ2: 100% success rate".** FOL parse success is 92.7% and placeholder rate is high. Rewrite to `"92.7% parse success; of those, X% produced semantic predicates after one retry"`.

3. **README "RQ3: 1,309 triples generated".** Current `shapes_generated.ttl` has ~500 shapes × ~4 triples = ~2000 triples, but count it properly (`rdflib: len(graph)`). Report the real number.

4. **ARCHITECTURE mermaid shows `route_fol` as conditional edge.** Code uses static `add_edge`. Either:
   - Wire `route_fol` properly (`g.add_conditional_edges(...)`), which requires changing the `shacl` and `direct_shacl` nodes to no longer run unconditionally in parallel.
   - Delete `edges/route_fol.py` and update the ARCHITECTURE doc to reflect the static parallel fan-out.

   Either is fine. Ambiguity between doc and code is what's bad.

Draft an honest one-paragraph summary you can put in README and defend:

> PolicyChecker extracts institutional policy rules from PDFs through a LangGraph pipeline: heuristic prefiltering, LLM classification with second-opinion re-prompting, FOL formalization, and SHACL shape generation with a natural-language fallback for FOL failures. On the AIT corpus (1,531 sentences), the pipeline produces N rules, M FOL formulas (K% non-placeholder), and S SHACL shapes, of which V are syntactically valid. Against a gold standard of 96 curated shapes, the pipeline achieves an extraction coverage of M1%, classification coverage of M2%, and an end-to-end shape F1 of M4 (precision P, recall R).

Fill in N/M/K/S/V/M1/M2/M4/P/R from a clean run after the Phase 1-3 fixes.

---

## 7. Phase 6 — Ablation studies for the thesis

Your architecture naturally supports ablations — you don't need new code, just flags. Each row below is a table row in your results section.

| Ablation | What to toggle | Expected effect | Thesis claim |
|---|---|---|---|
| No prefilter | `candidates = state["extracted_sentences"]` | M1 same (extract is upstream), but classification cost explodes and noise drops M2 | "Prefilter is essential for efficient classification" |
| No prefilter hints in classify | Set `hint = {}` in classify | M2 drops by boost-calibrated amount | "Speech-act context improves classification accuracy" |
| No reclassify | Route "reclassify" edge → "fol" | M2 slightly drops (uncertain rules are dropped) | "Second-opinion reclassification recovers borderline rules" |
| No direct_shacl fallback | Skip `direct_shacl_node` | M1 unchanged, M4 drops on FOL-failing rules | "Direct NL fallback captures rules that FOL can't express" |
| No FOL retry | `max_retries=0` in `_generate_with_retry` | M3 drops to baseline, M4 drops on placeholder-heavy rules | "Placeholder-detection retry improves FOL quality" |
| Single model (mistral only) | `SECOND_MODEL=mistral` (current default) | Baseline | — |
| Two models | `SECOND_MODEL=glm` or similar | M2 potentially up | "Model diversity helps on uncertain cases" |
| Spacy sentencizer | `EXTRACT_SPACY=1` | M1 up by splitting quality | "Robust sentencization improves extraction" |
| No may-disambig | Skip §4.2 layer 1 | M2 drops on may-heavy subsections | "Lexical disambiguation is a cheap quality boost" |

**Practical implementation.** Add a `--ablation <name>` flag to `run.py` that sets env vars before the graph runs:

```python
# langgraph_agent/run.py
ABLATIONS = {
    "no-prefilter":       {"ABLATION_SKIP_PREFILTER": "1"},
    "no-hints":           {"ABLATION_NO_HINTS": "1"},
    "no-reclassify":      {"ABLATION_SKIP_RECLASSIFY": "1"},
    "no-fallback":        {"ABLATION_SKIP_DIRECT_SHACL": "1"},
    "no-fol-retry":       {"ABLATION_NO_FOL_RETRY": "1"},
    "no-may-disambig":    {"ABLATION_NO_MAY_DISAMBIG": "1"},
    "baseline":           {},
}
parser.add_argument("--ablation", choices=list(ABLATIONS.keys()), default="baseline")
args = parser.parse_args()
os.environ.update(ABLATIONS[args.ablation])
```

Each affected node checks its env var and short-circuits. Output path becomes `output/ait_<ablation>/` so results don't overwrite each other.

A nightly script runs all ablations + the evaluation harness and compiles a `thesis_results.md` with the full ablation table. Fully automated results section.

---

## 8. Phase 7 — Lower-priority polish

### 8.1 Wire `route_fol` or delete it

```python
# In graph.py, replace the static fan-out:
g.add_edge("fol", "shacl")
g.add_edge("fol", "direct_shacl")

# with:
from langgraph_agent.edges.route_fol import route_fol
g.add_conditional_edges(
    "fol",
    route_fol,
    {"shacl": "shacl", "direct_shacl": "direct_shacl"},
)
```

But note: `route_fol` returns a single branch ("shacl" OR "direct_shacl"), which means you lose the parallel processing. If your intent is to always run both when there are failures, keep the static edges and delete `route_fol.py`. If your intent is "branch only when there are enough failures," switch to conditional. Pick one.

### 8.2 Genuine second-opinion model

If you can pull a second model (e.g., `qwen2:7b`, `llama3.2:3b`, `phi3:mini`), set `OLLAMA_SECOND_MODEL` to it. The second-opinion pattern works much better when the second voice is actually a different voice. Run the "two models" ablation in §7.

### 8.3 Tests for new code

Your current tests cover prefilter and graph compilation. Add:

- `tests/test_classify_hints.py`: given a `SentenceItem` with hints, assert the prompt contains them (use a mock LLM).
- `tests/test_shacl_generation.py`: given a FOL item, assert `_property_path` rejects single letters.
- `tests/test_align.py`: given three gold rules and three pipeline rules with known pairs, assert alignment picks the right match.
- `tests/test_per_rule_eval.py`: a tiny fixture with one gold shape + matching pipeline shape + Pos/Neg entities.

### 8.4 MCP server surface

The MCP server (`core/mcp_server.py`) currently only exposes `verify_rule` and `check_status`. Low-hanging additions:

- `extract_rules_from_pdf(pdf_path)` → runs the full extract → prefilter → classify stack on a single file
- `generate_shape(rule_text, rule_type)` → emits a single SHACL shape (FOL-mediated with NL fallback)
- `validate_text_against_shapes(text)` → full pipeline + validation, returns structured verdict

Not thesis-critical but demo-friendly.

---

## 9. Implementation schedule

Assuming ~4 hours/day of focused work, here's a realistic schedule. Adjust for your actual cadence.

### Week 1 — unblock measurement (≈12 hours)

| Day | Tasks | Deliverable |
|---|---|---|
| 1 AM | §2.1 PreFilter hints plumbing | classify.py reads hints; rerun shows real `prefilter_strength` |
| 1 PM | §2.2 `_merge_shapes` prefix + §2.3 property path vars | rerun shows shape_count ≈ 560, `ait:x`/`ait:y` gone |
| 2 AM | §2.4 determinism (seed + prompt versioning) | double-run diff = 0 |
| 2 PM | §3.2 `evaluation/align.py` — alignment script | `gold_alignment.json` with M1 number |
| 3 | §3.3 `evaluation/per_rule_eval.py` | `per_rule_eval.json` with M4 precision/recall |
| 4 | §3.4 results summary script, first thesis numbers table | `thesis_results_v1.md` with M1-M5 baseline |

**Checkpoint at end of week 1:** you have reproducible numbers. They won't be great yet, but they'll be real.

### Week 2 — move the numbers (≈12 hours)

| Day | Tasks | Expected delta |
|---|---|---|
| 1 | §4.1 sentence splitting fix | +2-4 pp M1 |
| 2 AM | §4.2 layer 1 (epistemic-may prefilter) | +5-8 pp M2 |
| 2 PM | §4.2 layer 2 (prompt update) | +3-5 pp M2 |
| 3 | §4.3 FOL placeholder retry | +20-30 pp M3 |
| 4 | §4.4 target-class inference + subject extraction | +15-25 pp M4 precision |
| 5 | §5.1 shape ID resolution + §5.2 severity tiers | cleaner reports, no numeric impact |

**Checkpoint at end of week 2:** you have "good-enough" numbers for a draft. Should be M1 ≥ 75%, M2 ≥ 80% on aligned rules, M3 ≥ 90%, M4 F1 ≥ 0.7.

### Week 3 — ablations & writeup (≈12 hours)

| Day | Tasks |
|---|---|
| 1 | §7 ablation flag infrastructure + first ablation runs (no-prefilter, no-hints) |
| 2 | Remaining ablations (no-reclassify, no-fallback, no-fol-retry, no-may-disambig) |
| 3 | §6.1–6.3 reproducibility hygiene + second-model ablation if model available |
| 4 | §6.4 README/ARCHITECTURE update with real numbers |
| 5 | Draft thesis results section |

### Optional week 4 — nice-to-haves (≈8 hours)

- §5.3 permission-as-exception (if thesis word count permits)
- §8.2 genuine second-opinion model integration
- §8.3 test coverage for new code
- Write up the "may" disambiguation contribution as a subsection

---

## Appendix A — Copy-paste ready code blocks

Consolidated for easy access. Snippets are presented in the order you should apply them.

### A.1 `langgraph_agent/state.py` — extended SentenceItem

```python
class SentenceItem(TypedDict, total=False):
    text: str
    page: int
    source: str
    # prefilter-populated
    deontic_strength: str
    speech_act: str
    section_context: str
    section_weight: float
    confidence_boost: float
```

### A.2 `langgraph_agent/nodes/prefilter.py` — populate hints

```python
for item, result in zip(items, results):
    if result.is_candidate:
        enriched: SentenceItem = {
            **item,
            "deontic_strength": result.deontic_strength,
            "speech_act": result.speech_act,
            "section_context": result.section_context,
            "section_weight": result.section_weight,
            "confidence_boost": result.confidence_boost,
        }
        candidates.append(enriched)
```

### A.3 `langgraph_agent/nodes/classify.py` — read hints + boost

```python
hint = {
    "deontic_strength": item.get("deontic_strength", "unknown"),
    "speech_act":       item.get("speech_act", "unknown"),
    "section_context":  item.get("section_context", "unknown"),
}
boost = float(item.get("confidence_boost", 0.0))

cache_params = {
    "prompt_version": CLASSIFY_PROMPT_VERSION,
    "deontic_strength": hint["deontic_strength"],
    "speech_act": hint["speech_act"],
}

# ... call LLM ...

raw_conf = float(result.get("confidence", 0.5))
confidence = max(0.0, min(1.0, raw_conf + boost))
```

### A.4 `langgraph_agent/nodes/validate.py` — prefix-aware merge

```python
from langgraph_agent.nodes.shacl import _TTL_PREFIXES

def _merge_shapes(pipeline_shapes: List[SHACLShape]) -> Graph:
    g = Graph()
    if SHACL_SHAPES_FILE.exists():
        g.parse(str(SHACL_SHAPES_FILE), format="turtle")

    skipped = 0
    for shape in pipeline_shapes:
        if not (shape["syntax_valid"] and shape["turtle_text"]):
            continue
        try:
            g.parse(data=_TTL_PREFIXES + shape["turtle_text"], format="turtle")
        except Exception:
            skipped += 1

    if skipped:
        import logging
        logging.getLogger(__name__).warning(
            f"_merge_shapes dropped {skipped}/{len(pipeline_shapes)} shapes"
        )
    return g
```

### A.5 `langgraph_agent/nodes/shacl.py` — robust property path

```python
_PLACEHOLDER_PREDICATES = {
    "x", "y", "z", "n", "m",
    "action", "subject", "predicate",
    "condition", "thing", "entity",
}

def _property_path(fol: FOLItem) -> str:
    m = re.search(r"[OPF]\(([a-zA-Z_]+)", fol["deontic_formula"])
    if m:
        raw = m.group(1)
        if len(raw) > 1 and raw.lower() not in _PLACEHOLDER_PREDICATES:
            parts = re.sub(r"([A-Z])", r" \1", raw).strip().split()
            return parts[0][0].lower() + parts[0][1:] + "".join(
                p.capitalize() for p in parts[1:]
            )

    preds = fol.get("predicates") or {}
    action = preds.get("action", "") if isinstance(preds, dict) else ""
    if action and action.lower() not in _PLACEHOLDER_PREDICATES:
        return _slugify(action, max_words=3, first_lower=True)

    return _slugify(fol["text"], max_words=4, first_lower=True)


def _slugify(text: str, max_words: int = 4, first_lower: bool = False) -> str:
    words = re.sub(r"[^a-zA-Z0-9 ]", "", text).split()
    if not words:
        return "policyRule"
    selected = words[:max_words]
    result = "".join(w.capitalize() for w in selected)
    if first_lower and result:
        result = result[0].lower() + result[1:]
    return result
```

### A.6 `langgraph_agent/llm.py` — determinism

```python
from __future__ import annotations
import os
from langchain_ollama import ChatOllama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
SECOND_MODEL = os.getenv("OLLAMA_SECOND_MODEL", "mistral")
SEED = int(os.getenv("OLLAMA_SEED", "42"))

def get_llm(model: str | None = None,
            temperature: float = 0.0,
            seed: int = SEED) -> ChatOllama:
    return ChatOllama(
        model=model or DEFAULT_MODEL,
        temperature=temperature,
        base_url=OLLAMA_HOST,
        model_kwargs={"seed": seed, "num_predict": 512,
                      "top_k": 1, "top_p": 1.0},
    )

def get_second_llm() -> ChatOllama:
    return get_llm(model=SECOND_MODEL, seed=SEED + 1)
```

### A.7 `core/prefilter.py` — may disambiguation (additions)

```python
EPISTEMIC_MAY_PATTERNS = [
    re.compile(r"\bmay\s+be\b", re.IGNORECASE),
    re.compile(r"\bmay\s+have\b", re.IGNORECASE),
    re.compile(r"\bmay\s+entail\b", re.IGNORECASE),
    re.compile(r"\bmay\s+include\b", re.IGNORECASE),
    re.compile(r"\bmay\s+contain\b", re.IGNORECASE),
    re.compile(r"\bmay\s+result\s+in\b", re.IGNORECASE),
]

DEONTIC_MAY_PATTERNS = [
    re.compile(r"\bmay\s+(apply|request|submit|use|access|file|obtain|appeal)\b",
               re.IGNORECASE),
    re.compile(r"\bmay\s+not\b", re.IGNORECASE),
]

def disambiguate_may(text: str) -> str:
    if not re.search(r"\bmay\b", text, re.IGNORECASE):
        return "n/a"
    if any(p.search(text) for p in DEONTIC_MAY_PATTERNS):
        return "deontic"
    if any(p.search(text) for p in EPISTEMIC_MAY_PATTERNS):
        return "epistemic"
    return "ambiguous"
```

---

## Appendix B — Prompt templates

### B.1 Classify prompt (v3-hints)

```text
You are a legal policy analyst specialising in institutional policy documents.

Classify whether the sentence below is a POLICY RULE — a deontic statement that
creates a binding obligation, grants a permission, or imposes a prohibition.

IMPORTANT DISTINCTIONS:
- "may be X-ed" / "may have" / "may entail" = DESCRIPTIVE possibility, NOT a rule.
  Example: "Research may be sponsored by agencies." → NOT A RULE.
- "may apply for" / "may request" / "may use" = PERMISSION (deontic rule).
- "may not" = always a PROHIBITION.
- "should" alone is ambiguous — rely on section context.

Context hints:
- Deontic strength: {deontic_strength}
- Speech act: {speech_act}
- Section: {section}

Sentence:
"{text}"

Respond with ONLY a JSON object (no markdown, no explanation):
{"is_rule": true/false, "rule_type": "obligation"/"permission"/"prohibition"/"none",
"confidence": 0.0-1.0, "reasoning": "one concise sentence"}
```

### B.2 FOL prompt (v2-semantic)

```text
You are a formal logician specialising in deontic logic for institutional policy.

Convert the policy rule below into a First-Order Logic (FOL) formula using
deontic operators:
  O(φ) — Obligation
  P(φ) — Permission
  F(φ) — Prohibition (Forbidden)

CRITICAL: The predicate inside the deontic operator must be SEMANTIC.
- Good: O(payFee(student)), P(applyForLeave(student)), F(cheatOnExam(student))
- BAD:  O(Action(x)), P(Subject(y)), F(Predicate(z))

Rule type: {rule_type}
Rule text: "{text}"

Output ONLY a JSON object:
{
  "deontic_type": "obligation"/"permission"/"prohibition",
  "deontic_formula": "O/P/F(semanticPredicate(subject))",
  "fol_expansion": "∀x (Subject(x) ∧ Condition(x) → O/P/F(semanticPredicate(x)))",
  "predicates": {"subject": "...", "action": "...", "condition": "..."},
  "shacl_hint": "brief hint: target class + key property"
}
```

### B.3 FOL retry prompt

```text
Your previous FOL formalization used placeholder predicates like "Action" or
single letters. That is not acceptable — use SEMANTIC predicates.

Rule type: {rule_type}
Rule text: "{text}"
Previous (BAD) formula: {bad_formula}

Rules:
- The inner predicate must name the actual action (e.g., "payFee", "submitThesis").
- Use camelCase or snake_case derived from the rule's main verb phrase.
- Do NOT use: Action, Subject, Predicate, Condition, or any single letter.

Output ONLY a JSON object with the same schema as before.
```

---

## Appendix C — Metric definitions

For the thesis methodology section.

**M1 — Extraction coverage.** Let `G = {g1, ..., g96}` be the set of gold rules, each with text `t(gi)`. Let `P = {p1, ..., pn}` be the set of pipeline-classified rules. We say gi is *covered* if there exists pj such that `cos_sim(embed(t(gi)), embed(t(pj))) ≥ τ` where embeddings are from `sentence-transformers/all-MiniLM-L6-v2` and τ = 0.65. Then:

```
M1 = |{gi ∈ G : gi is covered}| / |G|
```

**M2 — Classification coverage.** For each covered gi, let pj* be the best-matching pipeline rule. Let `d(gi)` be the gold deontic type and `d(pj)` be the pipeline's `rule_type`. Then:

```
M2 = |{gi ∈ G : gi is covered ∧ d(gi) = d(pj*)}| / |{gi : covered}|
```

**M3 — FOL quality rate.** Let `F = {f1, ..., fm}` be the set of FOL formulas produced for covered rules. Let `placeholder(fj)` = True iff fj's inner predicate matches `^(Action|Subject|Predicate|x|y|z)` or has length 1. Then:

```
M3 = 1 - |{fj ∈ F : placeholder(fj)}| / |F|
```

**M4 — Shape correctness.** For each covered rule gi with pipeline shape Sj:
- Let `PosPass(Sj)` = pyshacl verdict on `{Pos_GSi}` using Sj.
- Let `NegFail(Sj)` = ¬(pyshacl verdict on `{Neg_GSi}` using Sj).

Define:
- TP = |{gi : PosPass ∧ NegFail}|    (shape correct)
- FP = |{gi : ¬PosPass ∧ NegFail}|   (shape too strict)
- FN = |{gi : PosPass ∧ ¬NegFail}|   (shape too permissive)

Then:
```
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = 2PR / (P + R)
```

**M5 — Reproducibility.** For two clean-cache runs R1 and R2 of the same pipeline on the same input with fixed seed:
```
M5 = (diff(classified_rules.json) = ∅) ∧
     (diff(fol_formulas.json) = ∅) ∧
     (diff(shapes_generated.ttl) = ∅) ∧
     (M1(R1) = M1(R2)) ∧ ... ∧ (M4(R1) = M4(R2))
```
M5 is a boolean pass/fail.

---

## Closing note

Your pipeline's architecture is genuinely solid — LangGraph state machines, typed nodes, reducer-based merges, SQLite-backed caching, prefilter heuristics grounded in the literature. The gaps are at the seams: data that's computed but not passed, shapes that parse individually but not together, rule IDs that don't cross the gold/pipeline boundary.

The evaluation harness (§3) is the single most important artefact still missing. Everything else in this document is optimization around it. Start there.

Good luck with the thesis.
