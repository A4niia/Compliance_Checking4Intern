# SHACL Translation Report (Refined)

**Generated:** 2026-02-07T20:31:16.760732
**Input:** fol_formalization_v2_results.json
**Output:** ait_policy_shapes_refined.ttl

## Statistics

| Deontic Type | Count |
|--------------|-------|
| Obligation | 65 |
| Permission | 17 |
| Prohibition | 14 |
| Skipped | 0 |
| **Total** | **96** |

## Target Classes Used

| Class | Count |
|-------|-------|
| ait:Person | 31 |
| ait:Accommodation | 16 |
| ait:Student | 16 |
| ait:Examination | 3 |
| ait:ExchangeStudent | 3 |
| ait:Grievance | 3 |
| ait:Employee | 3 |
| ait:Faculty | 3 |
| ait:PostgraduateStudent | 2 |
| ait:Invoice | 2 |
| ait:Account | 2 |
| ait:Semester | 2 |
| ait:GrievanceCommittee | 2 |
| ait:Research | 2 |
| ait:RegistrationFee | 2 |
| ait:ContractedResearch | 1 |
| ait:Dormitory | 1 |
| ait:Committee | 1 |
| ait:Course | 1 |

## Improvements Over v1

1. **Proper Target Classes**: Uses domain ontology classes instead of auto-generated
2. **Entity Detection**: Automatically maps rules to appropriate entities (Student, Fee, etc.)
3. **Better Comments**: Includes truncated original text in rdfs:comment
4. **Cleaner Output**: Consistent formatting and organization

## Next Steps

1. Validate shapes syntax with pyshacl
2. Create test data matching the ontology classes
3. Run validation to verify shapes work correctly
