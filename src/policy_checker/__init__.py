"""
policy_checker — Automated policy formalization pipeline.
 
PDF Policies → LLM Classification → FOL → SHACL Validation
"""
from pathlib import Path
 
# OLD (each file computed its own):
#   PROJECT_ROOT = Path(__file__).parent.parent.parent  (in nodes/)
#   PROJECT_ROOT = Path(__file__).parent.parent          (in web/app.py)
#   PROJECT_ROOT = Path(__file__).resolve().parent.parent (in db/)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
 