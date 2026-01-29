# Thesis Agent System - Policy Rule Extraction Template
# This script and spreadsheet help extract policy rules from AIT P&P documents

import pandas as pd
from pathlib import Path
from datetime import datetime
import json

# ============================================================
# RULE EXTRACTION TEMPLATE
# ============================================================

EXTRACTION_TEMPLATE = {
    "rule_id": "",           # e.g., "FB-6-1-1-R001"
    "source_document": "",    # e.g., "FB-6-1-1 Credit Policy"
    "page_number": "",        # Page in PDF
    "section": "",            # e.g., "III.1.(2)"
    "original_text": "",      # Exact text from document
    "simplified_text": "",    # Your simplified interpretation
    
    # Annotation Dimensions (from your annotation scheme)
    "annotations": {
        "syntactic_structure": "",     # simple | compound | complex | compound-complex
        "clause_count": 0,             # 1, 2, 3, 4+
        "nesting_depth": 0,            # 0, 1, 2, 3+
        
        "deontic_marker": "",          # must | shall | may | should | prohibited | none
        "deontic_type": "",            # obligation | prohibition | permission | recommendation
        
        "quantification": "",          # universal | existential | negated_universal | implicit
        "quantifier_words": [],        # List of quantifiers found
        
        "conditional_structure": "",   # none | single | conjunctive | disjunctive | nested
        "has_exception": False,        # True if "unless", "except", etc.
        
        "temporal_elements": [],       # List: deadline, duration, sequence, frequency
        "temporal_expressions": [],    # Actual temporal phrases found
        
        "entity_types": [],            # student, staff, department, etc.
        "relationship_complexity": "", # direct | mediated | multi-hop
        
        "ambiguity_indicators": [],    # vague terms, implicit knowledge, undefined refs
    },
    
    # Formalization Attempt
    "formalization": {
        "attempt_date": "",
        "time_spent_minutes": 0,
        "confidence_1_5": 0,           # 1=very uncertain, 5=very confident
        
        "outcome": "",                 # SUCCESS | PARTIAL | FAILURE-LINGUISTIC | FAILURE-EXPRESSIVE | FAILURE-KNOWLEDGE
        "fol_statement": "",           # The FOL if successful
        "shacl_implemented": False,    # True if SHACL shape created
        
        "failure_reason": "",          # If failed, explain why
        "blocking_features": [],       # What linguistic features caused issues
        "assumptions_made": [],        # Any assumptions required
    },
    
    # Verification (for Direction 3)
    "verification": {
        "shacl_shape_file": "",        # Path to SHACL file
        "shacl2fol_output": "",        # Path to FOL output
        "equivalence_result": "",      # EQUIVALENT | STRONGER | WEAKER | INCOMPARABLE
        "counterexample": "",          # If not equivalent
        "verified_date": "",
    },
    
    # Metadata
    "notes": "",
    "advisor_reviewed": False,
    "review_date": "",
    "review_comments": "",
}


