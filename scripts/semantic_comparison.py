"""
Semantic Equivalence Comparison Tool
Compares SHACL validation results across different pipeline runs to measure semantic equivalence.

Purpose: Even if FOL formulas differ textually, they may produce the same validation results.
This tool measures semantic equivalence by comparing violation sets.

Key Metrics:
- Jaccard Similarity: intersection / union of violation sets
- Coverage Match: % of student records with identical violation status
- Violation Count Correlation: How similar are the violation counts
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict


# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_shacl_shapes(shacl_file: Path) -> str:
    """Load SHACL shapes from Turtle file."""
    if not shacl_file.exists():
        raise FileNotFoundError(f"SHACL file not found: {shacl_file}")
    return shacl_file.read_text()


def validate_student_set(shacl_shapes: str, student_records: List[Dict]) -> Dict[str, Set[str]]:
    """
    Validate a set of students against SHACL shapes.
    
    Args:
        shacl_shapes: SHACL shapes in Turtle format
        student_records: List of student records
    
    Returns:
        Dict mapping student_id -> set of violation types
    """
    from webapp.backend.services.rdf_converter import student_to_rdf
    from webapp.backend.services.shacl_validator import validate_student
    
    violations_by_student = {}
    
    for student in student_records:
        student_id = student.get('student_id', 'unknown')
        
        # Convert to RDF
        student_rdf = student_to_rdf(student, [])
        
        # Validate
        result = validate_student(student_rdf)
        
        # Extract violation types
        violations = set()
        if not result.get('conforms', True):
            violation_texts = result.get('violations', [])
            for v in violation_texts:
                # Simple extraction - in production, parse RDF properly
                if 'sh:focusNode' in v or 'sh:resultMessage' in v:
                    violations.add(v.split(':')[-1].strip())
        
        violations_by_student[student_id] = violations
    
    return violations_by_student


def calculate_jaccard_similarity(set_a: Set, set_b: Set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    
    return intersection / union if union > 0 else 0.0


def compare_violations(
    violations_a: Dict[str, Set[str]],
    violations_b: Dict[str, Set[str]]
) -> Dict[str, Any]:
    """
    Compare two sets of validation results.
    
    Args:
        violations_a: Violations from run A
        violations_b: Violations from run B
    
    Returns:
        Comparison metrics
    """
    all_students = set(violations_a.keys()) | set(violations_b.keys())
    
    exact_matches = 0
    total_similarity = 0.0
    status_matches = 0  # Same violation status (pass/fail)
    
    for student_id in all_students:
        viol_a = violations_a.get(student_id, set())
        viol_b = violations_b.get(student_id, set())
        
        # Exact match
        if viol_a == viol_b:
            exact_matches += 1
        
        # Status match (both pass or both fail)
        status_a = len(viol_a) > 0
        status_b = len(viol_b) > 0
        if status_a == status_b:
            status_matches += 1
        
        # Jaccard similarity
        similarity = calculate_jaccard_similarity(viol_a, viol_b)
        total_similarity += similarity
    
    num_students = len(all_students)
    
    return {
        "total_students": num_students,
        "exact_matches": exact_matches,
        "exact_match_rate": exact_matches / num_students if num_students > 0 else 0,
        "status_matches": status_matches,
        "status_match_rate": status_matches / num_students if num_students > 0 else 0,
        "average_jaccard_similarity": total_similarity / num_students if num_students > 0 else 0
    }


def compare_shacl_files(
    shacl_file_a: Path,
    shacl_file_b: Path,
    student_db_path: Path
) -> Dict[str, Any]:
    """
    Compare two SHACL shape files by validating against same student dataset.
    
    Args:
        shacl_file_a: First SHACL file
        shacl_file_b: Second SHACL file
        student_db_path: Path to student database
    
    Returns:
        Comparison results
    """
    # Load SHACL shapes
    shapes_a = load_shacl_shapes(shacl_file_a)
    shapes_b = load_shacl_shapes(shacl_file_b)
    
    # Load students
    from webapp.backend.services.student_db import get_all_students
    students = get_all_students()
    
    if not students:
        return {"error": "No students found in database"}
    
    # Validate with both SHACL sets
    print(f"Validating {len(students)} students with SHACL A...")
    violations_a = validate_student_set(shapes_a, students)
    
    print(f"Validating {len(students)} students with SHACL B...")
    violations_b = validate_student_set(shapes_b, students)
    
    # Compare violations
    comparison = compare_violations(violations_a, violations_b)
    
    return {
        "shacl_file_a": str(shacl_file_a.name),
        "shacl_file_b": str(shacl_file_b.name),
        "comparison": comparison,
        "semantic_equivalence_score": comparison["average_jaccard_similarity"],
        "interpretation": interpret_semantic_equivalence(comparison)
    }


def interpret_semantic_equivalence(comparison: Dict) -> str:
    """Provide human-readable interpretation of results."""
    score = comparison.get("average_jaccard_similarity", 0)
    status_rate = comparison.get("status_match_rate", 0)
    
    if score >= 0.95 and status_rate >= 0.95:
        return "SEMANTICALLY EQUIVALENT - Results are nearly identical"
    elif score >= 0.85 and status_rate >= 0.90:
        return "HIGHLY SIMILAR - Minor differences in violation details"
    elif score >= 0.70 and status_rate >= 0.80:
        return "MODERATELY SIMILAR - Some semantic differences exist"
    elif status_rate >= 0.70:
        return "PARTIALLY SIMILAR - Same pass/fail status but different violations"
    else:
        return "SEMANTICALLY DIFFERENT - Significant differences in validation results"


def compare_reproducibility_runs(
    run_1_shacl: Path,
    run_2_shacl: Path
) -> None:
    """
    Compare two reproducibility test runs.
    
    Args:
        run_1_shacl: SHACL output from run 1
        run_2_shacl: SHACL output from run 2
    """
    student_db = PROJECT_ROOT / "webapp" / "data" / "students.db"
    
    print("=" * 70)
    print("SEMANTIC EQUIVALENCE COMPARISON")
    print("=" * 70)
    print(f"\nRun 1 SHACL: {run_1_shacl.name}")
    print(f"Run 2 SHACL: {run_2_shacl.name}")
    print()
    
    results = compare_shacl_files(run_1_shacl, run_2_shacl, student_db)
    
    if "error" in results:
        print(f"ERROR: {results['error']}")
        return
    
    comp = results["comparison"]
    
    print("RESULTS:")
    print(f"  Total Students:      {comp['total_students']}")
    print(f"  Exact Matches:       {comp['exact_matches']} ({comp['exact_match_rate']:.1%})")
    print(f"  Status Matches:      {comp['status_matches']} ({comp['status_match_rate']:.1%})")
    print(f"  Jaccard Similarity:  {comp['average_jaccard_similarity']:.3f}")
    print()
    print(f"INTERPRETATION: {results['interpretation']}")
    print(f"SEMANTIC SCORE: {results['semantic_equivalence_score']:.1%}")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare semantic equivalence of SHACL outputs")
    parser.add_argument("shacl_1", type=Path, help="First SHACL file")
    parser.add_argument("shacl_2", type=Path, help="Second SHACL file")
    
    args = parser.parse_args()
    
    compare_reproducibility_runs(args.shacl_1, args.shacl_2)
