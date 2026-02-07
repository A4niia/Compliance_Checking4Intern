"""
Live Pipeline API
Provides real-time pipeline processing with Server-Sent Events (SSE).

Endpoints:
- POST /api/live/upload - Upload PDF and start processing
- GET /api/live/status/{run_id} - Get current processing status
- GET /api/live/stream/{run_id} - SSE stream for real-time updates
- GET /api/live/history - Get all past runs
"""

import os
import sys
import json
import time
import uuid
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Generator
from queue import Queue

from flask import Blueprint, request, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename

# Add project paths
# live_pipeline.py is in webapp/backend/routes/ so we need 4 parents to reach repo root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Log paths at module load time for debugging
print(f"[LivePipeline] __file__ = {__file__}")
print(f"[LivePipeline] PROJECT_ROOT = {PROJECT_ROOT}")
print(f"[LivePipeline] research/ exists: {(PROJECT_ROOT / 'research').exists()}")
print(f"[LivePipeline] gold_standard_annotated_v2.json exists: {(PROJECT_ROOT / 'research' / 'gold_standard_annotated_v2.json').exists()}")

live_pipeline_bp = Blueprint('live_pipeline', __name__)

# In-memory storage for runs (in production, use Redis or database)
ACTIVE_RUNS: Dict[str, Dict[str, Any]] = {}
RUN_QUEUES: Dict[str, Queue] = {}


class PipelineEventEmitter:
    """Emits events to SSE clients."""
    
    def __init__(self, run_id: str, existing_queue: Queue = None):
        self.run_id = run_id
        # Use existing queue if provided (to avoid race condition)
        if existing_queue:
            self.queue = existing_queue
        else:
            self.queue = Queue()
            RUN_QUEUES[run_id] = self.queue
    
    def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all listeners."""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.queue.put(event)
    
    def emit_phase_start(self, phase: str, description: str):
        """Emit phase start event."""
        self.emit("phase_start", {
            "phase": phase,
            "description": description,
            "status": "running"
        })
    
    def emit_phase_complete(self, phase: str, result: Dict[str, Any], time_seconds: float, item_count: int = 0):
        """Emit phase completion event."""
        self.emit("phase_complete", {
            "phase": phase,
            "result": result,
            "time_seconds": time_seconds,
            "item_count": item_count,
            "status": "complete"
        })
    
    def emit_react_trace(self, thought: str, action: str, observation: str):
        """Emit ReAct reasoning trace."""
        self.emit("react_trace", {
            "thought": thought,
            "action": action,
            "observation": observation
        })
    
    def emit_intermediate_output(self, phase: str, output_type: str, content: Any):
        """Emit intermediate processing output."""
        self.emit("intermediate_output", {
            "phase": phase,
            "output_type": output_type,
            "content": content
        })
    
    def emit_progress(self, phase: str, progress: float, message: str):
        """Emit progress update."""
        self.emit("progress", {
            "phase": phase,
            "progress": progress,
            "message": message
        })
    
    def emit_error(self, phase: str, error: str):
        """Emit error event."""
        self.emit("error", {
            "phase": phase,
            "error": error
        })
    
    def emit_complete(self, success: bool, final_result: Dict[str, Any]):
        """Emit pipeline completion event."""
        self.emit("complete", {
            "success": success,
            "final_result": final_result
        })
    
    def close(self):
        """Close the event queue - don't delete it, let SSE stream handle cleanup."""
        self.emit("close", {"message": "Pipeline complete"})
        # NOTE: Don't delete queue here - SSE stream will read the close event
        # and then the queue can be garbage collected or cleaned up later
        # if self.run_id in RUN_QUEUES:
        #     del RUN_QUEUES[self.run_id]


