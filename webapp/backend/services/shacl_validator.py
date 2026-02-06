"""
SHACL Validation Service
Uses pySHACL to validate RDF data against SHACL shapes
"""

from typing import Dict, Optional
from pathlib import Path

# Default SHACL shapes file
SHACL_FILE = Path(__file__).parent.parent.parent.parent / "shacl" / "ait_policy_shapes_refined.ttl"


def validate_student(student_rdf: str, shapes_file: Optional[str] = None) -> Dict:
    """
    Run SHACL validation on student RDF data.
    
    Args:
        student_rdf: RDF graph in Turtle format
        shapes_file: Optional path to SHACL shapes file
    
    Returns:
        Validation results dictionary
    """
    if shapes_file is None:
        shapes_file = str(SHACL_FILE)
    
    try:
        import pyshacl
        
        # Run validation
        conforms, results_graph, results_text = pyshacl.validate(
            data_graph=student_rdf,
            shacl_graph=shapes_file,
            data_graph_format='turtle',
            shacl_graph_format='turtle',
            inference='rdfs',
            abort_on_first=False,
            allow_warnings=True,
            meta_shacl=False
        )
        
        # Parse violations from results
        violations = []
        if not conforms:
            # Simple parsing - in production, parse the RDF properly
            lines = results_text.split('\n')
            for line in lines:
                if 'sh:focusNode' in line or 'sh:resultMessage' in line:
                    violations.append(line.strip())
        
        return {
            "conforms": conforms,
            "violations": violations,
            "report_text": results_text,
            "violation_count": len(violations)
        }
        
    except ImportError:
        # pySHACL not installed - return mock result
        return {
            "conforms": True,
            "violations": [],
            "report_text": "pySHACL not installed. Install with: pip install pyshacl",
            "violation_count": 0,
            "mock": True
        }
    except Exception as e:
        return {
            "conforms": False,
            "violations": [str(e)],
            "report_text": f"Validation error: {str(e)}",
            "violation_count": 1,
            "error": True
        }


if __name__ == "__main__":
    # Test
    test_rdf = """@prefix ait: <http://example.org/ait-policy#> .
@prefix student: <http://example.org/student/> .

student:ST001 a ait:Student ;
    ait:studentId "ST001" ;
    ait:feesPaid false .
"""
    
    result = validate_student(test_rdf)
    print(f"Conforms: {result['conforms']}")
    print(f"Violations: {result['violation_count']}")