def create_extraction_spreadsheet(output_path: str = "research/policy_rules_corpus.xlsx"):
    """Create an Excel spreadsheet for rule extraction with proper column structure."""
    
    # Flatten the template for spreadsheet columns
    columns = [
        # Core Info
        "rule_id", "source_document", "page_number", "section", 
        "original_text", "simplified_text",
        
        # Syntactic
        "ann_syntactic_structure", "ann_clause_count", "ann_nesting_depth",
        
        # Deontic
        "ann_deontic_marker", "ann_deontic_type",
        
        # Quantification
        "ann_quantification", "ann_quantifier_words",
        
        # Conditional
        "ann_conditional_structure", "ann_has_exception",
        
        # Temporal
        "ann_temporal_elements", "ann_temporal_expressions",
        
        # Entities
        "ann_entity_types", "ann_relationship_complexity",
        
        # Ambiguity
        "ann_ambiguity_indicators",
        
        # Formalization
        "form_attempt_date", "form_time_spent_min", "form_confidence",
        "form_outcome", "form_fol_statement", "form_shacl_implemented",
        "form_failure_reason", "form_blocking_features", "form_assumptions",
        
        # Verification
        "ver_shacl_file", "ver_shacl2fol_output", "ver_equivalence_result",
        "ver_counterexample", "ver_verified_date",
        
        # Metadata
        "notes", "advisor_reviewed", "review_date", "review_comments"
    ]
    
    # Create empty dataframe
    df = pd.DataFrame(columns=columns)
    
    # Add some example rows for guidance
    example_rows = [
        {
            "rule_id": "FB-6-1-1-R001",
            "source_document": "FB-6-1-1 Credit Policy",
            "page_number": "3",
            "section": "III.1.(2)",
            "original_text": "Self-support students who have not paid tuition fees within two weeks of the fee due date are not eligible for course registration.",
            "simplified_text": "Self-support students must pay tuition fees to be enrolled.",
            "ann_syntactic_structure": "complex",
            "ann_clause_count": 2,
            "ann_nesting_depth": 1,
            "ann_deontic_marker": "must (implied)",
            "ann_deontic_type": "obligation",
            "ann_quantification": "universal",
            "ann_quantifier_words": "students (implicit all)",
            "ann_conditional_structure": "single",
            "ann_has_exception": False,
            "ann_temporal_elements": "deadline",
            "ann_temporal_expressions": "within two weeks",
            "ann_entity_types": "student, fee, registration",
            "ann_relationship_complexity": "mediated",
            "ann_ambiguity_indicators": "",
            "form_attempt_date": "2026-01-29",
            "form_time_spent_min": 15,
            "form_confidence": 4,
            "form_outcome": "SUCCESS",
            "form_fol_statement": "∀x,o [Student(x) ∧ Type(x,'Self-Support') ∧ Enrolled(x) ∧ Obligation(o) ∧ hasObligation(x,o) ∧ Type(o,'TuitionFee') ∧ ¬Paid(o) → Violation(x)]",
            "form_shacl_implemented": True,
            "form_failure_reason": "",
            "form_blocking_features": "",
            "form_assumptions": "Two weeks simplified to 14 days",
            "ver_shacl_file": "ait-policy-prototype/ait-shacl-rules.ttl",
            "ver_shacl2fol_output": "",
            "ver_equivalence_result": "",
            "ver_counterexample": "",
            "ver_verified_date": "",
            "notes": "Existing implementation in prototype",
            "advisor_reviewed": False,
            "review_date": "",
            "review_comments": ""
        },
        {
            "rule_id": "FS-1-1-1-R001",
            "source_document": "FS-1-1-1 Campus Accommodation",
            "page_number": "",
            "section": "VII",
            "original_text": "Pets are not allowed in student accommodation. The fine for non-compliance is Baht 2,000.",
            "simplified_text": "Students residing in campus accommodation must not have pets.",
            "ann_syntactic_structure": "simple",
            "ann_clause_count": 1,
            "ann_nesting_depth": 0,
            "ann_deontic_marker": "not allowed",
            "ann_deontic_type": "prohibition",
            "ann_quantification": "universal",
            "ann_quantifier_words": "pets (all)",
            "ann_conditional_structure": "none",
            "ann_has_exception": False,
            "ann_temporal_elements": "",
            "ann_temporal_expressions": "",
            "ann_entity_types": "student, pet, accommodation",
            "ann_relationship_complexity": "mediated",
            "ann_ambiguity_indicators": "",
            "form_attempt_date": "",
            "form_time_spent_min": 0,
            "form_confidence": 0,
            "form_outcome": "",
            "form_fol_statement": "",
            "form_shacl_implemented": False,
            "form_failure_reason": "",
            "form_blocking_features": "",
            "form_assumptions": "",
            "ver_shacl_file": "",
            "ver_shacl2fol_output": "",
            "ver_equivalence_result": "",
            "ver_counterexample": "",
            "ver_verified_date": "",
            "notes": "Example from Research_Enhancement_Plan.md",
            "advisor_reviewed": False,
            "review_date": "",
            "review_comments": ""
        }
    ]
    
    df = pd.concat([df, pd.DataFrame(example_rows)], ignore_index=True)
    
    # Save to Excel
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False, engine='openpyxl')
    
    print(f"Created extraction spreadsheet: {output_path}")
    print(f"Columns: {len(columns)}")
    print(f"Example rows: {len(example_rows)}")
    
    return df


