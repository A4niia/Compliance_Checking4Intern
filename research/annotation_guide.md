# Human Annotation Guide

## Purpose

This guide helps human annotators label policy rules to create a gold standard dataset for evaluating LLM classification performance.

---

## Task Overview

You will review text excerpts from AIT policy documents and determine:

1. **Is this a policy rule?** (Yes/No)
2. **What type?** (Obligation/Permission/Prohibition)
3. **Confidence level** (1-5 scale)

---

## What is a Policy Rule?

A policy rule is a statement that:

- Prescribes, permits, or prohibits behavior
- Contains deontic markers (must, shall, may, cannot, etc.)
- Specifies conditions and actions
- Applies to specific subjects (students, employees, etc.)

### Examples

| Text | Is Rule? | Type | Why |
|------|----------|------|-----|
| "Students must pay fees before registration" | ✅ Yes | Obligation | "must" + specific action |
| "Employees may work remotely on Fridays" | ✅ Yes | Permission | "may" + allowed action |
| "Smoking is prohibited in all buildings" | ✅ Yes | Prohibition | "prohibited" + forbidden action |
| "AIT was founded in 1959" | ❌ No | N/A | Factual statement, no prescription |
| "The library has 50,000 books" | ❌ No | N/A | Description, not a rule |

---

## Deontic Markers

### Obligation Words

- must, shall, required, have to, need to, obligated
- "is required to", "are expected to", "will be"

### Permission Words

- may, can, allowed, permitted, entitled
- "is eligible to", "has the right to"

### Prohibition Words

- must not, shall not, cannot, prohibited, forbidden
- "is not allowed", "are not permitted"

---

## Annotation Process

### Step 1: Read the Text

Read the entire text excerpt carefully.

### Step 2: Identify Deontic Markers

Look for words indicating obligation, permission, or prohibition.

### Step 3: Classify

| Question | Answer Options |
|----------|----------------|
| Is this a rule? | Yes / No |
| If yes, what type? | Obligation / Permission / Prohibition |
| Confidence (1-5) | 1=Very Unsure, 5=Very Confident |

### Step 4: Document Reasoning

Write a brief explanation for your decision.

---

## Edge Cases

### Implicit Rules

Some rules don't use explicit deontic markers:

- "Late submissions will be penalized" → Implicit **Prohibition**
- "Students are responsible for..." → Implicit **Obligation**

### Conditional Rules

Rules with conditions are still rules:

- "If grades drop below 2.0, students must..." → **Obligation** with condition

### Multiple Rules

Some sentences contain multiple rules. Annotate the primary rule.

---

## Annotation Template

```json
{
  "id": "GS-001",
  "text": "Students must pay fees before registration",
  "human_annotation": {
    "is_rule": true,
    "rule_type": "obligation",
    "confidence": 5,
    "annotator": "YOUR_NAME",
    "reasoning": "Contains 'must' marker with clear action requirement"
  }
}
```

---

## Quality Guidelines

1. **Be consistent** - Apply the same criteria across all annotations
2. **When in doubt, mark as rule** - Err on the side of inclusion
3. **Focus on prescriptive content** - Ignore procedural descriptions
4. **Document uncertainty** - Use confidence scores honestly

---

## Calculating Agreement

After annotation, we calculate Cohen's Kappa:

```python
from sklearn.metrics import cohen_kappa_score

human_labels = [1, 1, 0, 1, 0, ...]  # Your annotations
llm_labels = [1, 1, 1, 1, 0, ...]    # LLM predictions

kappa = cohen_kappa_score(human_labels, llm_labels)
print(f"Cohen's Kappa: {kappa:.3f}")
```

**Interpretation:**

| Kappa | Agreement |
|-------|-----------|
| < 0.20 | Poor |
| 0.21-0.40 | Fair |
| 0.41-0.60 | Moderate |
| 0.61-0.80 | Substantial |
| 0.81-1.00 | Almost Perfect |

---

## Getting Started

1. Open `research/gold_standard_template.json`
2. For each rule, add your `human_annotation` object
3. Save periodically
4. Run `python scripts/calculate_kappa.py` when done