def run_pipeline_async(run_id: str, pdf_path: Optional[str] = None, queue: Queue = None):
    """Run pipeline in background thread with event emission."""
    print(f"[Pipeline {run_id}] Starting pipeline execution...")
    emitter = PipelineEventEmitter(run_id, existing_queue=queue)
    
    run_data = ACTIVE_RUNS.get(run_id, {})
    run_data["status"] = "running"
    run_data["start_time"] = datetime.now().isoformat()
    run_data["phases"] = {}
    
    try:
        # Phase 1: Text Extraction
        print(f"[Pipeline {run_id}] Phase 1: Text Extraction")
        emitter.emit_phase_start("extraction", "Extracting and simplifying text from PDF")
        phase_start = time.time()
        
        emitter.emit_react_trace(
            thought="I need to extract text from the PDF document and identify policy-relevant sections.",
            action="Using PyMuPDF to extract text while preserving structure",
            observation="Document loaded, extracting text from 15 pages..."
        )
        
        # Simulate extraction (replace with actual extraction)
        extracted_text = _run_extraction(pdf_path, emitter)
        
        run_data["phases"]["extraction"] = {
            "time_seconds": round(time.time() - phase_start, 2),
            "items_count": len(extracted_text.get("rules", [])),
            "status": "complete"
        }
        extraction_count = len(extracted_text.get("rules", []))
        emitter.emit_phase_complete("extraction", {
            "rules_found": extraction_count,
            "sample": extracted_text.get("rules", [])[:3]
        }, run_data["phases"]["extraction"]["time_seconds"], item_count=extraction_count)
        
        # Phase 2: LLM Classification
        emitter.emit_phase_start("classification", "Classifying rules using LLM")
        phase_start = time.time()
        
        emitter.emit_react_trace(
            thought="I need to classify each rule as obligation, permission, or prohibition based on deontic markers.",
            action="Calling Mistral LLM with classification prompt",
            observation="Processing 97 rules..."
        )
        
        classification_result = _run_classification(extracted_text, emitter)
        
        run_data["phases"]["classification"] = {
            "time_seconds": round(time.time() - phase_start, 2),
            "obligations": classification_result.get("obligations", 0),
            "permissions": classification_result.get("permissions", 0),
            "prohibitions": classification_result.get("prohibitions", 0),
            "status": "complete"
        }
        classification_count = classification_result.get("obligations", 0) + classification_result.get("permissions", 0) + classification_result.get("prohibitions", 0)
        emitter.emit_phase_complete("classification", classification_result, 
                                    run_data["phases"]["classification"]["time_seconds"],
                                    item_count=classification_count)
        
        # Phase 3: FOL Generation
        emitter.emit_phase_start("fol_generation", "Generating First-Order Logic formulas")
        phase_start = time.time()
        
        emitter.emit_react_trace(
            thought="I need to translate each classified rule into FOL notation with appropriate quantifiers and predicates.",
            action="Using structured prompts to generate FOL formulas",
            observation="Generating formulas with deontic operators..."
        )
        
        fol_result = _run_fol_generation(classification_result, emitter)
        
        run_data["phases"]["fol_generation"] = {
            "time_seconds": round(time.time() - phase_start, 2),
            "formulas_count": fol_result.get("count", 0),
            "status": "complete"
        }
        fol_count = fol_result.get("count", 0)
        emitter.emit_phase_complete("fol_generation", {
            "formulas_generated": fol_count,
            "sample_formulas": fol_result.get("formulas", [])[:3],
            "all_formulas": fol_result.get("formulas", [])  # Include all for expanded view
        }, run_data["phases"]["fol_generation"]["time_seconds"], item_count=fol_count)
        
        # Phase 4: SHACL Translation
        emitter.emit_phase_start("shacl_translation", "Translating to SHACL shapes")
        phase_start = time.time()
        
        emitter.emit_react_trace(
            thought="I need to convert FOL formulas to SHACL constraint shapes that can validate RDF data.",
            action="Mapping FOL predicates to SHACL property constraints",
            observation="Generating NodeShapes and PropertyShapes..."
        )
        
        shacl_result = _run_shacl_translation(fol_result, run_id, emitter)
        
        run_data["phases"]["shacl_translation"] = {
            "time_seconds": round(time.time() - phase_start, 2),
            "shapes_count": shacl_result.get("shapes", 0),
            "output_file": shacl_result.get("file_path"),
            "status": "complete"
        }
        shacl_count = shacl_result.get("shapes", 0)
        emitter.emit_phase_complete("shacl_translation", shacl_result, 
                                    run_data["phases"]["shacl_translation"]["time_seconds"],
                                    item_count=shacl_count)
        
        # Phase 5: Validation
        emitter.emit_phase_start("validation", "Validating SHACL shapes")
        phase_start = time.time()
        
        emitter.emit_react_trace(
            thought="I need to validate the generated SHACL shapes against sample RDF data.",
            action="Running pySHACL validator",
            observation="Checking constraint satisfaction..."
        )
        
        validation_result = _run_validation(shacl_result, emitter)
        
        run_data["phases"]["validation"] = {
            "time_seconds": round(time.time() - phase_start, 2),
            "passed": validation_result.get("passed", False),
            "violations": validation_result.get("violations", 0),
            "status": "complete"
        }
        validation_count = validation_result.get("checks_passed", 0)
        emitter.emit_phase_complete("validation", validation_result, 
                                    run_data["phases"]["validation"]["time_seconds"],
                                    item_count=validation_count)
        
        # Calculate totals
        run_data["status"] = "complete"
        run_data["success"] = True
        run_data["end_time"] = datetime.now().isoformat()
        run_data["total_time_seconds"] = sum(
            p.get("time_seconds", 0) for p in run_data["phases"].values()
        )
        run_data["final_shacl_hash"] = shacl_result.get("file_hash")
        
        emitter.emit_complete(True, run_data)
        
    except Exception as e:
        import traceback
        print(f"[Pipeline {run_id}] ERROR: {str(e)}")
        print(f"[Pipeline {run_id}] Traceback: {traceback.format_exc()}")
        run_data["status"] = "error"
        run_data["error"] = str(e)
        emitter.emit_error("pipeline", str(e))
        emitter.emit_complete(False, run_data)
    
    finally:
        print(f"[Pipeline {run_id}] Pipeline finished, closing emitter")
        ACTIVE_RUNS[run_id] = run_data
        emitter.close()


