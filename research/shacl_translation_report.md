# SHACL Translation Report

**Generated:** 2026-01-29T19:36:39.802512
**Output:** ait_policy_shapes.ttl

## Statistics

| Type | Count |
|------|-------|
| Obligations | 65 |
| Permissions | 17 |
| Prohibitions | 14 |
| Skipped | 0 |
| **Total** | **96** |

## SHACL Features Used

- `sh:NodeShape` for class-level constraints
- `sh:property` for required properties
- `sh:severity` based on deontic type
- `deontic:type` custom property for rule classification

## Usage

```bash
# Validate RDF data against SHACL shapes
pip install pyshacl

# Python validation
from pyshacl import validate
conforms, results_graph, results_text = validate(
    data_graph='your_data.ttl',
    shacl_graph='ait_policy_shapes.ttl'
)
print(results_text)
```

## Next Steps

1. Create test RDF data for validation
2. Run SHACL validation
3. Report compliance results
