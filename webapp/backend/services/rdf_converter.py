"""
RDF Converter Service
Converts student JSON data to RDF Turtle format
"""

from typing import Dict


def student_to_rdf(student_data: Dict, violations: list = None) -> str:
    """
    Convert student data to RDF/Turtle format.
    
    Args:
        student_data: Student record from database
        violations: List of rule violations
    
    Returns:
        RDF graph in Turtle format
    """
    student_id = student_data.get('student_id', 'UNKNOWN')
    name = student_data.get('name', 'Unknown')
    program = student_data.get('program', 'Unknown')
    fees_paid = student_data.get('fees_paid', False)
    is_full_time = student_data.get('is_full_time', True)
    
    # Build RDF graph
    rdf = f"""@prefix ait: <http://example.org/ait-policy#> .
@prefix student: <http://example.org/student/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

student:{student_id} a ait:Student ;
    ait:studentId "{student_id}" ;
    ait:name "{name}" ;
    ait:program "{program}" ;
    ait:feesPaid {str(fees_paid).lower()} ;
    ait:isFullTime {str(is_full_time).lower()} .
"""
    
    return rdf


if __name__ == "__main__":
    # Test
    test_data = {
        "student_id": "ST001",
        "name": "Alice Chen",
        "program": "Master",
        "fees_paid": True,
        "is_full_time": True
    }
    
    print(student_to_rdf(test_data))
