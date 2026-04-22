"""
PolicyChecker — Compliance Dashboard (FastAPI)

A web-based demo that showcases the SHACL-based compliance checking pipeline.
Users can browse extracted rules, submit RDF data, and see live validation results.

Usage:
    pip install fastapi uvicorn jinja2 python-multipart
    cd demo
    python app.py
    # Open http://localhost:8000
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

app = FastAPI(title="PolicyChecker Compliance Dashboard", version="1.0.0")

# Static files and templates
DEMO_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(DEMO_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(DEMO_DIR / "templates"))

# ── Data paths ────────────────────────────────────────────────────────────
OUTPUT_DIR = PROJECT_ROOT / "output" / "ait"
SHAPES_FILE = OUTPUT_DIR / "shapes_generated.ttl"
RULES_FILE = OUTPUT_DIR / "classified_rules.json"
FOL_FILE = OUTPUT_DIR / "fol_formulas.json"
REPORT_FILE = OUTPUT_DIR / "pipeline_report.json"
TEST_DATA_FILE = PROJECT_ROOT / "shacl" / "test_data" / "tdd_test_data_fixed.ttl"
ONTOLOGY_FILE = PROJECT_ROOT / "shacl" / "ontology" / "ait_policy_ontology.ttl"


# ── Cached data loading ──────────────────────────────────────────────────
_cache: dict = {}

def _load_json(path: Path) -> dict | list:
    if str(path) not in _cache:
        if path.exists():
            _cache[str(path)] = json.loads(path.read_text(encoding="utf-8"))
        else:
            _cache[str(path)] = []
    return _cache[str(path)]


def _load_text(path: Path) -> str:
    if path.exists():
        text = path.read_text(encoding="utf-8")
        # Sanitise broken multi-line FOL comments in generated shapes
        if path == SHAPES_FILE:
            text = _sanitize_turtle(text)
        return text
    return ""


def _sanitize_turtle(text: str) -> str:
    """Fix broken Turtle syntax in generated shapes.

    Issues handled:
    1. Multi-line FOL comments where continuation lines lack '#' prefix
    2. SPARQL-style '?x' variables in Turtle (invalid)
    """
    import re
    lines = text.split('\n')
    result = []
    in_fol_comment = False
    for line in lines:
        stripped = line.strip()
        # Detect start of FOL comment
        if stripped.startswith('# FOL:'):
            in_fol_comment = True
            result.append(line)
            continue
        # If we're inside a FOL comment continuation
        if in_fol_comment:
            # Valid Turtle starts with a prefix, URI, or is blank
            if (stripped == '' or stripped.startswith('#') or
                stripped.startswith('@') or stripped.startswith('ait:') or
                stripped.startswith('sh:') or stripped.startswith('rdf') or
                stripped.startswith('deontic:')):
                in_fol_comment = False
            else:
                # This is a continuation of the FOL comment — fix it
                result.append('# ' + stripped)
                continue

        # Fix ?x variables in non-comment lines (invalid in Turtle)
        if not stripped.startswith('#') and '?' in line:
            line = re.sub(r'\?[a-zA-Z_]\w*', 'ait:Thing', line)

        result.append(line)
    return '\n'.join(result)


def _get_rules() -> list:
    return _load_json(RULES_FILE)


def _get_fol() -> list:
    return _load_json(FOL_FILE)


def _get_report() -> dict:
    data = _load_json(REPORT_FILE)
    return data if isinstance(data, dict) else {}


def _get_shapes_for_rule(rule_id: str) -> str:
    """Extract the SHACL shape block for a specific rule from the combined TTL."""
    shapes_text = _load_text(SHAPES_FILE)
    if not shapes_text:
        return ""
    # Find the block for this rule
    marker = f"# Rule: {rule_id}"
    start = shapes_text.find(marker)
    if start == -1:
        return ""
    # Find the next rule block or end
    next_marker = shapes_text.find("# Rule:", start + len(marker))
    if next_marker == -1:
        return shapes_text[start:].strip()
    return shapes_text[start:next_marker].strip()


# ── Sample data for demo ─────────────────────────────────────────────────
SAMPLE_DATA = """\
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix ait:  <http://example.org/ait-policy#> .

