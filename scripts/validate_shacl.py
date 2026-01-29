#!/usr/bin/env python3
"""
SHACL Validation Script
Validates RDF data against SHACL policy shapes.
"""

import json
from pathlib import Path
from datetime import datetime

try:
    from pyshacl import validate
    from rdflib import Graph
    HAS_PYSHACL = True
except ImportError:
    HAS_PYSHACL = False
    print("Warning: pyshacl not installed. Install with: pip install pyshacl")

PROJECT_ROOT = Path(__file__).parent.parent
SHACL_DIR = PROJECT_ROOT / "shacl"
RESEARCH_DIR = PROJECT_ROOT / "research"


def run_validation(data_file: Path, shapes_file: Path):
    """Run SHACL validation and return results."""
    print("=" * 60)
    print("SHACL VALIDATION")
    print("=" * 60)
    
    if not HAS_PYSHACL:
        print("Error: pyshacl required. Install with: pip install pyshacl")
        return None
    
    print(f"Data:   {data_file}")
    print(f"Shapes: {shapes_file}")
    
    # Run validation
    conforms, results_graph, results_text = validate(
        str(data_file),
        shacl_graph=str(shapes_file),
        inference='none',
        abort_on_first=False,
        allow_warnings=True,
        meta_shacl=False
    )
    
    print("\n" + "=" * 60)
    print(f"RESULT: {'✅ CONFORMS' if conforms else '❌ VIOLATIONS FOUND'}")
    print("=" * 60)
    
    if results_text:
        print("\nValidation Report:")
        print("-" * 40)
        print(results_text[:2000])  # Limit output
    
    return {
        "conforms": conforms,
        "results_text": results_text,
        "timestamp": datetime.now().isoformat()
    }


def main():
    # Default files
    shapes_file = SHACL_DIR / "ait_policy_shapes.ttl"
    data_file = SHACL_DIR / "test_data.ttl"
    
    if not shapes_file.exists():
        print(f"Error: Shapes file not found: {shapes_file}")
        return
    
    if not data_file.exists():
        print(f"Error: Test data not found: {data_file}")
        print("Create test_data.ttl in shacl/ directory")
        return
    
    # Run validation
    results = run_validation(data_file, shapes_file)
    
    if results:
        # Save results
        output_file = RESEARCH_DIR / "shacl_validation_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\n📊 Results saved: {output_file}")


if __name__ == "__main__":
    main()
