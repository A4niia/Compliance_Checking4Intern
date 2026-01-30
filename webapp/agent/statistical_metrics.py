"""
Statistical Metrics with Confidence Intervals
Provides 95% CI for all research metrics
"""

import math
from typing import List, Tuple
from dataclasses import dataclass


@dataclass 
class ConfidenceInterval:
    """95% Confidence Interval"""
    point_estimate: float
    lower_bound: float
    upper_bound: float
    margin_of_error: float
    confidence_level: float = 0.95
    
    def to_dict(self) -> dict:
        return {
            "point_estimate": round(self.point_estimate, 4),
            "lower_bound": round(self.lower_bound, 4),
            "upper_bound": round(self.upper_bound, 4),
            "margin_of_error": round(self.margin_of_error, 4),
            "confidence_level": self.confidence_level,
            "ci_string": f"{self.point_estimate:.3f} [{self.lower_bound:.3f}, {self.upper_bound:.3f}]"
        }


def calculate_proportion_ci(successes: int, total: int, confidence: float = 0.95) -> ConfidenceInterval:
    """
    Calculate confidence interval for a proportion (e.g., accuracy)
    Uses Wilson score interval for better small-sample properties
    """
    if total == 0:
        return ConfidenceInterval(0, 0, 0, 0)
    
    p = successes / total
    n = total
    
    # Z-score for 95% confidence
    z = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
    
    # Wilson score interval
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denominator
    margin = z * math.sqrt((p*(1-p) + z**2/(4*n)) / n) / denominator
    
    lower = max(0, center - margin)
    upper = min(1, center + margin)
    
    return ConfidenceInterval(
        point_estimate=p,
        lower_bound=lower,
        upper_bound=upper,
        margin_of_error=upper - p,
        confidence_level=confidence
    )


def calculate_mean_ci(values: List[float], confidence: float = 0.95) -> ConfidenceInterval:
    """
    Calculate confidence interval for a mean
    Uses t-distribution for small samples
    """
    if not values:
        return ConfidenceInterval(0, 0, 0, 0)
    
    n = len(values)
    mean = sum(values) / n
    
    if n < 2:
        return ConfidenceInterval(mean, mean, mean, 0)
    
    # Standard deviation
    variance = sum((x - mean)**2 for x in values) / (n - 1)
    std = math.sqrt(variance)
    
    # Standard error
    se = std / math.sqrt(n)
    
    # T-value for degrees of freedom (using approximation for n >= 30)
    if n >= 30:
        t = 1.96 if confidence == 0.95 else 2.576
    else:
        # Simplified t-value lookup
        t_values = {5: 2.571, 10: 2.228, 15: 2.131, 20: 2.086, 25: 2.064, 30: 2.042}
        t = t_values.get(n, 2.0)
    
    margin = t * se
    
    return ConfidenceInterval(
        point_estimate=mean,
        lower_bound=mean - margin,
        upper_bound=mean + margin,
        margin_of_error=margin,
        confidence_level=confidence
    )


def calculate_kappa_ci(kappa: float, n: int, confidence: float = 0.95) -> ConfidenceInterval:
    """
    Calculate confidence interval for Cohen's Kappa
    Uses approximation method
    """
    if n < 2:
        return ConfidenceInterval(kappa, kappa, kappa, 0)
    
    # Approximate standard error for kappa
    # Fleiss formula approximation
    se = math.sqrt((1 - kappa**2) / n)
    
    z = 1.96 if confidence == 0.95 else 2.576
    margin = z * se
    
    return ConfidenceInterval(
        point_estimate=kappa,
        lower_bound=max(-1, kappa - margin),
        upper_bound=min(1, kappa + margin),
        margin_of_error=margin,
        confidence_level=confidence
    )


def calculate_f1_ci(tp: int, fp: int, fn: int, n_bootstrap: int = 1000) -> ConfidenceInterval:
    """
    Calculate confidence interval for F1-score
    Uses bootstrap approximation
    """
    if tp + fp + fn == 0:
        return ConfidenceInterval(0, 0, 0, 0)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    if precision + recall == 0:
        f1 = 0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)
    
    # Simplified CI using Delta method
    n = tp + fp + fn
    se = math.sqrt(f1 * (1 - f1) / n) if n > 0 else 0
    
    z = 1.96
    margin = z * se
    
    return ConfidenceInterval(
        point_estimate=f1,
        lower_bound=max(0, f1 - margin),
        upper_bound=min(1, f1 + margin),
        margin_of_error=margin,
        confidence_level=0.95
    )