# ═══════════════════════════════════════════════════════════════
# Sample University Data — AIT Compliance Checking Demo
# ═══════════════════════════════════════════════════════════════
# Each entity represents a realistic member of the AIT community.
# Properties align with SHACL shapes generated from AIT policy
# documents (Credit Policy, Campus Accommodation, Ethical
# Behavior, Student Handbook, Academic Integrity).
# ═══════════════════════════════════════════════════════════════

# ── 1. Somchai — Master's Student, Fully Compliant ────────────
# Scenario: A self-funded Thai M.Eng. student in his 2nd semester.
#   He paid all fees on time, lives on-campus in a Category-2
#   dorm, maintains academic integrity, and follows all conduct
#   rules. Expected result: CLEAN (zero violations).
ait:Somchai a ait:Student ;
    rdfs:label "Somchai Prasert — Compliant Master's Student" ;
    ait:enrolled               true ;
    ait:payFee                 true ;
    ait:payFirstSemesterFee    true ;
    ait:fullPayment            true ;
    ait:student                true ;
    ait:bringConcernsToAttention        true ;
    ait:regularcleaningandhygieneoftheunit true ;
    ait:maintainCleanlinessOfCommonAreaAndLandscape true ;
    ait:maintainCleanlinessOfBedroomAndFacilities   true ;
    ait:clean                  true ;
    ait:vacateRoom             true ;
    ait:newStudent             true ;
    ait:queuing                true ;
    ait:confirmOfferMove       true ;
    ait:moveWithSpouse         true ;
    ait:provideapproximatedateofarrivaloncampus     true ;
    ait:putNameOnWaitingListForCampusAccommodation  true ;
    ait:payRentForStayOnCampus true ;
    ait:vacatesRoom            true ;
    ait:meetHighestStandardsOfPersonalEthicalAndMoralConduct true ;
    ait:maintainPeacefulHealthyLearningEnvironmentForFreeDiscussion true ;
    ait:useAITLibraryAndEducationalResourcesResponsibly true ;
    ait:abideByAcceptableUsePolicyForITResources    true ;
    ait:determineGradeInCourse true ;
    ait:scheduledoutsideregularhoursmakeupclasses    true ;
    ait:paidinadvanceorfully   true ;
    ait:registry               true ;
    ait:serveAsCorrespondingAuthor true ;
    ait:correspondAsAuthorWithJournal true ;
    ait:multiAuthoredArticleWrittenByStudentShouldBeFirstAuthorUnlessJournalRequiresDifferentOrder true .

# ── 2. Napat — Undergrad, Hasn't Paid Fees ────────────────────
# Scenario: A 1st-year Thai B.Eng. student who enrolled but
#   failed to pay the semester fee by the deadline. His student
#   ID has not been activated, and he risks suspension.
#   Expected result: violations on fee-payment obligations
#   (AIT-0007, AIT-0010, AIT-0014, AIT-0032, AIT-0094).
ait:Napat a ait:Student ;
    rdfs:label "Napat Srikhao — Fee Defaulter (Unpaid Tuition)" ;
    ait:enrolled               true ;
    ait:payFee                 false ;
    ait:payFirstSemesterFee    false ;
    ait:fullPayment            false ;
    ait:paidinadvanceorfully   false ;
    ait:student                true ;
    ait:bringConcernsToAttention        true ;
    ait:regularcleaningandhygieneoftheunit true ;
    ait:maintainCleanlinessOfCommonAreaAndLandscape true ;
    ait:maintainCleanlinessOfBedroomAndFacilities   true ;
    ait:clean                  true ;
    ait:vacateRoom             true ;
    ait:queuing                true ;
    ait:confirmOfferMove       true ;
    ait:moveWithSpouse         true ;
    ait:provideapproximatedateofarrivaloncampus     true ;
    ait:putNameOnWaitingListForCampusAccommodation  true ;
    ait:payRentForStayOnCampus true ;
    ait:vacatesRoom            true ;
    ait:meetHighestStandardsOfPersonalEthicalAndMoralConduct true ;
    ait:maintainPeacefulHealthyLearningEnvironmentForFreeDiscussion true ;
    ait:useAITLibraryAndEducationalResourcesResponsibly true ;
    ait:abideByAcceptableUsePolicyForITResources    true ;
    ait:determineGradeInCourse true ;
    ait:scheduledoutsideregularhoursmakeupclasses    true ;
    ait:registry               true ;
    ait:newStudent             true ;
    ait:serveAsCorrespondingAuthor true ;
    ait:correspondAsAuthorWithJournal true ;
    ait:multiAuthoredArticleWrittenByStudentShouldBeFirstAuthorUnlessJournalRequiresDifferentOrder true .

