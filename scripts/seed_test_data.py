#!/usr/bin/env python3
"""
Seed Test Data Script
Creates mock student database for TDD validation of SHACL shapes.

Generates both COMPLIANT and NON-COMPLIANT test data for all 97 policy rules.
"""

import sqlite3
import json
import os
from datetime import datetime, date, time, timedelta
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "research" / "mock_student_data.db"
GOLD_STANDARD_PATH = Path(__file__).parent.parent / "research" / "gold_standard_annotated_v2.json"


def create_database(conn: sqlite3.Connection):
    """Create all tables for the mock student database."""
    cursor = conn.cursor()
    
    # Core entity tables
    cursor.executescript("""
        -- Students table
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            program TEXT NOT NULL, -- 'Master', 'Doctoral', 'Diploma'
            enrollment_status TEXT NOT NULL, -- 'active', 'graduated', 'suspended', 'withdrawn'
            is_full_time BOOLEAN DEFAULT TRUE,
            semester_count INTEGER DEFAULT 1,
            fees_paid BOOLEAN DEFAULT FALSE,
            registered_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Sponsors table (for sponsored students)
        CREATE TABLE IF NOT EXISTS sponsors (
            sponsor_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            has_promissory_note BOOLEAN DEFAULT FALSE,
            outstanding_dues REAL DEFAULT 0.0
        );
        
        -- Student-Sponsor relationship
        CREATE TABLE IF NOT EXISTS student_sponsors (
            student_id TEXT,
            sponsor_id TEXT,
            sponsorship_type TEXT, -- 'full', 'partial'
            PRIMARY KEY (student_id, sponsor_id),
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (sponsor_id) REFERENCES sponsors(sponsor_id)
        );
        
        -- Assignments table
        CREATE TABLE IF NOT EXISTS assignments (
            assignment_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            course_code TEXT NOT NULL,
            submitted_at TIME,
            deadline TIME NOT NULL,
            has_cover_page BOOLEAN DEFAULT TRUE,
            submission_date DATE,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );
        
        -- Accommodations table
        CREATE TABLE IF NOT EXISTS accommodations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            unit_number TEXT,
            accommodation_type TEXT, -- 'dormitory', 'apartment', 'employee_housing'
            is_on_campus BOOLEAN DEFAULT TRUE,
            approval_status TEXT, -- 'approved', 'pending', 'denied'
            move_in_date DATE,
            move_out_date DATE,
            has_subletting BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );
        
        -- Research publications
        CREATE TABLE IF NOT EXISTS publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            title TEXT NOT NULL,
            is_contracted_research BOOLEAN DEFAULT FALSE,
            has_confidentiality_clause BOOLEAN DEFAULT FALSE,
            publication_date DATE,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );
        
        -- Employee gifts (for ethics rules)
        CREATE TABLE IF NOT EXISTS gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_id TEXT NOT NULL, -- can be student or employee
            recipient_type TEXT NOT NULL, -- 'student', 'employee'
            gift_value REAL NOT NULL,
            reported_to_unit_head BOOLEAN DEFAULT FALSE,
            reported_within_15_days BOOLEAN DEFAULT FALSE,
            acceptance_date DATE,
            report_date DATE
        );
        
        -- Grievances
        CREATE TABLE IF NOT EXISTS grievances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filed_by TEXT NOT NULL,
            filed_against TEXT,
            grievance_type TEXT,
            facts_ascertained BOOLEAN DEFAULT FALSE,
            settlement_informed_to_president BOOLEAN DEFAULT FALSE,
            breach_identified BOOLEAN DEFAULT FALSE,
            filed_date DATE,
            resolved_date DATE
        );
        
        -- Overdue accounts
        CREATE TABLE IF NOT EXISTS overdue_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            amount_due REAL NOT NULL,
            days_overdue INTEGER DEFAULT 0,
            reviewed_periodically BOOLEAN DEFAULT FALSE,
            collection_initiated BOOLEAN DEFAULT FALSE,
            written_off BOOLEAN DEFAULT FALSE,
            president_approved_writeoff BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );
        
        -- Exam registrations
        CREATE TABLE IF NOT EXISTS exam_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_code TEXT NOT NULL,
            exam_type TEXT, -- 'midterm', 'final'
            payment_completed BOOLEAN DEFAULT FALSE,
            payment_deadline DATE,
            exam_date DATE,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );
        
        -- Test case results tracking
        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT NOT NULL,
            test_type TEXT NOT NULL, -- 'compliant', 'non_compliant'
            entity_type TEXT NOT NULL, -- 'student', 'sponsor', 'employee', etc.
            entity_id TEXT NOT NULL,
            expected_result TEXT NOT NULL, -- 'PASS', 'FAIL'
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()


def seed_students(conn: sqlite3.Connection):
    """Create sample students with various statuses."""
    cursor = conn.cursor()
    
    students = [
        # Compliant students (fees paid, registered properly)
        ("ST001", "Alice Chen", "Master", "active", True, 2, True, "2026-01-15"),
        ("ST002", "Bob Smith", "Doctoral", "active", True, 4, True, "2026-01-10"),
        ("ST003", "Carol Williams", "Diploma", "active", True, 1, True, "2026-01-20"),
        
        # Non-compliant students (fees not paid but registered)
        ("ST004", "David Brown", "Master", "active", True, 2, False, "2026-01-15"),
        ("ST005", "Eva Johnson", "Doctoral", "active", True, 3, False, "2026-01-10"),
        
        # Part-time students
        ("ST006", "Frank Miller", "Master", "active", False, 2, True, "2026-01-15"),
        ("ST007", "Grace Lee", "Doctoral", "active", False, 4, False, "2026-01-10"),
        
        # Graduated students
        ("ST008", "Henry Davis", "Master", "graduated", True, 4, True, "2025-12-01"),
        ("ST009", "Ivy Wilson", "Doctoral", "graduated", True, 8, True, "2025-11-15"),
        
        # Exchange/Dual degree students
        ("ST010", "Jack Taylor", "Master", "active", True, 2, True, "2026-01-15"),
        ("ST011", "Kate Anderson", "Doctoral", "active", True, 3, True, "2026-01-10"),
        
        # New students (first semester)
        ("ST012", "Leo Martinez", "Master", "active", True, 1, True, "2026-01-20"),
        ("ST013", "Mia Garcia", "Doctoral", "active", True, 1, True, "2026-01-22"),
        
        # Suspended students
        ("ST014", "Nathan Clark", "Master", "suspended", True, 3, False, "2025-08-15"),
        ("ST015", "Olivia White", "Doctoral", "suspended", True, 2, False, "2025-09-01"),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO students 
        (student_id, name, program, enrollment_status, is_full_time, semester_count, fees_paid, registered_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, students)
    
    conn.commit()
    return [s[0] for s in students]


def seed_sponsors(conn: sqlite3.Connection):
    """Create sample sponsors with various payment statuses."""
    cursor = conn.cursor()
    
    sponsors = [
        # Compliant sponsors (with promissory notes)
        ("SP001", "Thailand Government Scholarship", True, 0.0),
        ("SP002", "AIT Foundation", True, 5000.0),
        
        # Non-compliant sponsors (outstanding dues, no promissory note)
        ("SP003", "XYZ Corporation", False, 15000.0),
        ("SP004", "Private Foundation", False, 8000.0),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO sponsors (sponsor_id, name, has_promissory_note, outstanding_dues)
        VALUES (?, ?, ?, ?)
    """, sponsors)
    
    # Link students to sponsors
    student_sponsors = [
        ("ST001", "SP001", "full"),
        ("ST002", "SP002", "partial"),
        ("ST004", "SP003", "full"),  # Non-compliant: sponsor has no promissory note
        ("ST005", "SP004", "partial"),  # Non-compliant
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO student_sponsors (student_id, sponsor_id, sponsorship_type)
        VALUES (?, ?, ?)
    """, student_sponsors)
    
    conn.commit()


def seed_assignments(conn: sqlite3.Connection):
    """Create sample assignments with various submission times."""
    cursor = conn.cursor()
    
    assignments = [
        # Compliant submissions (before deadline)
        ("A001", "ST001", "CS501", "16:55:00", "17:00:00", True, "2026-02-01"),
        ("A002", "ST002", "CS502", "14:30:00", "17:00:00", True, "2026-02-01"),
        ("A003", "ST003", "CS503", "16:59:00", "17:00:00", True, "2026-02-01"),
        
        # Non-compliant: late submissions
        ("A004", "ST004", "CS501", "17:30:00", "17:00:00", True, "2026-02-01"),
        ("A005", "ST005", "CS502", "18:45:00", "17:00:00", True, "2026-02-01"),
        ("A006", "ST001", "CS504", "23:59:00", "17:00:00", True, "2026-02-02"),
        
        # Non-compliant: missing cover page
        ("A007", "ST006", "CS501", "16:00:00", "17:00:00", False, "2026-02-01"),
        ("A008", "ST007", "CS502", "15:30:00", "17:00:00", False, "2026-02-01"),
        
        # Non-compliant: both late AND missing cover page
        ("A009", "ST004", "CS503", "18:00:00", "17:00:00", False, "2026-02-01"),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO assignments 
        (assignment_id, student_id, course_code, submitted_at, deadline, has_cover_page, submission_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, assignments)
    
    conn.commit()


def seed_accommodations(conn: sqlite3.Connection):
    """Create sample accommodation records."""
    cursor = conn.cursor()
    
    accommodations = [
        # Compliant: on-campus with approval
        ("ST001", "D101", "dormitory", True, "approved", "2026-01-15", None, False),
        ("ST002", "A201", "apartment", True, "approved", "2026-01-10", None, False),
        
        # Non-compliant: off-campus without approval
        ("ST004", None, "apartment", False, "pending", "2026-01-15", None, False),
        ("ST005", None, "dormitory", False, "denied", "2026-01-10", None, False),
        
        # Non-compliant: subletting
        ("ST006", "D102", "dormitory", True, "approved", "2025-08-01", None, True),
        
        # Graduated but still in housing (beyond 5-day limit)
        ("ST008", "A203", "apartment", True, "approved", "2025-08-01", None, False),
        ("ST009", "D105", "dormitory", True, "approved", "2025-06-01", None, False),
        
        # Exchange students
        ("ST010", "D103", "dormitory", True, "approved", "2026-01-15", "2026-02-28", False),
        ("ST011", "D104", "dormitory", True, "approved", "2026-01-10", "2026-03-15", False),
        
        # Employee housing (married students)
        ("ST003", "E301", "employee_housing", True, "approved", "2026-01-20", None, False),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO accommodations 
        (student_id, unit_number, accommodation_type, is_on_campus, approval_status, 
         move_in_date, move_out_date, has_subletting)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, accommodations)
    
    conn.commit()


def seed_publications(conn: sqlite3.Connection):
    """Create sample research publications."""
    cursor = conn.cursor()
    
    publications = [
        # Regular publications (no confidentiality issues)
        ("ST002", "Machine Learning for Policy Analysis", False, False, "2026-01-15"),
        ("ST009", "Deep Learning Applications in NLP", False, False, "2025-12-01"),
        
        # Contracted research with confidentiality (compliant - not published)
        ("ST001", "Proprietary Algorithm Development", True, True, None),
        
        # Contracted research published without approval (non-compliant)
        ("ST005", "Corporate Data Analysis", True, True, "2026-01-20"),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO publications 
        (student_id, title, is_contracted_research, has_confidentiality_clause, publication_date)
        VALUES (?, ?, ?, ?, ?)
    """, publications)
    
    conn.commit()


