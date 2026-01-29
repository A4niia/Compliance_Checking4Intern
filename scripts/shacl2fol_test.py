# Thesis Agent System - SHACL2FOL Test Script
# Tests whether SHACL2FOL can process your existing SHACL shapes

"""
SHACL2FOL COMPATIBILITY TEST

CRITICAL FINDING from GitHub README:
- SHACL2FOL only supports sh:NodeKind for filter components
- Your shapes use sh:sparql (SPARQL-based constraints)
- This may NOT be supported by SHACL2FOL

This script:
1. Converts your sh:sparql shapes to declarative SHACL (if possible)
2. Tests SHACL2FOL compatibility
3. Provides alternative verification approaches if SHACL2FOL doesn't work
"""

from pathlib import Path
import subprocess
import sys

# Your existing SHACL shape analysis
CURRENT_SHACL_ANALYSIS = """
==========================================================
SHACL2FOL COMPATIBILITY ANALYSIS
==========================================================

Your Current SHACL Shapes (from ait-shacl-rules.ttl):

1. ait:TuitionComplianceShape
   - Type: sh:NodeShape with sh:sparql constraint
   - Pattern: SPARQL-based validation
   - SHACL2FOL Support: ❓ UNCERTAIN (sh:sparql may not be supported)

2. ait:AccommodationComplianceShape  
   - Type: sh:NodeShape with sh:sparql constraint
   - Pattern: SPARQL-based validation
   - SHACL2FOL Support: ❓ UNCERTAIN (sh:sparql may not be supported)

==========================================================
ALTERNATIVE APPROACHES IF SHACL2FOL DOESN'T SUPPORT sh:sparql
==========================================================

Option A: Convert to Declarative SHACL
--------------------------------------
Instead of:
   sh:sparql [ sh:select "..." ]

Use declarative constraints like:
   sh:property [
     sh:path ait:hasStudentType ;
     sh:hasValue "Self-Support" ;
   ] ;
   sh:property [
     sh:path ait:hasEnrollmentStatus ;
     sh:hasValue "Enrolled" ;
   ]

LIMITATION: Declarative SHACL cannot express complex multi-hop 
queries that your sh:sparql constraints use.

Option B: Hybrid Verification Approach
--------------------------------------
1. Decompose each policy into atomic constraints
2. Verify atomic parts formally with SHACL2FOL
3. Verify composition manually or with testing
4. Document which parts are formally verified vs tested

Option C: Custom FOL Equivalence Checking
-----------------------------------------
1. Write FOL manually for each policy
2. Write FOL manually for SHACL semantics
3. Use Z3/Vampire to check equivalence
4. More work but doesn't depend on SHACL2FOL

RECOMMENDATION:
Start with Option B - it's pragmatic and still provides partial
formal verification, which is more than most related work has.

==========================================================
"""


def create_declarative_shacl_example():
    """Create example of declarative SHACL for comparison."""
    
    declarative_shacl = """# Declarative SHACL Version (for SHACL2FOL compatibility)
# This is an ALTERNATIVE representation of your rules
# NOTE: Less expressive than sh:sparql but formally verifiable

@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix ait:   <http://ait.ac.th/ontology#> .

# Rule 1: Tuition Compliance (Declarative Version)
# This checks individual properties but CANNOT check the combination
# as cleanly as the SPARQL version

ait:SelfSupportStudentShape
  a sh:NodeShape ;
  sh:targetClass ait:Student ;
  
  # Check: If student is Self-Support...
  sh:property [
    sh:path ait:hasStudentType ;
    sh:hasValue "Self-Support" ;
    sh:minCount 0 ;  # Not required - this is a conditional
  ] .

# The PROBLEM with declarative SHACL:
# We cannot express: "IF self-support AND enrolled AND has tuition obligation
#                     THEN that obligation must be paid"
# This requires SPARQL or very complex nested shapes.

# For SHACL2FOL, we may need to:
# 1. Simplify rules to what can be expressed declaratively
# 2. Accept that some rules require SPARQL (won't be formally verified)
# 3. Use hybrid approach (formal for simple, empirical for complex)
"""
    
    output_path = Path("ait-policy-prototype/ait-shacl-declarative.ttl")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(declarative_shacl)
    
    print(f"Created declarative SHACL example: {output_path}")