# ── 3. Priya — Exchange Student, Disruptive Dorm Resident ─────
# Scenario: An Indian exchange student staying in a shared dorm.
#   She has been cooking in her unit (prohibited in Cat-1 dorms),
#   disturbing neighbours with loud late-night study groups, and
#   keeps a pet cat in the dorm. Her fees are paid, but she
#   violates multiple accommodation conduct rules.
#   Expected result: violations on AIT-0072, AIT-0076, AIT-0078,
#   AIT-0085, AIT-0088.
ait:Priya a ait:Student ;
    rdfs:label "Priya Sharma — Disruptive Dorm Resident" ;
    ait:enrolled               true ;
    ait:payFee                 true ;
    ait:payFirstSemesterFee    true ;
    ait:fullPayment            true ;
    ait:paidinadvanceorfully   true ;
    ait:student                true ;
    ait:bringConcernsToAttention        true ;
    ait:newStudent             true ;
    ait:queuing                true ;
    ait:confirmOfferMove       true ;
    ait:moveWithSpouse         true ;
    ait:provideapproximatedateofarrivaloncampus     true ;
    ait:putNameOnWaitingListForCampusAccommodation  true ;
    ait:payRentForStayOnCampus true ;
    ait:vacatesRoom            true ;
    ait:vacateRoom             true ;
    ait:clean                  true ;
    ait:meetHighestStandardsOfPersonalEthicalAndMoralConduct true ;
    ait:maintainPeacefulHealthyLearningEnvironmentForFreeDiscussion true ;
    ait:useAITLibraryAndEducationalResourcesResponsibly true ;
    ait:abideByAcceptableUsePolicyForITResources    true ;
    ait:determineGradeInCourse true ;
    ait:scheduledoutsideregularhoursmakeupclasses    true ;
    ait:registry               true ;
    ait:serveAsCorrespondingAuthor true ;
    ait:correspondAsAuthorWithJournal true ;
    ait:multiAuthoredArticleWrittenByStudentShouldBeFirstAuthorUnlessJournalRequiresDifferentOrder true ;
    # ⚠ Violations — accommodation conduct
    ait:cookInUnit             true ;
    ait:cookInProhibitedDormitory true ;
    ait:disturbFellowStudentsInResidentialAreas true ;
    ait:noisyGroupStudyOrPartyInStudentAccommodation true ;
    ait:petInStudentAccommodation true ;
    # Missing cleaning obligations
    ait:regularcleaningandhygieneoftheunit false ;
    ait:maintainCleanlinessOfCommonAreaAndLandscape false ;
    ait:maintainCleanlinessOfBedroomAndFacilities   false .

# ── 4. Dr. Tanaka — Faculty, Fully Compliant ─────────────────
# Scenario: A Japanese associate professor in the School of
#   Engineering. He follows disciplinary procedures, discloses
#   potential conflicts of interest, makes grading criteria
#   known to students at the start of each course, and reports
#   suspicious academic integrity issues to the Dean.
#   Expected result: CLEAN (zero violations).
ait:DrTanaka a ait:Faculty ;
    rdfs:label "Dr. Kenji Tanaka — Compliant Faculty Member" ;
    ait:followProceduresForDisciplinaryActions true ;
    ait:disclose               true ;
    ait:makeKnownCriteriaForGrading true ;
    ait:suspectCheatingDuringExamOrAssignmentOrResearchProject true ;
    ait:reported               true .

