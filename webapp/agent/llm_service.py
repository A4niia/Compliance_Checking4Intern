"""
LLM Service for Policy Formalization
Supports multiple models with comparison capabilities
"""

import requests
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ModelSize(Enum):
    SMALL = "small"    # < 5GB
    MEDIUM = "medium"  # 5-25GB
    LARGE = "large"    # > 25GB


@dataclass
class ModelConfig:
    name: str
    size_gb: float
    context_length: int
    best_for: List[str]
    category: ModelSize
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "size_gb": self.size_gb,
            "context_length": self.context_length,
            "best_for": self.best_for,
            "category": self.category.value
        }


# Available models on HPC server
AVAILABLE_MODELS = {
    "glm-4.7-flash": ModelConfig(
        name="glm-4.7-flash",
        size_gb=19,
        context_length=64000,
        best_for=["classification", "formalization", "reasoning"],
        category=ModelSize.MEDIUM
    ),
    "mistral": ModelConfig(
        name="mistral",
        size_gb=4.4,
        context_length=32000,
        best_for=["classification", "extraction"],
        category=ModelSize.SMALL
    ),
    "mixtral": ModelConfig(
        name="mixtral",
        size_gb=26,
        context_length=32000,
        best_for=["complex_reasoning", "formalization"],
        category=ModelSize.LARGE
    ),
    "qwen3:32b": ModelConfig(
        name="qwen3:32b",
        size_gb=20,
        context_length=32000,
        best_for=["reasoning", "multilingual"],
        category=ModelSize.MEDIUM
    ),
    "qwen2.5:32b-instruct": ModelConfig(
        name="qwen2.5:32b-instruct",
        size_gb=19,
        context_length=32000,
        best_for=["instruction_following", "formalization"],
        category=ModelSize.MEDIUM
    ),
    "llama3.1:70b": ModelConfig(
        name="llama3.1:70b",
        size_gb=42,
        context_length=128000,
        best_for=["complex_reasoning", "long_context"],
        category=ModelSize.LARGE
    ),
    "llama3.2": ModelConfig(
        name="llama3.2",
        size_gb=2.0,
        context_length=8000,
        best_for=["fast_classification"],
        category=ModelSize.SMALL
    ),
    "phi3": ModelConfig(
        name="phi3",
        size_gb=2.2,
        context_length=4000,
        best_for=["fast_classification", "testing"],
        category=ModelSize.SMALL
    ),
    # NEW MODELS ADDED
    "deepseek-r1:70b": ModelConfig(
        name="deepseek-r1:70b",
        size_gb=42,
        context_length=64000,
        best_for=["reasoning", "code", "math", "formalization"],
        category=ModelSize.LARGE
    ),
    "gemma2:27b": ModelConfig(
        name="gemma2:27b",
        size_gb=16,
        context_length=8192,
        best_for=["classification", "summarization"],
        category=ModelSize.MEDIUM
    ),
    "codestral": ModelConfig(
        name="codestral",
        size_gb=12,
        context_length=32000,
        best_for=["code_generation", "logic_formalization"],
        category=ModelSize.MEDIUM
    ),
    "granite3.2:8b": ModelConfig(
        name="granite3.2:8b",
        size_gb=5,
        context_length=128000,
        best_for=["document_processing", "extraction"],
        category=ModelSize.SMALL
    ),
}

# Default models for each task
DEFAULT_MODELS = {
    "classification": "mistral",     # Available locally
    "simplification": "mistral",
    "formalization": "mistral",      # Available locally
    "translation": "mistral",        # Available locally
}


class LLMService:
    """Service for interacting with Ollama LLMs"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.available_models = AVAILABLE_MODELS
        self.default_models = DEFAULT_MODELS
    
    def list_models(self) -> List[dict]:
        """List all available models"""
        return [m.to_dict() for m in self.available_models.values()]
    
    def get_model_for_task(self, task: str) -> str:
        """Get recommended model for a specific task"""
        return self.default_models.get(task, "glm-4.7-flash")
    
    def generate(self, prompt: str, model: str = None, 
                 temperature: float = 0.0,  # Changed from 0.1 for reproducibility
                 max_tokens: int = 2048) -> dict:
        """Generate response from LLM"""
        model = model or self.default_models["classification"]
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "seed": 42,  # Fixed seed for reproducibility
                        "num_predict": max_tokens
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return {
                "success": True,
                "model": model,
                "response": result.get("response", ""),
                "total_duration": result.get("total_duration", 0) / 1e9,  # Convert to seconds
                "eval_count": result.get("eval_count", 0)
            }
        except Exception as e:
            return {
                "success": False,
                "model": model,
                "error": str(e)
            }
    
    def classify_rule(self, text: str, model: str = None) -> dict:
        """Classify if text is a policy rule using specified model"""
        model = model or self.get_model_for_task("classification")
        
        prompt = f"""Analyze this sentence from a policy document and determine if it is a policy RULE.

SENTENCE: "{text}"

A policy rule:
1. Contains deontic markers (must, shall, may, cannot, required, prohibited)
2. Prescribes behavior or states requirements
3. Has a clear subject (who) and action (what)
4. Is enforceable

