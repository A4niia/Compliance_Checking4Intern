"""
GraphDB Service for SHACL Validation
Connects to GraphDB for storing and validating SHACL shapes
"""

import requests
import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result from SHACL validation"""
    conforms: bool
    violations: List[dict]
    total_shapes: int
    shapes_tested: int
    
    def to_dict(self) -> dict:
        return {
            "conforms": self.conforms,
            "violation_count": len(self.violations),
            "violations": self.violations[:10],  # First 10
            "total_shapes": self.total_shapes,
            "shapes_tested": self.shapes_tested
        }


class GraphDBService:
    """
    GraphDB integration for SHACL validation
    
    Supports:
    - Uploading SHACL shapes to repository
    - Running validation against data
    - Retrieving validation reports
    """
    
    def __init__(self, base_url: str = None, repository: str = "policy-rules"):
        self.base_url = base_url or os.getenv("GRAPHDB_URL", "http://localhost:7200")
        self.repository = repository
        self.shapes_graph = "http://ait.ac.th/policy/shapes"
        self.data_graph = "http://ait.ac.th/policy/data"
    
    @property
    def sparql_endpoint(self) -> str:
        return f"{self.base_url}/repositories/{self.repository}"
    
    @property
    def statements_endpoint(self) -> str:
        return f"{self.base_url}/repositories/{self.repository}/statements"
    
    def health_check(self) -> bool:
        """Check if GraphDB is accessible"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/repositories",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def create_repository(self) -> bool:
        """Create repository if it doesn't exist"""
        config = f"""
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
        @prefix rep: <http://www.openrdf.org/config/repository#>.
        @prefix sr: <http://www.openrdf.org/config/repository/sail#>.
        @prefix sail: <http://www.openrdf.org/config/sail#>.
        @prefix graphdb: <http://www.ontotext.com/config/graphdb#>.

        [] a rep:Repository ;
            rep:repositoryID "{self.repository}" ;
            rdfs:label "Policy Rules Repository" ;
            rep:repositoryImpl [
                rep:repositoryType "graphdb:SailRepository" ;
                sr:sailImpl [
                    sail:sailType "graphdb:Sail" ;
                    graphdb:ruleset "rdfsplus-optimized"
                ]
            ].
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/rest/repositories",
                headers={"Content-Type": "text/turtle"},
                data=config,
                timeout=30
            )
            return response.status_code in [200, 201, 204]
        except Exception as e:
            print(f"Failed to create repository: {e}")
            return False
    
    def upload_shapes(self, ttl_content: str) -> dict:
        """Upload SHACL shapes to GraphDB"""
        try:
            response = requests.post(
                self.statements_endpoint,
                headers={
                    "Content-Type": "text/turtle",
                },
                params={
                    "context": f"<{self.shapes_graph}>"
                },
                data=ttl_content,
                timeout=30
            )
            
            return {
                "success": response.status_code in [200, 201, 204],
                "status_code": response.status_code,
                "message": "Shapes uploaded successfully" if response.ok else response.text
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def upload_test_data(self, ttl_content: str) -> dict:
        """Upload test data for validation"""
        try:
            response = requests.post(
                self.statements_endpoint,
                headers={
                    "Content-Type": "text/turtle",
                },
                params={
                    "context": f"<{self.data_graph}>"
                },
                data=ttl_content,
                timeout=30
            )
            
            return {
                "success": response.status_code in [200, 201, 204],
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate(self) -> ValidationResult:
        """Run SHACL validation against data"""
        # GraphDB SHACL validation query
        query = """
        PREFIX sh: <http://www.w3.org/ns/shacl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?shape ?focusNode ?resultPath ?message ?severity
        WHERE {
            GRAPH <http://ait.ac.th/policy/validation> {
                ?report a sh:ValidationReport ;
                        sh:result ?result .
                ?result sh:focusNode ?focusNode ;
                        sh:resultPath ?resultPath ;
                        sh:resultMessage ?message ;
                        sh:resultSeverity ?severity .
                OPTIONAL { ?result sh:sourceShape ?shape }
            }
        }
        """
        
        try:
            response = requests.post(
                self.sparql_endpoint,
                headers={
                    "Accept": "application/sparql-results+json",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"query": query},
                timeout=60
            )
            
            if response.ok:
                results = response.json()
                bindings = results.get("results", {}).get("bindings", [])
                
                violations = []
                for b in bindings:
                    violations.append({
                        "shape": b.get("shape", {}).get("value", ""),
                        "focus_node": b.get("focusNode", {}).get("value", ""),
                        "path": b.get("resultPath", {}).get("value", ""),
                        "message": b.get("message", {}).get("value", ""),
                        "severity": b.get("severity", {}).get("value", "")
                    })
                
                return ValidationResult(
                    conforms=len(violations) == 0,
                    violations=violations,
                    total_shapes=self._count_shapes(),
                    shapes_tested=self._count_shapes()
                )
            else:
                return ValidationResult(
                    conforms=False,
                    violations=[{"error": response.text}],
                    total_shapes=0,
                    shapes_tested=0
                )
        except Exception as e:
            return ValidationResult(
                conforms=False,
                violations=[{"error": str(e)}],
                total_shapes=0,
                shapes_tested=0
            )
    
    def _count_shapes(self) -> int:
        """Count number of SHACL shapes in repository"""
        query = """
        PREFIX sh: <http://www.w3.org/ns/shacl#>
        SELECT (COUNT(?shape) as ?count)
        WHERE {
            GRAPH <http://ait.ac.th/policy/shapes> {
                ?shape a sh:NodeShape .
            }
        }
        """
        
        try:
            response = requests.post(
                self.sparql_endpoint,
                headers={
                    "Accept": "application/sparql-results+json",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"query": query},
                timeout=10
            )
            
            if response.ok:
                results = response.json()
                bindings = results.get("results", {}).get("bindings", [])
                if bindings:
                    return int(bindings[0].get("count", {}).get("value", 0))
            return 0
        except:
            return 0
    
    def clear_graphs(self) -> bool:
        """Clear shapes and data graphs"""
        update = f"""
        CLEAR GRAPH <{self.shapes_graph}> ;
        CLEAR GRAPH <{self.data_graph}>
        """
        
        try:
            response = requests.post(
                f"{self.sparql_endpoint}/statements",
                headers={"Content-Type": "application/sparql-update"},
                data=update,
                timeout=30
            )
            return response.status_code in [200, 204]
        except:
            return False


# Global service instance
graphdb_service = GraphDBService()