# ── 5. Maria — Administrative Staff, Unreported Gift ──────────
# Scenario: A Filipina administrative officer in the Finance
#   department. She accepted a gift worth THB 5,000 from a
#   vendor but did not report it to her Unit Head within 15 days
#   as required. She also hasn't settled a travel promissory
#   note on time.
#   Expected result: violations on AIT-0029 (settled), AIT-0102
#   (reported).
ait:Maria a ait:Employee ;
    rdfs:label "Maria Santos — Unreported Gift (Admin Staff)" ;
    ait:reported               false ;
    ait:settled                false ;
    ait:feesPaid               true ;
    ait:payFees                true ;
    ait:usesAuthorityEthicallyWithRespectAndSensitivityAndInAccordanceWithInstitutesPolicies true ;
    ait:expresses_personal_opinion true ;
    ait:undergoDisciplinaryAction true .

# ── 6. Arjun — Campus Resident, Lease Violations ─────────────
# Scenario: An Indian research assistant living in staff
#   accommodation. His employment contract ended last month
#   but he has not vacated the unit. He has not paid the
#   required two-month deposit and owes overdue rent.
#   Expected result: violations on AIT-0026, AIT-0027, AIT-0023,
#   AIT-0028, AIT-0084, AIT-0098.
ait:Arjun a ait:Resident ;
    rdfs:label "Arjun Mehta — Overstaying Campus Resident" ;
    ait:tenant_vacates_unit    false ;
    ait:payTwoMonthDeposit     false ;
    ait:payAdditionalCharges   false ;
    ait:requestDoubtfulAccountsApproval false ;
    ait:request_and_Approve_and_Forward false ;
    ait:actInInterestOfInstitute false ;
    ait:inform_President_of_Settlements false ;
    ait:consult_with_president_and_inform_police false ;
    ait:ceaseGameOrActivity    true ;
    ait:reportIncidentOrPractice true ;
    ait:appointGrievanceTribunal true .

# ── 7. Lin — PhD Student with Spouse, Compliant ──────────────
# Scenario: A Chinese doctoral student whose husband is an AIT
#   lab technician. She is registered for staff accommodation
#   as required for students with AIT-employed spouses. She has
#   paid all fees and maintains academic integrity.
#   Expected result: CLEAN (zero violations).
ait:Lin a ait:PostgraduateStudent ;
    rdfs:label "Lin Wei — Compliant PhD Student (Married)" ;
    ait:enrolled               true ;
    ait:payFee                 true ;
    ait:payFirstSemesterFee    true ;
    ait:fullPayment            true ;
    ait:student                true ;
    ait:paidinadvanceorfully   true ;
    ait:studentID_and_InternetEmailAccess_not_released_by_Registry true ;
    ait:registers_for_staff_accommodation true ;
    ait:bringConcernsToAttention        true ;
    ait:regularcleaningandhygieneoftheunit true ;
    ait:maintainCleanlinessOfCommonAreaAndLandscape true ;
    ait:maintainCleanlinessOfBedroomAndFacilities   true ;
    ait:clean                  true ;
    ait:vacateRoom             true ;
    ait:queuing                true ;
    ait:confirmOfferMove       true ;
    ait:moveWithSpouse         true ;
    ait:provideapproximatedateofarrivaloncampus     true ;
    ait:putNameOnWaitingListForCampusAccommodation  true ;
    ait:payRentForStayOnCampus true ;
    ait:vacatesRoom            true ;
    ait:newStudent             true ;
    ait:meetHighestStandardsOfPersonalEthicalAndMoralConduct true ;
    ait:maintainPeacefulHealthyLearningEnvironmentForFreeDiscussion true ;
    ait:useAITLibraryAndEducationalResourcesResponsibly true ;
    ait:abideByAcceptableUsePolicyForITResources    true ;
    ait:determineGradeInCourse true ;
    ait:scheduledoutsideregularhoursmakeupclasses    true ;
    ait:registry               true ;
    ait:serveAsCorrespondingAuthor true ;
    ait:correspondAsAuthorWithJournal true ;
    ait:multiAuthoredArticleWrittenByStudentShouldBeFirstAuthorUnlessJournalRequiresDifferentOrder true .