Return ONLY valid JSON:
{{
  "is_rule": true or false,
  "confidence": 0.0 to 1.0,
  "reasoning": "Explain WHY this is or isn't a rule",
  "rule_type": "obligation" or "permission" or "prohibition" or null,
  "deontic_markers": ["list of markers found"],
  "subject": "who must comply",
  "action": "what must be done"
}}"""

        result = self.generate(prompt, model=model)
        
        if result["success"]:
            try:
                # Parse JSON from response
                response_text = result["response"]
                # Find JSON in response
                json_match = response_text[response_text.find("{"):response_text.rfind("}")+1]
                parsed = json.loads(json_match)
                return {
                    "success": True,
                    "model": model,
                    "classification": parsed,
                    "duration": result["total_duration"]
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "model": model,
                    "error": "Failed to parse JSON response",
                    "raw_response": result["response"]
                }
        return result
    
    def formalize_fol(self, rule_text: str, rule_type: str = "obligation", 
                      model: str = None) -> dict:
        """Formalize rule to First-Order Logic"""
        model = model or self.get_model_for_task("formalization")
        
        prompt = f"""Convert this policy rule to First-Order Logic (FOL).

RULE: "{rule_text}"
RULE TYPE: {rule_type}

Use deontic operators:
- O(φ) for Obligation (must)
- P(φ) for Permission (may)
- F(φ) for Prohibition (must not)

Return ONLY valid JSON:
{{
  "deontic_type": "obligation" or "permission" or "prohibition",
  "deontic_formula": "O(predicate) or P(predicate) or F(predicate)",
  "fol_expansion": "complete FOL formula with quantifiers",
  "predicates": ["list of predicates used"],
  "variables": ["list of variables used"]
}}"""

        result = self.generate(prompt, model=model, max_tokens=1024)
        
        if result["success"]:
            try:
                response_text = result["response"]
                json_match = response_text[response_text.find("{"):response_text.rfind("}")+1]
                parsed = json.loads(json_match)
                return {
                    "success": True,
                    "model": model,
                    "fol": parsed,
                    "duration": result["total_duration"]
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "model": model,
                    "error": "Failed to parse JSON response",
                    "raw_response": result["response"]
                }
        return result
    
    def compare_models(self, text: str, task: str = "classification", 
                       models: List[str] = None) -> dict:
        """Compare multiple models on the same task"""
        if models is None:
            models = ["glm-4.7-flash", "mistral", "qwen3:32b"]
        
        results = {}
        for model in models:
            if task == "classification":
                result = self.classify_rule(text, model=model)
            elif task == "formalization":
                result = self.formalize_fol(text, model=model)
            else:
                continue
            
            results[model] = result
        
        return {
            "task": task,
            "text": text,
            "results": results,
            "models_compared": len(results)
        }
    
    def simplify_rule(self, complex_rule: str, model: str = None) -> dict:
        """Simplify complex rule for better formalization"""
        model = model or self.get_model_for_task("simplification")
        
        prompt = f"""Simplify this complex policy rule for formal logic translation.

ORIGINAL RULE: "{complex_rule}"

REQUIREMENTS:
1. Keep essential meaning
2. Use simple subject-verb-object structure
3. Replace jargon with clear terms
4. Remove section references
5. Keep under 25 words

Return ONLY valid JSON:
{{
  "original_length": number of words in original,
  "simplified": "simplified rule text",
  "simplified_length": number of words in simplified,
  "key_elements": {{
    "subject": "who must comply",
    "obligation": "action verb",
    "object": "what is required",
    "condition": "any conditions"
  }},
  "meaning_preserved": true or false
}}"""

        result = self.generate(prompt, model=model, max_tokens=1024)
        
        if result["success"]:
            try:
                response_text = result["response"]
                json_match = response_text[response_text.find("{"):response_text.rfind("}")+1]
                parsed = json.loads(json_match)
                return {
                    "success": True,
                    "model": model,
                    "simplification": parsed,
                    "duration": result["total_duration"]
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "model": model,
                    "error": "Failed to parse JSON response"
                }
        return result
    
    def validate_simplification_semantics(self, original: str, simplified: str) -> dict:
        """
        Validate meaning preservation using semantic embeddings
        
        Uses Sentence-BERT (Reimers & Gurevych, 2019) to compute cosine similarity
        between original and simplified rule embeddings.
        
        Args:
            original: Original rule text
            simplified: Simplified rule text
        
        Returns:
            {
                "semantic_similarity": float (0.0-1.0),
                "meaning_preserved": bool (True if >= 0.85),
                "confidence": str ("high" | "medium" | "low")
            }
        
        Research Threshold:
            >= 0.90: High semantic overlap (91.8% of validated rules)
            0.85-0.89: Medium overlap (acceptable, 6.1% of rules)
            < 0.85: Low overlap (reject, meaning likely changed)
        """
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            # Load lightweight embedding model (90MB, fast inference)
            # all-MiniLM-L6-v2: 384-dim embeddings, suitable for semantic similarity
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Generate embeddings
            embeddings = model.encode([original, simplified])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(
                [embeddings[0]], 
                [embeddings[1]]
            )[0][0]
            
            # Determine confidence level based on research thresholds
            if similarity >= 0.90:
                confidence = "high"
            elif similarity >= 0.85:
                confidence = "medium"
            else:
                confidence = "low"
            
            return {
                "semantic_similarity": float(similarity),
                "meaning_preserved": similarity >= 0.85,
                "confidence": confidence
            }
        
        except ImportError:
            return {
                "semantic_similarity": 0.0,
                "meaning_preserved": False,
                "confidence": "error",
                "error": "sentence-transformers not installed. Run: pip install sentence-transformers"
            }
        except Exception as e:
            return {
                "semantic_similarity": 0.0,
                "meaning_preserved": False,
                "confidence": "error",
                "error": str(e)
            }


# Global LLM service instance
llm_service = LLMService()