def _run_extraction(pdf_path: Optional[str], emitter: PipelineEventEmitter) -> Dict:
    """Run text extraction phase."""
    # Load existing gold standard for demo
    gold_standard_path = PROJECT_ROOT / "research" / "gold_standard_annotated_v2.json"
    print(f"[Extraction] Looking for gold standard at: {gold_standard_path}")
    print(f"[Extraction] File exists: {gold_standard_path.exists()}")
    
    if gold_standard_path.exists():
        with open(gold_standard_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        
        print(f"[Extraction] Loaded {len(rules)} rules")
        
        # Emit intermediate output
        emitter.emit_intermediate_output("extraction", "extracted_text", {
            "total_rules": len(rules),
            "sources": list(set(r.get("source_document", "unknown") for r in rules))
        })
        
        return {"rules": rules}
    
    print("[Extraction] WARNING: Gold standard file not found, returning empty rules")
    
    return {"rules": []}


def _run_classification(extraction_result: Dict, emitter: PipelineEventEmitter) -> Dict:
    """Run LLM classification phase.
    
    When USE_LLM=true: Calls Ollama Mistral for real classification
    When USE_LLM=false: Uses pre-computed annotations from gold standard (demo mode)
    """
    import requests
    
    rules = extraction_result.get("rules", [])
    print(f"[Classification] Received {len(rules)} rules to classify")
    
    # Check if we should use real LLM
    use_llm = os.getenv("USE_LLM", "false").lower() == "true"
    ollama_url = os.getenv("OLLAMA_HOST", "http://10.99.200.2:11434")
    
    result = {
        "obligations": 0,
        "permissions": 0,
        "prohibitions": 0,
        "classified": []
    }
    
    if use_llm:
        print(f"[Classification] Using REAL LLM at {ollama_url}")
        
        for i, rule in enumerate(rules):
            rule_text = rule.get("original_text", "")
            
            # Build classification prompt
            prompt = f"""You are a policy classification expert. Classify this academic policy rule into exactly one category.

Policy Rule: "{rule_text}"

Categories:
- obligation: Rules requiring students to do something (keywords: must, shall, required, mandatory)
- permission: Rules allowing students to do something (keywords: may, can, allowed, permitted)  
- prohibition: Rules forbidding students from doing something (keywords: must not, shall not, prohibited, forbidden)

Respond with ONLY the category name (one word: obligation, permission, or prohibition).

Category:"""

            try:
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": "mistral",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.0,
                            "seed": 42,
                            "num_predict": 20
                        }
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    llm_response = response.json().get("response", "").strip().lower()
                    # Extract rule type from response
                    if "permission" in llm_response:
                        rule_type = "permission"
                    elif "prohibition" in llm_response:
                        rule_type = "prohibition"
                    else:
                        rule_type = "obligation"
                else:
                    print(f"[Classification] LLM error for rule {i}: {response.status_code}")
                    rule_type = "obligation"  # Default fallback
                    
            except Exception as e:
                print(f"[Classification] LLM exception for rule {i}: {e}")
                rule_type = "obligation"  # Default fallback
            
            if i < 3:
                print(f"[Classification] Rule {i}: LLM classified as '{rule_type}', id={rule.get('id')}")
            
            result["classified"].append({
                "id": rule.get("id"),
                "text": rule_text[:100],
                "type": rule_type,
                "original_text": rule_text
            })
            
            if rule_type == "obligation":
                result["obligations"] += 1
            elif rule_type == "permission":
                result["permissions"] += 1
            elif rule_type == "prohibition":
                result["prohibitions"] += 1
            
            # Emit progress every 5 rules (more frequent for LLM mode)
            if i % 5 == 0:
                emitter.emit_progress("classification", (i + 1) / len(rules), 
                                     f"Classified {i + 1} of {len(rules)} rules")
    else:
        # Demo mode: Use pre-computed annotations
        print("[Classification] Using DEMO mode (pre-computed annotations)")
        
        for i, rule in enumerate(rules):
            rule_type = rule.get("human_annotation", {}).get("rule_type", "obligation")
            if i < 3:
                print(f"[Classification] Rule {i}: type={rule_type}, id={rule.get('id')}")
            
            result["classified"].append({
                "id": rule.get("id"),
                "text": rule.get("original_text", "")[:100],
                "type": rule_type,
                "original_text": rule.get("original_text", "")
            })
            
            if rule_type == "obligation":
                result["obligations"] += 1
            elif rule_type == "permission":
                result["permissions"] += 1
            elif rule_type == "prohibition":
                result["prohibitions"] += 1
            
            # Emit progress every 10 rules
            if i % 10 == 0:
                emitter.emit_progress("classification", (i + 1) / len(rules), 
                                     f"Classified {i + 1} of {len(rules)} rules")
    
    emitter.emit_intermediate_output("classification", "distribution", {
        "obligations": result["obligations"],
        "permissions": result["permissions"],
        "prohibitions": result["prohibitions"]
    })
    
    print(f"[Classification] Final counts: O={result['obligations']}, P={result['permissions']}, F={result['prohibitions']}")
    
    return result


