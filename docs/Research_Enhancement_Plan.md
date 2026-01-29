# Research Enhancement Plan
## Addressing Committee Feedback for Thesis Proposal

**A Methodology for Transforming Natural Language Academic Policies into Formal Knowledge for Automated Reasoning**

**Ponkrit Kaewsawee (st 124960)**

---

## Executive Summary

This document presents a comprehensive plan to address the feedback received from the thesis proposal committee (Dr. Chutiporn Anutariya and Prof. Attaphongse Taparugssanagorn). The plan reorganizes the research approach to eliminate methodological biases, strengthen scientific rigor, and provide clear validation mechanisms at every stage of the transformation process.

---

## 1. Committee Feedback Analysis

### 1.1 Dr. Chutiporn's Key Concerns

| Concern | Issue Identified | Impact on Research |
|---------|------------------|-------------------|
| **Selection Bias** | Self-defined complexity/clarity criteria lead to cherry-picking simple rules | Results would not generalize; methodology validity questionable |
| **Ungrounded Estimates** | 50% accuracy for complex rules is arbitrary without scientific basis | Cannot establish meaningful baseline or validate hypotheses |
| **Missing Validation** | Manual translation lacks verification checkpoints | Errors propagate through pipeline undetected |

### 1.2 Prof. Attaphongse's Key Concerns

| Concern | Issue Identified | Impact on Research |
|---------|------------------|-------------------|
| **Missing Full Example** | No complete end-to-end demonstration of the methodology | Readers cannot verify if approach actually works |
| **Unjustified Choices** | Why FOL? Why ABA? Why this classification? Not explained | Methodology appears arbitrary rather than principled |
| **Weak Evaluation** | No concrete metrics, comparison tables, or quantitative analysis | Cannot measure success or compare with alternatives |
| **Technical Gaps** | Ambiguity handling, tool chain, edge cases not specified | Implementation reproducibility compromised |

---

## 2. Revised Research Approach

### 2.1 From Selection to Discovery (Addressing Bias)

**Instead of defining categories and selecting rules that fit, adopt a pattern discovery approach:**

| Old Approach (Problematic) | New Approach (Recommended) |
|---------------------------|---------------------------|
| 1. Define complexity/clarity criteria | 1. Collect ALL rules from P&P documents |
| 2. Select only 'clear' and 'low complexity' rules | 2. Attempt to formalize each rule systematically |
| 3. Apply methodology to selected subset | 3. Document what works and what doesn't |
| 4. Report success rate on easy cases | 4. Discover patterns that emerge from data |
| **Result: Biased, non-generalizable findings** | **Result: Evidence-based pattern classification** |

### 2.2 Language Expressiveness Analysis

**Reframe scope based on what technologies CAN and CANNOT express:**

- **Expressible in FOL + SHACL:** Simple conditionals, class membership, property constraints, cardinality restrictions, value comparisons, temporal conditions (with proper modeling)

- **Beyond Current Scope:** Deontic modalities (permissions vs obligations), context-dependent interpretations, implicit domain knowledge, procedural sequences with state changes

- This analysis provides **scientific justification** for scope boundaries, not arbitrary selection.

---

## 3. Multi-Stage Validation Framework

Implement validation checkpoints at every major transformation stage:

| Stage | Validation Method | Validator | Deliverable |
|-------|------------------|-----------|-------------|
| **Policy → Simplified NL** | Semantic equivalence check | Domain Expert / Advisor | Annotated policy mapping document |
| **Simplified NL → FOL** | Logical proof verification | Advisor + Self-review with test cases | FOL statement with worked proofs |
| **FOL → Ontology** | Vocabulary completeness check | Ontology validation tools (Protégé) | OWL file + documentation |
| **FOL → SHACL** | Constraint correctness testing | Unit tests with synthetic data | SHACL shapes + test suite |
| **Full Pipeline** | End-to-end validation | Ground truth comparison | Confusion matrix + metrics |

---

## 4. Complete Worked Example Template

Provide a full end-to-end example with the following structure:

### Example Rule: "No pets allowed in student accommodation"

#### Step 1: Original Policy Statement
> **Source:** FS-1-1-1 Campus Accommodation for Students, Section VII
> 
> *"Pets are not allowed in student accommodation. The fine for non-compliance is Baht 2,000."*

#### Step 2: Simplified Natural Language
> "For all students residing in campus accommodation, they must not have pets."

#### Step 3: Vocabulary Extraction
- **Variables:** Student(x), Pet(p), Accommodation(a)
- **Predicates:** ResidesIn(x, a), HasPet(x, p), IsOnCampus(a)
- **Constants:** Fine = 2000 Baht

#### Step 4: FOL Statement
```
∀x,a [ (Student(x) ∧ Accommodation(a) ∧ ResidesIn(x, a) ∧ IsOnCampus(a) ∧ ∃p(Pet(p) ∧ HasPet(x, p))) → Violation(x, "PetProhibition") ]
```

