#!/usr/bin/env python3
"""
Student Database Service
Queries mock_student_data.db for validation scenarios
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional

# Use absolute path or relative from project root
DB_PATH = Path(__file__).parent.parent.parent.parent / "research" / "mock_student_data.db"


def get_connection():
    """Get database connection."""
    return sqlite3.connect(str(DB_PATH))


def get_student_by_id(student_id: str) -> Optional[Dict]:
    """Get student record by ID."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute(
        "SELECT * FROM students WHERE student_id = ?",
        (student_id,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_student_by_scenario(scenario: str) -> Optional[Dict]:
    """
    Get a student by violation scenario.
    
    Args:
        scenario: 'single_violation', 'multiple_violations', or 'compliant'
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    
    # Query based on test case results
    if scenario == 'single_violation':
        # Find student with exactly 1 failing test case
        query = """
        SELECT s.*, COUNT(tc.id) as violation_count
        FROM students s
        JOIN test_cases tc ON s.student_id = tc.entity_id
        WHERE tc.expected_result = 'FAIL' AND tc.entity_type = 'student'
        GROUP BY s.student_id
        HAVING COUNT(tc.id) = 1
        LIMIT 1
        """
    elif scenario == 'multiple_violations':
        # Find student with 2+ failing test cases
        query = """
        SELECT s.*, COUNT(tc.id) as violation_count
        FROM students s
        JOIN test_cases tc ON s.student_id = tc.entity_id
        WHERE tc.expected_result = 'FAIL' AND tc.entity_type = 'student'
        GROUP BY s.student_id
        HAVING COUNT(tc.id) > 1
        LIMIT 1
        """
    elif scenario == 'compliant':
        # Find student with only passing test cases or no test cases
        query = """
        SELECT s.*, 0 as violation_count
        FROM students s
        WHERE s.student_id NOT IN (
            SELECT entity_id FROM test_cases 
            WHERE expected_result = 'FAIL' AND entity_type = 'student'
        )
        LIMIT 1
        """
    else:
        return None
    
    cursor = conn.execute(query)
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_student_violations(student_id: str) -> List[Dict]:
    """Get all rule violations for a student."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute("""
        SELECT * FROM test_cases
        WHERE entity_id = ? AND expected_result = 'FAIL'
    """, (student_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_all_students(limit: int = 10) -> List[Dict]:
    """Get all students with optional limit."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute(f"SELECT * FROM students LIMIT {limit}")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_database_stats() -> Dict:
    """Get database statistics."""
    conn = get_connection()
    
    stats = {}
    
    # Total students
    stats['total_students'] = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    
    # By violation count from test_cases
    stats['compliant'] = conn.execute("""
        SELECT COUNT(DISTINCT s.student_id)
        FROM students s
        WHERE s.student_id NOT IN (
            SELECT entity_id FROM test_cases 
            WHERE expected_result = 'FAIL' AND entity_type = 'student'
        )
    """).fetchone()[0]
    
    stats['single_violation'] = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT entity_id
            FROM test_cases
            WHERE expected_result = 'FAIL' AND entity_type = 'student'
            GROUP BY entity_id
            HAVING COUNT(*) = 1
        )
    """).fetchone()[0]
    
    stats['multiple_violations'] = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT entity_id
            FROM test_cases
            WHERE expected_result = 'FAIL' AND entity_type = 'student'
            GROUP BY entity_id
            HAVING COUNT(*) > 1
        )
    """).fetchone()[0]
    
    conn.close()
    return stats


if __name__ == "__main__":
    # Test the service
    print("Database Statistics:")
    print(json.dumps(get_database_stats(), indent=2))
    
    print("\nSample student (single violation):")
    student = get_student_by_scenario('single_violation')
    if student:
        print(f"  ID: {student.get('student_id')}")
        print(f"  Name: {student.get('name')}")
        
        violations = get_student_violations(student['student_id'])
        print(f"  Violations: {len(violations)}")
        if violations:
            for v in violations:
                print(f"    - Rule: {v.get('rule_id')}, Desc: {v.get('description')}")