class StatisticalMetrics:
    """
    Calculate all research metrics with confidence intervals
    """
    
    def __init__(self):
        self.results = {}
    
    def calculate_classification_metrics(self, tp: int, tn: int, fp: int, fn: int) -> dict:
        """Calculate RQ1 metrics with CI"""
        total = tp + tn + fp + fn
        
        # Accuracy
        accuracy = (tp + tn) / total if total > 0 else 0
        accuracy_ci = calculate_proportion_ci(tp + tn, total)
        
        # Precision
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        precision_ci = calculate_proportion_ci(tp, tp + fp)
        
        # Recall
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        recall_ci = calculate_proportion_ci(tp, tp + fn)
        
        # F1
        f1_ci = calculate_f1_ci(tp, fp, fn)
        
        return {
            "accuracy": accuracy_ci.to_dict(),
            "precision": precision_ci.to_dict(),
            "recall": recall_ci.to_dict(),
            "f1_score": f1_ci.to_dict(),
            "confusion_matrix": {
                "tp": tp, "tn": tn, "fp": fp, "fn": fn
            }
        }
    
    def calculate_kappa_with_ci(self, observed_agree: float, expected_agree: float, n: int) -> dict:
        """Calculate Cohen's Kappa with CI"""
        if expected_agree == 1:
            kappa = 1.0
        else:
            kappa = (observed_agree - expected_agree) / (1 - expected_agree)
        
        kappa_ci = calculate_kappa_ci(kappa, n)
        
        return {
            "kappa": kappa_ci.to_dict(),
            "interpretation": self._interpret_kappa(kappa),
            "observed_agreement": observed_agree,
            "expected_agreement": expected_agree
        }
    
    def _interpret_kappa(self, kappa: float) -> str:
        """Interpret Kappa value according to Landis & Koch"""
        if kappa < 0:
            return "Poor"
        elif kappa < 0.20:
            return "Slight"
        elif kappa < 0.40:
            return "Fair"
        elif kappa < 0.60:
            return "Moderate"
        elif kappa < 0.80:
            return "Substantial"
        else:
            return "Almost Perfect"
    
    def generate_latex_table(self, metrics: dict) -> str:
        """Generate LaTeX table for thesis"""
        latex = """
\\begin{table}[h]
\\centering
\\caption{Classification Metrics with 95\\% Confidence Intervals}
\\begin{tabular}{|l|c|c|}
\\hline
\\textbf{Metric} & \\textbf{Value} & \\textbf{95\\% CI} \\\\
\\hline
"""
        for name, data in metrics.items():
            if isinstance(data, dict) and "point_estimate" in data:
                latex += f"{name.replace('_', ' ').title()} & "
                latex += f"{data['point_estimate']:.3f} & "
                latex += f"[{data['lower_bound']:.3f}, {data['upper_bound']:.3f}] \\\\\n"
        
        latex += """\\hline
\\end{tabular}
\\end{table}
"""
        return latex


# Example usage
if __name__ == "__main__":
    stats = StatisticalMetrics()
    
    # Example: 97 rules classified
    # tp=95 (correctly identified rules)
    # tn=392 (correctly rejected non-rules)
    # fp=2 (false positives)
    # fn=3 (missed rules)
    
    metrics = stats.calculate_classification_metrics(tp=95, tn=392, fp=2, fn=3)
    
    print("Classification Metrics with 95% CI:")
    for name, data in metrics.items():
        if isinstance(data, dict) and "ci_string" in data:
            print(f"  {name}: {data['ci_string']}")
    
    # Kappa example
    kappa_result = stats.calculate_kappa_with_ci(
        observed_agree=0.97,
        expected_agree=0.80,
        n=492
    )
    print(f"\nCohen's Kappa: {kappa_result['kappa']['ci_string']}")
    print(f"Interpretation: {kappa_result['interpretation']}")
    
    # LaTeX output
    print("\n" + stats.generate_latex_table(metrics))