#### Step 5: Logical Proof (Validation)

**Test Case A - Compliant Student:**
- Facts: Student(s1), Accommodation(dorm1), ResidesIn(s1, dorm1), IsOnCampus(dorm1), ¬∃p(HasPet(s1, p))
- Result: Condition fails (no pet exists) → **No violation ✓**

**Test Case B - Violating Student:**
- Facts: Student(s2), Accommodation(dorm2), ResidesIn(s2, dorm2), IsOnCampus(dorm2), Pet(dog1), HasPet(s2, dog1)
- Result: All conditions true → **Violation(s2, "PetProhibition") ✓**

#### Step 6: Ontology (Turtle Syntax)
```turtle
ait:Student a rdfs:Class .
ait:Pet a rdfs:Class .
ait:Accommodation a rdfs:Class .
ait:hasPet a rdf:Property ; rdfs:domain ait:Student ; rdfs:range ait:Pet .
ait:residesIn a rdf:Property ; rdfs:domain ait:Student ; rdfs:range ait:Accommodation .
ait:isOnCampus a rdf:Property ; rdfs:domain ait:Accommodation ; rdfs:range xsd:boolean .
```

#### Step 7: SHACL Shape
```turtle
ait:NoPetsShape a sh:NodeShape ;
  sh:targetClass ait:Student ;
  sh:sparql [
    sh:message "Student has a pet in campus accommodation (violation)." ;
    sh:select """
      SELECT $this WHERE {
        $this ait:residesIn ?acc .
        ?acc ait:isOnCampus true .
        $this ait:hasPet ?pet .
      }
    """ ;
  ] .
```

#### Step 8: Data Graph Examples

**Compliant Student Data:**
```turtle
ait:student_001 a ait:Student ;
  ait:hasName "Alice" ;
  ait:residesIn ait:dorm_A .
ait:dorm_A a ait:Accommodation ; ait:isOnCampus true .
```

**Non-Compliant Student Data:**
```turtle
ait:student_002 a ait:Student ;
  ait:hasName "Bob" ;
  ait:residesIn ait:dorm_B ;
  ait:hasPet ait:fluffy .
ait:dorm_B a ait:Accommodation ; ait:isOnCampus true .
ait:fluffy a ait:Pet .
```

#### Step 9: Validation Report
```turtle
SHACL Validation Result:
sh:conforms false ;
sh:result [
  sh:focusNode ait:student_002 ;
  sh:sourceShape ait:NoPetsShape ;
  sh:resultMessage "Student has a pet in campus accommodation (violation)." ;
] .
```

---

## 5. Justification of Methodological Choices

### 5.1 Why First-Order Logic (FOL)?

| Criterion | FOL | Alternatives (DL, Propositional) |
|-----------|-----|----------------------------------|
| **Expressive Power** | Quantifiers (∀, ∃), predicates, functions - sufficient for policy rules | DL: Limited quantification; Propositional: No variables |
| **Technology Independence** | Can translate to multiple targets (SHACL, OWL, Prolog) | DL: Tied to OWL; Propositional: Too limited |
| **Verifiability** | Standard proof methods, automated theorem provers available | DL: Specialized reasoners; Propositional: SAT solvers |
| **SHACL Compatibility** | SHACL2FOL proves bidirectional translation possible (Pareti, 2024) | Less direct mapping exists |

### 5.2 Why Assumption-Based Argumentation (ABA)?

ABA addresses a critical challenge in policy formalization: **handling ambiguity and implicit assumptions.**

- **Explicit Assumption Identification:** Policies often contain implicit assumptions (e.g., "large electrical appliances" assumes a shared understanding of what "large" means)
- **Conflict Resolution:** When rules contradict, ABA provides systematic evaluation of which interpretation is "acceptable"
- **Formal Foundation:** Grounded in Dung's argumentation semantics, providing theoretical rigor

#### ABA Application Example

**Ambiguous Rule:** *"Large electrical appliances are not permitted."*

1. **Identify Assumption:** What constitutes "large"? (Assumption: items > 1000W)
2. **Check Acceptability:** Does this assumption conflict with other policies or domain knowledge?
3. **Document Decision:** Record the chosen interpretation and justification
4. **Formalize:** Use the explicit assumption in FOL: `∀x,a (Appliance(a) ∧ Wattage(a) > 1000 ∧ Owns(x,a) → Violation(x))`

---

## 6. Enhanced Evaluation Framework

### 6.1 Quantitative Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Formalization Coverage** | (Rules successfully formalized / Total rules) × 100% | Report actual % |
| **Detection Accuracy** | (TP + TN) / (TP + TN + FP + FN) × 100% | ≥ 95% for low complexity |
| **Precision** | TP / (TP + FP) - Avoiding false alarms | ≥ 90% |
| **Recall** | TP / (TP + FN) - Catching all violations | ≥ 90% |
| **Translation Fidelity** | Expert-assessed semantic equivalence score (1-5 scale) | ≥ 4.0 average |