# ── 8. Ethics Committee — Institutional Body ─────────────────
# Scenario: AIT's Grievance Committee responsible for handling
#   harassment and discrimination complaints. Validates whether
#   the committee fulfils its procedural obligations (receiving
#   grievances, electing a chair, maintaining confidentiality).
#   Expected result: CLEAN (zero violations).
ait:EthicsCommittee a ait:Committee ;
    rdfs:label "AIT Grievance & Ethics Committee" ;
    ait:receive_grievance      true ;
    ait:electsChair            true ;
    ait:grievanceCommitteePerformsRole true ;
    ait:prepared               true ;
    ait:confidentiality_and_due_regard  true ;
    ait:grievanceProcedureInvolvement   true ;
    ait:writeDownGrievanceFacts true ;
    ait:recordFacts            true ;
    ait:analyzeGrievance       true ;
    ait:conveneGrievanceTribunal true ;
    ait:attendHearing          true ;
    ait:ascertainFactsOfCase   true ;
    ait:expressesInWriting     true ;
    ait:submitWrittenAgreementsToGrievanceCommittee true .
"""


# ── Routes ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/stats")
async def get_stats():
    """Pipeline summary statistics."""
    report = _get_report()
    summary = report.get("summary", {})
    rules = _get_rules()
    # Count by type
    type_dist = {}
    for r in rules:
        t = r.get("rule_type", "unknown")
        type_dist[t] = type_dist.get(t, 0) + 1

    return {
        "total_rules": len(rules),
        "type_distribution": type_dist,
        "sentences_extracted": summary.get("sentences_extracted", 0),
        "candidates_prefiltered": summary.get("candidates_prefiltered", 0),
        "fol_ok": summary.get("fol_formulas_ok", 0),
        "fol_failed": summary.get("fol_formulas_failed", 0),
        "shapes_total": summary.get("shacl_shapes_total", 0),
        "shapes_valid": summary.get("shacl_shapes_valid", 0),
        "pipeline_version": report.get("pipeline_version", "unknown"),
    }


@app.get("/api/rules")
async def get_rules(
    rule_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
):
    """List classified rules with filtering and pagination."""
    rules = _get_rules()

    # Filter by type
    if rule_type and rule_type != "all":
        rules = [r for r in rules if r.get("rule_type") == rule_type]

    # Search
    if search:
        q = search.lower()
        rules = [r for r in rules if q in r.get("text", "").lower()
                 or q in r.get("rule_id", "").lower()
                 or q in r.get("source_document", "").lower()]

    total = len(rules)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "rules": rules[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@app.get("/api/rules/{rule_id}")
async def get_rule_detail(rule_id: str):
    """Get a single rule with its SHACL shape and FOL formula."""
    rules = _get_rules()
    rule = next((r for r in rules if r["rule_id"] == rule_id), None)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    # Find matching FOL
    fol_formulas = _get_fol()
    fol = next((f for f in fol_formulas if f["rule_id"] == rule_id), None)

    # Get SHACL shape
    shape = _get_shapes_for_rule(rule_id)

    return {
        "rule": rule,
        "fol": fol,
        "shacl_shape": shape,
    }


@app.get("/api/sample-data")
async def get_sample_data():
    """Return pre-built sample RDF data for demo."""
    return {"turtle": SAMPLE_DATA}


@app.post("/api/validate")
async def validate_data(request: Request):
    """Validate submitted RDF data against pipeline SHACL shapes."""
    body = await request.json()
    data_turtle = body.get("data", "")
    selected_shapes = body.get("shapes", "all")  # "all" or list of rule_ids

    if not data_turtle.strip():
        raise HTTPException(status_code=400, detail="No RDF data provided")

    try:
        from rdflib import Graph
        from pyshacl import validate

        # Load data graph
        data_graph = Graph()
        data_graph.parse(data=data_turtle, format="turtle")

        # Load shapes — clear cache to pick up sanitisation
        if str(SHAPES_FILE) in _cache:
            del _cache[str(SHAPES_FILE)]
        shapes_text = _load_text(SHAPES_FILE)

        if selected_shapes != "all" and isinstance(selected_shapes, list):
            # Extract only selected shape blocks
            blocks = []
            prefix_end = shapes_text.find("# Rule:")
            if prefix_end > 0:
                blocks.append(shapes_text[:prefix_end])
            for rid in selected_shapes:
                block = _get_shapes_for_rule(rid)
                if block:
                    blocks.append(block)
            shapes_text = "\n\n".join(blocks)

        # Parse shapes block-by-block — skip any LLM-generated invalid Turtle
        shapes_graph = Graph()
        prefix_block = shapes_text[:shapes_text.find("# Rule:")] if "# Rule:" in shapes_text else ""
        shape_blocks = shapes_text.split("# Rule:")
        skipped = 0
        for i, block in enumerate(shape_blocks):
            if i == 0:
                # This is the prefix block — always include
                try:
                    shapes_graph.parse(data=block, format="turtle")
                except Exception:
                    pass
                continue
            turtle_block = prefix_block + "\n# Rule:" + block
            try:
                shapes_graph.parse(data=turtle_block, format="turtle")
            except Exception:
                skipped += 1

        # Run pyshacl validation
        # Note: do NOT pass ont_graph — causes 'NoneType' error in some
        # pyshacl/rdflib version combinations. inference="none" is sufficient.
        conforms, results_graph, results_text = validate(
            data_graph,
            shacl_graph=shapes_graph,
            inference="none",
            abort_on_first=False,
            do_owl_imports=False,
        )

        # Parse violations from results graph
        violations = _parse_violations(results_graph)

        # Count entities
        entities = set()
        for s in data_graph.subjects():
            entities.add(str(s))

        return {
            "conforms": conforms,
            "total_violations": len(violations),
            "total_entities": len(entities),
            "violations": violations[:200],  # cap for UI
            "results_text": results_text[:5000] if results_text else "",
        }

    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        print(f"[validate] ERROR: {exc}\n{tb}")
        return JSONResponse(
            status_code=422,
            content={"error": str(exc), "detail": "Validation failed"},
        )


def _parse_violations(results_graph) -> list:
    """Extract structured violations from pyshacl results graph."""
    from rdflib import SH, RDF, Namespace
    SH_NS = Namespace("http://www.w3.org/ns/shacl#")

    violations = []
    for result in results_graph.subjects(RDF.type, SH_NS.ValidationResult):
        v = {}
        for p, o in results_graph.predicate_objects(result):
            pname = str(p).split("#")[-1]
            v[pname] = str(o)

        # Map to friendly names
        focus = v.get("focusNode", "")
        source = v.get("sourceShape", "")
        severity_raw = v.get("resultSeverity", "")
        message = v.get("resultMessage", "")
        path = v.get("resultPath", "")

        # Clean up URIs
        focus_label = focus.split("#")[-1] if "#" in focus else focus.split("/")[-1]
        source_label = source.split("#")[-1] if "#" in source else source.split("/")[-1]
        severity_label = severity_raw.split("#")[-1] if "#" in severity_raw else severity_raw
        path_label = path.split("#")[-1] if "#" in path else path.split("/")[-1]

        violations.append({
            "focus_node": focus_label,
            "focus_uri": focus,
            "source_shape": source_label,
            "source_uri": source,
            "severity": severity_label,
            "message": message[:300],
            "path": path_label,
        })

    # Sort: Violation > Warning > Info
    severity_order = {"Violation": 0, "Warning": 1, "Info": 2}
    violations.sort(key=lambda v: severity_order.get(v["severity"], 3))

    return violations


# ── Startup ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*60}")
    print(f"  PolicyChecker — Compliance Dashboard")
    print(f"  http://localhost:8000")
    print(f"{'='*60}\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