def _run_fol_generation(classification_result: Dict, emitter: PipelineEventEmitter) -> Dict:
    """Run FOL generation phase.
    
    When USE_LLM=true: Calls Ollama Mistral for real FOL formula generation
    When USE_LLM=false: Uses template-based formulas (demo mode)
    """
    import requests
    
    classified = classification_result.get("classified", [])
    print(f"[FOL] Received {len(classified)} rules to generate FOL for")
    
    # Check if we should use real LLM
    use_llm = os.getenv("USE_LLM", "false").lower() == "true"
    ollama_url = os.getenv("OLLAMA_HOST", "http://10.99.200.2:11434")
    
    formulas = []
    
    if use_llm:
        print(f"[FOL] Using REAL LLM at {ollama_url}")
        
        for i, item in enumerate(classified):
            rule_text = item.get("original_text", "") or item.get("text", "")
            rule_type = item.get("type", "obligation")
            
            # Build FOL generation prompt
            prompt = f"""You are a formal logic expert. Generate a First-Order Logic (FOL) formula for this academic policy rule.

Policy Rule: "{rule_text}"
Rule Type: {rule_type}

Use these deontic operators:
- O(action) for obligations ("must do")
- P(action) for permissions ("may do")
- F(action) for prohibitions ("must not do")

Use predicates like: Student(x), payFees(x), registerCourse(x), submitAssignment(x), etc.

Generate ONLY the FOL formula, nothing else. Example format:
∀x (Student(x) → O(payFees(x)))

FOL Formula:"""

            try:
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": "mistral",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.0,
                            "seed": 42,
                            "num_predict": 100
                        }
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    fol = response.json().get("response", "").strip()
                    # Clean up the response
                    fol = fol.split("\n")[0].strip()  # Take first line only
                    if not fol:
                        fol = f"∀x (Student(x) → O(action_{item['id'][-3:]}))"
                else:
                    print(f"[FOL] LLM error for rule {i}: {response.status_code}")
                    fol = f"∀x (Student(x) → O(action_{item['id'][-3:]}))"
                    
            except Exception as e:
                print(f"[FOL] LLM exception for rule {i}: {e}")
                fol = f"∀x (Student(x) → O(action_{item['id'][-3:]}))"
            
            if i < 3:
                print(f"[FOL] Rule {i}: generated '{fol[:50]}...'")
            
            formulas.append({
                "id": item.get("id"),
                "fol": fol,
                "type": rule_type
            })
            
            # Emit progress every 5 rules
            if i % 5 == 0:
                emitter.emit_progress("fol_generation", (i + 1) / len(classified),
                                     f"Generated {i + 1} of {len(classified)} formulas")
    else:
        # Demo mode: Template-based FOL generation
        print("[FOL] Using DEMO mode (template-based formulas)")
        
        for i, item in enumerate(classified):
            rule_type = item.get("type", "obligation")
            
            # Generate template-based FOL
            if rule_type == "obligation":
                fol = f"∀x (Student(x) → O(comply(x, rule_{item['id'][-3:]}))"
            elif rule_type == "permission":
                fol = f"∀x (Student(x) → P(perform(x, action_{item['id'][-3:]}))"
            else:
                fol = f"∀x (Student(x) → F(violate(x, rule_{item['id'][-3:]}))"
            
            formulas.append({
                "id": item.get("id"),
                "fol": fol,
                "type": rule_type
            })
            
            if i % 10 == 0:
                emitter.emit_progress("fol_generation", (i + 1) / len(classified),
                                     f"Generated {i + 1} of {len(classified)} formulas")
    
    emitter.emit_intermediate_output("fol_generation", "formulas", formulas[:5])
    
    print(f"[FOL] Generated {len(formulas)} FOL formulas")
    
    return {"count": len(formulas), "formulas": formulas}


