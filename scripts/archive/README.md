# Archived Scripts

This directory contains deprecated scripts that have been superseded by newer versions or are no longer needed in the active pipeline.

## v1_deprecated/

Scripts that have been replaced by improved v2 versions:

- **`populate_llm_annotations.py`** - Used fallback regex instead of real LLM. Replaced by `populate_llm_annotations_v2.py`
- **`generate_fol.py`** - Superseded by `generate_fol_v2.py`
- **`fol_to_shacl.py`** - Superseded by `fol_to_shacl_v2.py`

## One-time Utilities

Scripts used once for data setup/fixes:

- **`create_annotation_template.py`** - Created initial `gold_standard_template.json` (completed)
- **`annotate_interactive.py`** - Manual annotation UI (not used in automated pipeline)
- **`reannotate_consequences.py`** - Fixed "may result in" misclassifications (applied to v2 gold standard)
- **`compare_models.py`** - Generated initial model comparison (used regex fallback, results invalid)

## Why Archived?

These scripts are preserved for reference but moved out of the active `scripts/` directory to:

1. Reduce confusion about which version to use
2. Keep the main scripts folder clean and focused
3. Maintain project history for documentation

**Note:** If you need to reference the original implementation or understand the project evolution, these scripts provide that context.