### 6.2 Expected Results Table Template

| Rule Pattern | Count | Formalized | Accuracy | Precision | Recall |
|-------------|-------|------------|----------|-----------|--------|
| Simple Prohibition | 12 | 12 (100%) | 100% | 100% | 100% |
| Conditional (1-2 conditions) | 15 | 14 (93%) | 95% | 92% | 96% |
| Temporal Constraints | 6 | 5 (83%) | 88% | 85% | 90% |
| Multi-step Procedures | 5 | 2 (40%) | N/A | N/A | N/A |
| **TOTAL** | **38** | **33 (87%)** | **-** | **-** | **-** |

*Note: This is a template showing expected format. Actual values will be determined through experimentation.*

---

## 7. Technical Implementation Clarifications

### 7.1 Tool Chain

- **Ontology Development:** Protégé (for visualization and validation), OWL/RDF serialization
- **SHACL Processing:** PySHACL (Python library for SHACL validation)
- **RDF Manipulation:** RDFLib (Python), Apache Jena (Java)
- **Triple Store:** GraphDB (for SHACL-enabled validation)
- **Data Conversion:** Custom Python scripts for SQL → RDF transformation

### 7.2 Handling Special Cases

#### Exception Handling Pattern
**Policy:** *"Cooking is not permitted, except in accommodation units with cooking facilities."*
```
∀x,a [ Student(x) ∧ ResidesIn(x,a) ∧ Cooks(x) ∧ ¬HasCookingFacility(a) → Violation(x, "IllegalCooking") ]
```

#### Temporal Constraint Pattern
**Policy:** *"Students must vacate within 5 days after graduation."*
```
∀x,d [ Student(x) ∧ Graduated(x) ∧ GraduationDate(x,d) ∧ StillResiding(x) ∧ DaysSince(d) > 5 → Violation(x, "LateVacation") ]
```

---

## 8. Acknowledged Limitations & Future Work

### 8.1 Current Limitations

1. **Manual Translation:** The Policy → FOL step requires human expertise; automation is future work
2. **Domain Specificity:** Framework validated only on AIT academic policies; generalization needs testing
3. **Deontic Logic Gap:** Current approach treats all rules as constraints; permissions/obligations not distinguished
4. **Procedural Rules:** Multi-step processes with state changes beyond current SHACL capabilities

### 8.2 Future Research Directions

- **LLM-Assisted Translation:** Using GPT-4 or similar to automate Policy → FOL with human verification
- **Deontic Extension:** Incorporating obligation/permission operators into the formal framework
- **Cross-Domain Validation:** Testing methodology on legal regulations, healthcare policies, financial compliance

---

## 9. Implementation Action Plan

| Week | Action Item | Deliverable | Validation |
|------|------------|-------------|------------|
| **1-2** | Extract ALL rules from 5 P&P documents (no pre-filtering) | Complete rule inventory | Advisor review |
| **3-4** | Attempt FOL formalization for each rule; document failures | FOL statements + failure log | Proof verification |
| **5-6** | Analyze patterns: what works, what doesn't, why | Pattern taxonomy | Committee feedback |
| **7-8** | Develop ontology and SHACL shapes for formalizable rules | Shape Graph | Protégé validation |
| **9-10** | Create test data and run validation experiments | Test suite + results | Ground truth comparison |
| **11-12** | Compute metrics, analyze results, document limitations | Evaluation chapter | Statistical analysis |

---

## 10. Conclusion

This enhancement plan addresses all major concerns raised by the thesis committee. The key changes are:

1. **Shifting from selection-based to discovery-based methodology** (eliminating bias)
2. **Adding multi-stage validation with expert review** (ensuring quality)
3. **Providing complete worked examples** (demonstrating feasibility)
4. **Justifying methodological choices with comparisons** (strengthening rigor)
5. **Defining concrete evaluation metrics** (enabling measurement)

By implementing these changes, the research will produce scientifically valid, reproducible, and practically useful results that genuinely contribute to the field of automated compliance checking.

---

## Quick Reference: Addressing Each Committee Concern

### Dr. Chutiporn's Concerns → Solutions

| Concern | Solution in This Plan |
|---------|----------------------|
| Selection Bias | Section 2.1: Discovery-based approach |
| Need for "Universal Pattern" | Section 2.2: Language expressiveness analysis |
| Missing Validation | Section 3: Multi-stage validation framework |

### Prof. Attaphongse's Concerns → Solutions

| Concern | Solution in This Plan |
|---------|----------------------|
| Missing Full Example | Section 4: Complete worked example |
| Unjustified Choices | Section 5: Why FOL? Why ABA? |
| Weak Evaluation | Section 6: Quantitative metrics and tables |
| Technical Gaps | Section 7: Tool chain and special cases |

---

*Document prepared to guide research enhancement based on committee feedback analysis.*