def print_shacl2fol_setup_instructions():
    """Print instructions for setting up SHACL2FOL."""
    
    instructions = """
==========================================================
SHACL2FOL SETUP INSTRUCTIONS
==========================================================

1. Download SHACL2FOL:
   git clone https://github.com/paolo7/SHACL2FOL.git
   
2. Install Prerequisites:
   - Java 21 or newer
   - Vampire theorem prover (recommended):
     https://github.com/vprover/vampire/releases
   - OR E Prover (alternative):
     https://wwwlehre.dhbw-stuttgart.de/~sschulz/E/E.html

3. Configure config.properties:
   prover_path=/path/to/vampire
   OR
   prover_path=/path/to/eprover

4. Test with simple shape:
   java -jar SHACL2FOL.jar s simple_shape.ttl

5. For your thesis shapes:
   java -jar SHACL2FOL.jar v ait-shacl-rules.ttl test_data.ttl

==========================================================
WINDOWS-SPECIFIC NOTES
==========================================================

Vampire typically runs on Linux. On Windows, you can:
- Use WSL (Windows Subsystem for Linux)
- Use a Docker container
- Use E Prover (has Windows builds)

Recommended for Windows:
   1. Install WSL2 with Ubuntu
   2. Install Vampire in WSL: 
      sudo apt install vampire
   3. Run SHACL2FOL from WSL

==========================================================
"""
    print(instructions)


def analyze_shacl_file(filepath: str):
    """Analyze a SHACL file for SHACL2FOL compatibility."""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis = {
            "file": filepath,
            "has_sparql": "sh:sparql" in content,
            "has_property": "sh:property" in content,
            "has_node_kind": "sh:nodeKind" in content,
            "has_class": "sh:class" in content,
            "has_datatype": "sh:datatype" in content,
            "has_min_count": "sh:minCount" in content,
            "has_max_count": "sh:maxCount" in content,
            "has_pattern": "sh:pattern" in content,
        }
        
        print(f"\n📋 SHACL Compatibility Analysis: {filepath}")
        print("-" * 50)
        
        if analysis["has_sparql"]:
            print("⚠️  Uses sh:sparql - MAY NOT be supported by SHACL2FOL")
        else:
            print("✅ No sh:sparql detected")
        
        supported_features = []
        for key, value in analysis.items():
            if key.startswith("has_") and key != "has_sparql" and value:
                feature = key.replace("has_", "sh:")
                supported_features.append(feature)
        
        if supported_features:
            print(f"✅ Supported features used: {', '.join(supported_features)}")
        
        return analysis
        
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return None


if __name__ == "__main__":
    print(CURRENT_SHACL_ANALYSIS)
    
    # Analyze your existing SHACL file
    analyze_shacl_file("ait-policy-prototype/ait-shacl-rules.ttl")
    
    # Create declarative example
    create_declarative_shacl_example()
    
    # Print setup instructions
    print_shacl2fol_setup_instructions()
    
    print("\n" + "="*60)
    print("NEXT STEPS FOR DIRECTION 3 (Formal Verification)")
    print("="*60)
    print("""
1. IMMEDIATE: Test SHACL2FOL with a simple declarative shape
   - If it works → proceed with declarative SHACL subset
   - If it fails → document and adjust thesis scope

2. DECISION POINT: 
   - Your sh:sparql shapes are more expressive but less verifiable
   - Consider: Is expressiveness or formal verification more important?

3. RECOMMENDATION:
   Use HYBRID approach:
   - Formally verify SIMPLE rules (declarative SHACL)
   - Empirically test COMPLEX rules (SPARQL-based SHACL)
   - Document the boundary clearly in thesis

4. THESIS CONTRIBUTION:
   This analysis itself is valuable! Document:
   - What CAN be formally verified
   - What CANNOT (and why)
   - The trade-off between expressiveness and verifiability
""")