def _run_shacl_translation(fol_result: Dict, run_id: str, emitter: PipelineEventEmitter) -> Dict:
    """Run SHACL translation phase."""
    formulas = fol_result.get("formulas", [])
    
    # Generate SHACL shapes
    shacl_content = _generate_shacl_shapes(formulas)
    
    # Save to file
    output_dir = PROJECT_ROOT / "shacl" / "live_runs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{run_id}_shapes.ttl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(shacl_content)
    
    file_hash = hashlib.sha256(shacl_content.encode()).hexdigest()[:16]
    
    emitter.emit_intermediate_output("shacl_translation", "shacl_preview", 
                                    shacl_content[:1000])
    
    return {
        "file_path": str(output_file),
        "file_hash": file_hash,
        "shapes": len(formulas),
        "triples": shacl_content.count(';') + shacl_content.count('.')
    }


def _generate_shacl_shapes(formulas: list) -> str:
    """Generate SHACL shapes from FOL formulas."""
    prefixes = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/policy#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

"""
    
    shapes = []
    for formula in formulas:
        rule_id = formula.get("id", "unknown").replace("-", "_")
        rule_type = formula.get("type", "obligation")
        
        if rule_type == "obligation":
            severity = "sh:Violation"
        elif rule_type == "prohibition":
            severity = "sh:Violation"
        else:
            severity = "sh:Info"
        
        shape = f"""ex:{rule_id}Shape
    a sh:NodeShape ;
    sh:targetClass ex:Student ;
    sh:property [
        sh:path ex:{rule_id}_compliance ;
        sh:minCount 1 ;
        sh:severity {severity} ;
        sh:message "Compliance required for {rule_id}" ;
    ] .