def seed_gifts(conn: sqlite3.Connection):
    """Create sample gift records for ethics rules."""
    cursor = conn.cursor()
    
    gifts = [
        # Compliant: small gifts (< 3000 THB)
        ("EMP001", "employee", 2500.0, False, False, "2026-01-15", None),
        ("EMP002", "employee", 1000.0, False, False, "2026-01-20", None),
        
        # Compliant: large gifts reported within 15 days
        ("EMP003", "employee", 5000.0, True, True, "2026-01-10", "2026-01-20"),
        ("EMP004", "employee", 10000.0, True, True, "2026-01-05", "2026-01-15"),
        
        # Non-compliant: large gifts not reported
        ("EMP005", "employee", 4000.0, False, False, "2026-01-01", None),
        ("EMP006", "employee", 8000.0, False, False, "2025-12-15", None),
        
        # Non-compliant: large gifts reported late (> 15 days)
        ("EMP007", "employee", 6000.0, True, False, "2025-12-01", "2026-01-20"),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO gifts 
        (recipient_id, recipient_type, gift_value, reported_to_unit_head, 
         reported_within_15_days, acceptance_date, report_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, gifts)
    
    conn.commit()


def seed_grievances(conn: sqlite3.Connection):
    """Create sample grievance records."""
    cursor = conn.cursor()
    
    grievances = [
        # Compliant: all procedures followed
        ("ST001", "Prof. Smith", "academic", True, True, True, "2026-01-01", "2026-01-15"),
        ("EMP001", "EMP002", "workplace", True, True, True, "2025-12-01", "2025-12-20"),
        
        # Non-compliant: facts not ascertained
        ("ST004", "Prof. Jones", "academic", False, False, False, "2026-01-10", None),
        
        # Non-compliant: settlement not informed to president
        ("ST005", "ST006", "personal", True, False, True, "2026-01-05", "2026-01-25"),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO grievances 
        (filed_by, filed_against, grievance_type, facts_ascertained, 
         settlement_informed_to_president, breach_identified, filed_date, resolved_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, grievances)
    
    conn.commit()


def seed_overdue_accounts(conn: sqlite3.Connection):
    """Create sample overdue account records."""
    cursor = conn.cursor()
    
    overdue_accounts = [
        # Compliant: reviewed and collection initiated
        ("ST004", 15000.0, 30, True, True, False, False),
        ("ST005", 8000.0, 45, True, True, False, False),
        
        # Non-compliant: not reviewed periodically
        ("ST014", 25000.0, 60, False, False, False, False),
        ("ST015", 12000.0, 90, False, False, False, False),
        
        # Written off with approval (compliant)
        ("ST008", 5000.0, 180, True, True, True, True),
        
        # Written off without president approval (non-compliant)
        ("ST009", 3000.0, 120, True, True, True, False),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO overdue_accounts 
        (student_id, amount_due, days_overdue, reviewed_periodically, 
         collection_initiated, written_off, president_approved_writeoff)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, overdue_accounts)
    
    conn.commit()


def seed_exam_registrations(conn: sqlite3.Connection):
    """Create sample exam registration records."""
    cursor = conn.cursor()
    
    exam_registrations = [
        # Compliant: payment completed before deadline
        ("ST001", "CS501", "midterm", True, "2026-02-01", "2026-02-15"),
        ("ST002", "CS502", "final", True, "2026-01-25", "2026-02-20"),
        
        # Non-compliant: payment not completed but exam registered
        ("ST004", "CS501", "midterm", False, "2026-02-01", "2026-02-15"),
        ("ST007", "CS503", "final", False, "2026-01-20", "2026-02-25"),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO exam_registrations 
        (student_id, course_code, exam_type, payment_completed, payment_deadline, exam_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, exam_registrations)
    
    conn.commit()


def register_test_cases(conn: sqlite3.Connection):
    """Register all test cases linking entities to policy rules."""
    cursor = conn.cursor()
    
    # Load gold standard to map test cases to rules
    with open(GOLD_STANDARD_PATH, 'r', encoding='utf-8') as f:
        gold_standard = json.load(f)
    
    test_cases = []
    
    # Map common rule patterns to test data
    for rule in gold_standard:
        rule_id = rule.get('rule_id', rule.get('id'))
        rule_type = rule['human_annotation']['rule_type']
        original_text = rule.get('original_text', '').lower()
        
        # Payment/Fees rules
        if 'paid' in original_text or 'payment' in original_text or 'fees' in original_text:
            test_cases.extend([
                (rule_id, 'compliant', 'student', 'ST001', 'PASS', 'Fees paid before registration'),
                (rule_id, 'compliant', 'student', 'ST002', 'PASS', 'Fees paid before registration'),
                (rule_id, 'non_compliant', 'student', 'ST004', 'FAIL', 'Fees not paid'),
                (rule_id, 'non_compliant', 'student', 'ST005', 'FAIL', 'Fees not paid'),
            ])
        
        # Submission deadline rules
        if 'submit' in original_text or 'deadline' in original_text:
            test_cases.extend([
                (rule_id, 'compliant', 'assignment', 'A001', 'PASS', 'On-time submission'),
                (rule_id, 'compliant', 'assignment', 'A002', 'PASS', 'On-time submission'),
                (rule_id, 'non_compliant', 'assignment', 'A004', 'FAIL', 'Late submission'),
                (rule_id, 'non_compliant', 'assignment', 'A005', 'FAIL', 'Late submission'),
            ])
        
        # Accommodation rules
        if 'accommodat' in original_text or 'housing' in original_text or 'dormitor' in original_text:
            test_cases.extend([
                (rule_id, 'compliant', 'accommodation', 'ST001', 'PASS', 'Valid on-campus housing'),
                (rule_id, 'non_compliant', 'accommodation', 'ST004', 'FAIL', 'Unapproved housing'),
                (rule_id, 'non_compliant', 'accommodation', 'ST006', 'FAIL', 'Subletting violation'),
            ])
        
        # Sponsor rules
        if 'sponsor' in original_text or 'promissory' in original_text:
            test_cases.extend([
                (rule_id, 'compliant', 'sponsor', 'SP001', 'PASS', 'Has promissory note'),
                (rule_id, 'non_compliant', 'sponsor', 'SP003', 'FAIL', 'No promissory note'),
            ])
        
        # Gift/Ethics rules
        if 'gift' in original_text or 'thb' in original_text or 'reported' in original_text:
            test_cases.extend([
                (rule_id, 'compliant', 'gift', 'EMP003', 'PASS', 'Gift reported within 15 days'),
                (rule_id, 'non_compliant', 'gift', 'EMP005', 'FAIL', 'Gift not reported'),
                (rule_id, 'non_compliant', 'gift', 'EMP007', 'FAIL', 'Gift reported late'),
            ])
        
        # Grievance rules
        if 'grievance' in original_text or 'tribunal' in original_text:
            test_cases.extend([
                (rule_id, 'compliant', 'grievance', '1', 'PASS', 'All procedures followed'),
                (rule_id, 'non_compliant', 'grievance', '3', 'FAIL', 'Facts not ascertained'),
            ])
        
        # Overdue account rules
        if 'overdue' in original_text or 'collection' in original_text:
            test_cases.extend([
                (rule_id, 'compliant', 'overdue_account', 'ST004', 'PASS', 'Account reviewed and collection initiated'),
                (rule_id, 'non_compliant', 'overdue_account', 'ST014', 'FAIL', 'Account not reviewed'),
            ])
        
        # Write-off rules
        if 'write' in original_text or 'president' in original_text:
            test_cases.extend([
                (rule_id, 'compliant', 'overdue_account', 'ST008', 'PASS', 'Write-off approved by president'),
                (rule_id, 'non_compliant', 'overdue_account', 'ST009', 'FAIL', 'Write-off without approval'),
            ])
    
    # Remove duplicates
    test_cases = list(set(test_cases))
    
    cursor.executemany("""
        INSERT OR REPLACE INTO test_cases 
        (rule_id, test_type, entity_type, entity_id, expected_result, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, test_cases)
    
    conn.commit()
    print(f"Registered {len(test_cases)} test cases")


def generate_summary(conn: sqlite3.Connection):
    """Generate summary of seeded data."""
    cursor = conn.cursor()
    
    tables = [
        'students', 'sponsors', 'student_sponsors', 'assignments',
        'accommodations', 'publications', 'gifts', 'grievances',
        'overdue_accounts', 'exam_registrations', 'test_cases'
    ]
    
    print("\n" + "="*60)
    print("MOCK DATABASE SUMMARY")
    print("="*60)
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:25} : {count:5} records")
    
    # Test case summary
    cursor.execute("""
        SELECT test_type, expected_result, COUNT(*) 
        FROM test_cases 
        GROUP BY test_type, expected_result
    """)
    
    print("\n" + "-"*40)
    print("TEST CASE BREAKDOWN")
    print("-"*40)
    for row in cursor.fetchall():
        print(f"{row[0]:15} {row[1]:6} : {row[2]:5} cases")
    
    print("="*60 + "\n")


def main():
    """Main function to create and seed the database."""
    print(f"Creating database at: {DB_PATH}")
    
    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Removed existing database")
    
    # Create connection
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Create tables
        print("Creating tables...")
        create_database(conn)
        
        # Seed data
        print("Seeding students...")
        seed_students(conn)
        
        print("Seeding sponsors...")
        seed_sponsors(conn)
        
        print("Seeding assignments...")
        seed_assignments(conn)
        
        print("Seeding accommodations...")
        seed_accommodations(conn)
        
        print("Seeding publications...")
        seed_publications(conn)
        
        print("Seeding gifts...")
        seed_gifts(conn)
        
        print("Seeding grievances...")
        seed_grievances(conn)
        
        print("Seeding overdue accounts...")
        seed_overdue_accounts(conn)
        
        print("Seeding exam registrations...")
        seed_exam_registrations(conn)
        
        print("Registering test cases...")
        register_test_cases(conn)
        
        # Generate summary
        generate_summary(conn)
        
        print(f"✅ Successfully created mock database at: {DB_PATH}")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