def generate_annotation_codebook(output_path: str = "research/annotation_codebook.md"):
    """Generate a detailed annotation codebook for consistent rule annotation."""
    
    codebook = """# Policy Rule Annotation Codebook
## Version 1.0 - Single Annotator with Advisor Sampling

This codebook provides guidelines for annotating policy rules extracted from AIT P&P documents.

---

## 1. Syntactic Structure

### 1.1 Sentence Type
| Value | Definition | Example |
|-------|------------|---------|
| `simple` | Single independent clause | "Pets are not allowed." |
| `compound` | Two+ independent clauses joined by coordinating conjunction | "Students must pay fees, and they must attend orientation." |
| `complex` | Independent clause + dependent clause(s) | "Students who do not pay fees will be suspended." |
| `compound-complex` | Multiple independent and dependent clauses | "If students fail to pay, they will be suspended, but they may appeal." |

### 1.2 Clause Count
Count the number of clauses (verb phrases) in the sentence.
- Simple sentence: 1
- "If X then Y": 2
- "A and B and C": 3

### 1.3 Nesting Depth
Count how many levels of subordinate clauses exist.
- "Students must pay." → 0
- "Students who are enrolled must pay." → 1
- "Students who have obligations that are overdue must pay." → 2

---

## 2. Deontic Markers

### 2.1 Deontic Marker
| Marker | Examples |
|--------|----------|
| `must` | must, is required to, has to, shall |
| `shall` | shall (often legal/formal) |
| `may` | may, can, is permitted, is allowed |
| `should` | should, ought to, is advised, is recommended |
| `prohibited` | must not, shall not, is prohibited, cannot, not allowed |
| `none` | No explicit deontic marker |

### 2.2 Deontic Type
| Type | Meaning |
|------|---------|
| `obligation` | Something MUST be done |
| `prohibition` | Something MUST NOT be done |
| `permission` | Something MAY be done (optional) |
| `recommendation` | Something SHOULD be done (not mandatory) |

---

## 3. Quantification

### 3.1 Quantification Type
| Value | Definition | Example |
|-------|------------|---------|
| `universal` | Applies to ALL entities | "All students must...", "Every student..." |
| `existential` | Applies to SOME entities | "At least one advisor...", "Some courses..." |
| `negated_universal` | No entities | "No student may...", "None of the..." |
| `implicit` | Quantification is implied | "Students must..." (implies all students) |

### 3.2 Quantifier Words
List actual words used: all, every, each, any, some, no, none, at least, etc.

---

## 4. Conditional Structure

### 4.1 Conditional Type
| Value | Definition | Example |
|-------|------------|---------|
| `none` | No conditional | "Pets are not allowed." |
| `single` | One condition | "If X, then Y" |
| `conjunctive` | Multiple AND conditions | "If X and Y and Z, then W" |
| `disjunctive` | Multiple OR conditions | "If X or Y, then Z" |
| `nested` | Conditions within conditions | "If X, then (if Y then Z)" |

### 4.2 Exception Presence
Mark `True` if words like: unless, except, excluding, with the exception of, provided that (negating)

---

## 5. Temporal Elements

### 5.1 Temporal Types
| Type | Examples |
|------|----------|
| `deadline` | within X days, before date, by time |
| `duration` | for X period, during, throughout |
| `sequence` | after, before, upon, following, prior to |
| `frequency` | annually, per semester, monthly, each term |

### 5.2 Temporal Expressions
Record the actual phrases: "within two weeks", "before the end of semester", etc.

---

## 6. Entity and Relationship

### 6.1 Entity Types
Common entities in AIT policies:
- `student`, `staff`, `faculty`, `advisor`
- `fee`, `payment`, `scholarship`
- `course`, `registration`, `grade`
- `accommodation`, `room`, `facility`
- `document`, `form`, `application`
- `department`, `office`, `committee`

### 6.2 Relationship Complexity
| Value | Definition | Example |
|-------|------------|---------|
| `direct` | Subject directly relates to object | "Student pays fee" |
| `mediated` | Via intermediate entity | "Student has obligation; obligation has amount" |
| `multi-hop` | Multiple intermediaries | "Student enrolled in program offered by department" |

---

## 7. Ambiguity Indicators

### 7.1 Vague Terms
Words without precise definition: large, appropriate, reasonable, timely, excessive, sufficient

### 7.2 Implicit Knowledge
Context needed beyond document: "as per standard procedure", "following normal process"

### 7.3 Undefined References
References to other documents or unspecified entities: "as specified in...", "according to policy..."

---

## 8. Formalization Outcomes

| Outcome | Definition |
|---------|------------|
| `SUCCESS` | Complete, valid FOL produced; can implement as SHACL |
| `PARTIAL` | FOL produced but requires simplifications/assumptions |
| `FAILURE-LINGUISTIC` | Cannot parse meaning unambiguously |
| `FAILURE-EXPRESSIVE` | Meaning clear but beyond FOL/SHACL expressiveness |
| `FAILURE-KNOWLEDGE` | Requires external knowledge not in policy |

---

## 9. Advisor Sampling Protocol

Since single-annotator approach is used:
1. **Self-Review**: Annotate with high confidence first
2. **Flag Uncertain**: Mark rules where annotation is uncertain
3. **Advisor Sample**: Request advisor review on:
   - All `PARTIAL` and `FAILURE` outcomes
   - Rules with confidence < 3
   - Complex rules (clause_count > 2)
   - Rules with ambiguity indicators
4. **Document Disagreements**: Record any annotation changes after review

---

*Codebook Version 1.0 - Created for ST124960 Thesis Research*
"""
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(codebook)
    
    print(f"Created annotation codebook: {output_path}")
    return codebook


if __name__ == "__main__":
    # Create the extraction spreadsheet
    create_extraction_spreadsheet()
    
    # Create the annotation codebook
    generate_annotation_codebook()
    
    print("\n✅ Thesis research tools created successfully!")
    print("\nNext steps:")
    print("1. Open research/policy_rules_corpus.xlsx")
    print("2. Review research/annotation_codebook.md")
    print("3. Extract rules from AIT P&P PDFs into the spreadsheet")