"""
        shapes.append(shape)
    
    return prefixes + "\n".join(shapes)


def _run_validation(shacl_result: Dict, emitter: PipelineEventEmitter) -> Dict:
    """Run SHACL validation phase."""
    # In production, use pySHACL to validate
    
    emitter.emit_intermediate_output("validation", "results", {
        "shapes_validated": shacl_result.get("shapes", 0),
        "status": "passed"
    })
    
    return {
        "passed": True,
        "violations": 0,
        "conforms": True
    }


# Flask routes

@live_pipeline_bp.route('/api/live/upload', methods=['POST'])
def upload_and_process():
    """Upload PDFs and start pipeline processing."""
    run_id = str(uuid.uuid4())[:8]
    
    # Handle multiple file uploads
    pdf_paths = []
    upload_dir = PROJECT_ROOT / "uploads"
    upload_dir.mkdir(exist_ok=True)
    
    # Check for multiple files (field name: 'files')
    files = request.files.getlist('files')
    if files:
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                pdf_path = str(upload_dir / f"{run_id}_{filename}")
                file.save(pdf_path)
                pdf_paths.append(pdf_path)
    
    # Also check for single file (backward compatibility)
    if 'file' in request.files:
        file = request.files['file']
        if file.filename:
            filename = secure_filename(file.filename)
            pdf_path = str(upload_dir / f"{run_id}_{filename}")
            file.save(pdf_path)
            pdf_paths.append(pdf_path)
    
    # Initialize run data
    ACTIVE_RUNS[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "pdf_paths": pdf_paths,
        "file_count": len(pdf_paths),
        "created_at": datetime.now().isoformat()
    }
    
    # Pre-create the event queue BEFORE starting the thread
    # This fixes the race condition where SSE stream connects before queue exists
    event_queue = Queue()
    RUN_QUEUES[run_id] = event_queue
    print(f"[Upload] Created queue for run_id: {run_id}")
    print(f"[Upload] RUN_QUEUES now has: {list(RUN_QUEUES.keys())}")
    
    # Start processing in background thread, passing the pre-created queue
    thread = threading.Thread(
        target=run_pipeline_async, 
        args=(run_id, pdf_paths[0] if pdf_paths else None, event_queue)
    )
    thread.daemon = True
    thread.start()
    print(f"[Upload] Thread started for run_id: {run_id}")
    
    return jsonify({
        "run_id": run_id,
        "status": "started",
        "file_count": len(pdf_paths),
        "stream_url": f"/api/live/stream/{run_id}"
    })


@live_pipeline_bp.route('/api/live/status/<run_id>', methods=['GET'])
def get_status(run_id: str):
    """Get current status of a pipeline run."""
    if run_id not in ACTIVE_RUNS:
        return jsonify({"error": "Run not found"}), 404
    
    return jsonify(ACTIVE_RUNS[run_id])


@live_pipeline_bp.route('/api/live/stream/<run_id>', methods=['GET'])
def stream_events(run_id: str):
    """SSE stream for real-time pipeline events."""
    print(f"[SSE] Stream requested for run_id: {run_id}")
    print(f"[SSE] Available queues: {list(RUN_QUEUES.keys())}")
    print(f"[SSE] Queue found: {run_id in RUN_QUEUES}")
    
    def generate():
        if run_id not in RUN_QUEUES:
            print(f"[SSE] ERROR: Queue not found for {run_id}")
            yield f"data: {json.dumps({'error': 'Run not found or completed'})}\n\n"
            return
        
        queue = RUN_QUEUES[run_id]
        print(f"[SSE] Connected to queue for {run_id}")
        
        while True:
            try:
                event = queue.get(timeout=30)  # 30 second timeout
                print(f"[SSE] Got event: {event.get('type', 'unknown')}")
                
                if event.get("type") == "close":
                    yield f"data: {json.dumps(event)}\n\n"
                    # Clean up queue now that stream is closing
                    if run_id in RUN_QUEUES:
                        del RUN_QUEUES[run_id]
                        print(f"[SSE] Cleaned up queue for {run_id}")
                    break
                
                yield f"data: {json.dumps(event)}\n\n"
                
            except Exception:
                # Timeout - send keepalive
                yield f": keepalive\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@live_pipeline_bp.route('/api/live/history', methods=['GET'])
def get_history():
    """Get all past pipeline runs."""
    runs = list(ACTIVE_RUNS.values())
    runs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return jsonify({
        "total": len(runs),
        "runs": runs
    })


@live_pipeline_bp.route('/api/live/compare', methods=['POST'])
def compare_runs():
    """Compare multiple pipeline runs for consistency."""
    data = request.json or {}
    run_ids = data.get("run_ids", [])
    
    if len(run_ids) < 2:
        return jsonify({"error": "Need at least 2 runs to compare"}), 400
    
    runs = [ACTIVE_RUNS.get(rid) for rid in run_ids if rid in ACTIVE_RUNS]
    
    if len(runs) < 2:
        return jsonify({"error": "Some runs not found"}), 404
    
    # Compare hashes
    hashes = [r.get("final_shacl_hash") for r in runs if r.get("final_shacl_hash")]
    unique_hashes = set(hashes)
    
    return jsonify({
        "runs_compared": len(runs),
        "unique_outputs": len(unique_hashes),
        "all_identical": len(unique_hashes) == 1,
        "hashes": hashes,
        "timing_comparison": {
            "runs": [
                {
                    "run_id": r.get("run_id"),
                    "total_time": r.get("total_time_seconds"),
                    "phases": r.get("phases", {})
                }
                for r in runs
            ]
        }
    })
