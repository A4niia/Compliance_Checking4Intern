# Policy Rule Annotation Codebook
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
