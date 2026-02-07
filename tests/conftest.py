#!/usr/bin/env python3
"""
Shared pytest fixtures for SHACL TDD tests.
"""

import json
import pytest
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SHACL_DIR = PROJECT_ROOT / "shacl"
RESEARCH_DIR = PROJECT_ROOT / "research"

# Try to import rdflib and pyshacl
try:
    from rdflib import Graph, Namespace, Literal, URIRef, RDF, RDFS, XSD
    from pyshacl import validate
    HAS_SHACL_DEPS = True
except ImportError:
    HAS_SHACL_DEPS = False

# Namespaces
AIT = Namespace("http://example.org/ait-policy#")
DEONTIC = Namespace("http://example.org/deontic#")
SH = Namespace("http://www.w3.org/ns/shacl#")


@pytest.fixture(scope="session")
def project_root():
    """Return project root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def shacl_dir():
    """Return SHACL directory path."""
    return SHACL_DIR


@pytest.fixture(scope="session")
def research_dir():
    """Return research directory path."""
    return RESEARCH_DIR


@pytest.fixture(scope="session")
def shapes_graph():
    """Load the refined SHACL shapes graph."""
    if not HAS_SHACL_DEPS:
        pytest.skip("rdflib/pyshacl not installed")
    
    shapes_file = SHACL_DIR / "ait_policy_shapes_refined.ttl"
    if not shapes_file.exists():
        # Fall back to original shapes
        shapes_file = SHACL_DIR / "ait_policy_shapes.ttl"
    
    if not shapes_file.exists():
        pytest.skip(f"Shapes file not found: {shapes_file}")
    
    g = Graph()
    g.parse(str(shapes_file), format="turtle")
    return g


@pytest.fixture(scope="session")
def ontology_graph():
    """Load the AIT policy ontology graph."""
    if not HAS_SHACL_DEPS:
        pytest.skip("rdflib/pyshacl not installed")
    
    ontology_file = SHACL_DIR / "ait_policy_ontology.ttl"
    if not ontology_file.exists():
        pytest.skip(f"Ontology file not found: {ontology_file}")
    
    g = Graph()
    g.parse(str(ontology_file), format="turtle")
    return g


@pytest.fixture(scope="session")
def gold_standard():
    """Load the gold standard annotated dataset."""
    gs_file = RESEARCH_DIR / "gold_standard_annotated_v2.json"
    if not gs_file.exists():
        pytest.skip(f"Gold standard not found: {gs_file}")
    
    with open(gs_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    return data.get("rules", data.get("items", []))


@pytest.fixture(scope="session")
def fol_results():
    """Load FOL formalization results."""
    fol_file = RESEARCH_DIR / "fol_formalization_v2_results.json"
    if not fol_file.exists():
        fol_file = RESEARCH_DIR / "fol_formalization_results.json"
    
    if not fol_file.exists():
        pytest.skip(f"FOL results not found: {fol_file}")
    
    with open(fol_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get("formalized_rules", [])


@pytest.fixture
def empty_data_graph():
    """Create a fresh empty data graph with prefixes."""
    if not HAS_SHACL_DEPS:
        pytest.skip("rdflib/pyshacl not installed")
    
    g = Graph()
    g.bind("ait", AIT)
    g.bind("deontic", DEONTIC)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    return g


def create_compliant_student(graph, student_id="Student001", name="Test Student",
                              paid=True, enrolled=True, resides=True):
    """Helper: Create a compliant student entity in the graph."""
    student = AIT[student_id]
    graph.add((student, RDF.type, AIT.Student))
    graph.add((student, RDFS.label, Literal(name)))
    graph.add((student, AIT.studentId, Literal(f"ST{student_id}")))
    graph.add((student, AIT.paid, Literal(paid, datatype=XSD.boolean)))
    graph.add((student, AIT.enrolled, Literal(enrolled, datatype=XSD.boolean)))
    graph.add((student, AIT.residesoncampus, Literal(resides, datatype=XSD.boolean)))
    return student


def create_noncompliant_student(graph, student_id="Student999", name="Bad Student",
                                 paid=False, enrolled=True):
    """Helper: Create a non-compliant student entity (unpaid fees)."""
    student = AIT[student_id]
    graph.add((student, RDF.type, AIT.Student))
    graph.add((student, RDFS.label, Literal(name)))
    graph.add((student, AIT.studentId, Literal(f"ST{student_id}")))
    graph.add((student, AIT.paid, Literal(paid, datatype=XSD.boolean)))
    graph.add((student, AIT.enrolled, Literal(enrolled, datatype=XSD.boolean)))
    return student


def create_employee(graph, emp_id="Employee001", name="Test Employee",
                    accepted_gift=False, gift_value=0, reported=False):
    """Helper: Create an employee entity."""
    emp = AIT[emp_id]
    graph.add((emp, RDF.type, AIT.Employee))
    graph.add((emp, RDFS.label, Literal(name)))
    graph.add((emp, AIT.acceptedgift, Literal(accepted_gift, datatype=XSD.boolean)))
    graph.add((emp, AIT.giftvalue, Literal(gift_value, datatype=XSD.integer)))
    graph.add((emp, AIT.reported, Literal(reported, datatype=XSD.boolean)))
    return emp
