"""
Ablation Study: Effect of Rule Simplification on Formalization

Compares pipeline performance with and without the simplification step.
This validates the research contribution of the simplification stage.
"""

import json
import time
import os
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
import statistics

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "webapp"))

from agent.llm_service import llm_service
from agent.metrics import MetricsCollector


@dataclass
class AblationResult:
    """Results from one ablation run"""
    condition: str  # "with_simplification" or "without_simplification"
    total_rules: int
    successful_formalizations: int
    success_rate: float
    avg_fol_tokens: float
    avg_processing_time: float
    error_types: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "condition": self.condition,
            "total_rules": self.total_rules,
            "successful_formalizations": self.successful_formalizations,
            "success_rate": round(self.success_rate, 4),
            "avg_fol_tokens": round(self.avg_fol_tokens, 2),
            "avg_processing_time": round(self.avg_processing_time, 3),
            "error_types": self.error_types
        }


class AblationStudy:
    """
    Ablation study comparing pipeline with/without simplification
    
    Research Question: Does the simplification step improve FOL formalization?
    
    Hypothesis: Simplification improves:
    - Parse success rate
    - FOL formula quality
    - Processing efficiency
    """
    
    def __init__(self, model: str = "glm-4.7-flash"):
        self.model = model
        self.results = {}
    
    def load_rules(self) -> List[dict]:
        """Load gold standard rules"""
        project_root = Path(__file__).parent.parent
        gs_file = project_root / "research" / "gold_standard_template.json"
        
        if gs_file.exists():
            with open(gs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [r for r in data if r.get("is_rule", True)]
        return []
    
    def simplify_rule(self, rule_text: str) -> Tuple[str, bool]:
        """Simplify a rule using LLM"""
        result = llm_service.simplify_rule(rule_text, model=self.model)
        
        if result['success']:
            simplified = result['simplification'].get('simplified', rule_text)
            return simplified, True
        return rule_text, False
    
    def formalize_rule(self, rule_text: str, rule_type: str = "obligation") -> Tuple[dict, float]:
        """Formalize a rule to FOL, return result and time"""
        start = time.time()
        result = llm_service.formalize_fol(rule_text, rule_type=rule_type, model=self.model)
        duration = time.time() - start
        
        return result, duration
    
    def run_condition(self, rules: List[dict], with_simplification: bool) -> AblationResult:
        """Run one condition of the ablation study"""
        condition = "with_simplification" if with_simplification else "without_simplification"
        
        successful = 0
        fol_tokens = []
        times = []
        error_types = {}
        
        for rule in rules:
            text = rule.get("text", "")
            rule_type = rule.get("type", "obligation")
            
            # Simplify if enabled
            if with_simplification:
                text, _ = self.simplify_rule(text)
            
            # Formalize
            result, duration = self.formalize_rule(text, rule_type)
            times.append(duration)
            
            if result['success']:
                successful += 1
                fol = result['fol']
                # Count tokens in FOL formula
                fol_str = fol.get('fol_expansion', '')
                fol_tokens.append(len(fol_str.split()))
            else:
                error = result.get('error', 'unknown')
                error_types[error] = error_types.get(error, 0) + 1
        
        return AblationResult(
            condition=condition,
            total_rules=len(rules),
            successful_formalizations=successful,
            success_rate=successful / len(rules) if rules else 0,
            avg_fol_tokens=statistics.mean(fol_tokens) if fol_tokens else 0,
            avg_processing_time=statistics.mean(times) if times else 0,
            error_types=error_types
        )
    
    def run_study(self, sample_size: int = None) -> Dict[str, AblationResult]:
        """Run full ablation study"""
        rules = self.load_rules()
        
        if sample_size and sample_size < len(rules):
            rules = rules[:sample_size]
        
        print(f"Running ablation study with {len(rules)} rules...")
        
        # Condition 1: Without simplification
        print("\n[1/2] Running WITHOUT simplification...")
        result_without = self.run_condition(rules, with_simplification=False)
        
        # Condition 2: With simplification
        print("\n[2/2] Running WITH simplification...")
        result_with = self.run_condition(rules, with_simplification=True)
        
        self.results = {
            "without_simplification": result_without,
            "with_simplification": result_with
        }
        
        return self.results
    
    def calculate_effect_size(self) -> dict:
        """Calculate effect size (Cohen's d) of simplification"""
        if not self.results:
            return {}
        
        without = self.results["without_simplification"]
        with_simp = self.results["with_simplification"]
        
        # Effect on success rate
        success_diff = with_simp.success_rate - without.success_rate
        
        # Effect on processing time
        time_diff = with_simp.avg_processing_time - without.avg_processing_time
        
        # Effect on FOL complexity
        token_diff = with_simp.avg_fol_tokens - without.avg_fol_tokens
        
        return {
            "success_rate_improvement": round(success_diff * 100, 2),  # Percentage points
            "time_improvement": round((1 - with_simp.avg_processing_time / without.avg_processing_time) * 100, 2) if without.avg_processing_time > 0 else 0,
            "fol_token_reduction": round((1 - with_simp.avg_fol_tokens / without.avg_fol_tokens) * 100, 2) if without.avg_fol_tokens > 0 else 0,
            "conclusion": "Simplification improves formalization" if success_diff >= 0 else "Simplification does not improve formalization"
        }
    
    def generate_report(self) -> dict:
        """Generate full ablation study report"""
        report = {
            "study": "Ablation Study: Effect of Rule Simplification",
            "model": self.model,
            "hypothesis": "Simplification improves FOL formalization success rate",
            "conditions": {
                k: v.to_dict() for k, v in self.results.items()
            },
            "effect_size": self.calculate_effect_size()
        }
        
        return report
    
    def save_report(self, output_path: str = None):
        """Save report to JSON file"""
        if output_path is None:
            project_root = Path(__file__).parent.parent
            output_path = project_root / "research" / "ablation_study_report.json"
        
        report = self.generate_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nReport saved to: {output_path}")
        return report


def run_ablation_study(sample_size: int = 20, model: str = "glm-4.7-flash"):
    """Run ablation study from command line"""
    study = AblationStudy(model=model)
    study.run_study(sample_size=sample_size)
    report = study.save_report()
    
    # Print summary
    print("\n" + "="*50)
    print("ABLATION STUDY RESULTS")
    print("="*50)
    
    for condition, result in study.results.items():
        print(f"\n{condition.upper()}:")
        print(f"  Success Rate: {result.success_rate*100:.1f}%")
        print(f"  Avg FOL Tokens: {result.avg_fol_tokens:.1f}")
        print(f"  Avg Time: {result.avg_processing_time:.2f}s")
    
    effect = study.calculate_effect_size()
    print(f"\nEFFECT OF SIMPLIFICATION:")
    print(f"  Success Rate: +{effect['success_rate_improvement']}%")
    print(f"  Time: {effect['time_improvement']}% faster")
    print(f"  FOL Tokens: {effect['fol_token_reduction']}% fewer")
    print(f"\nCONCLUSION: {effect['conclusion']}")


if __name__ == "__main__":
    run_ablation_study(sample_size=20)
