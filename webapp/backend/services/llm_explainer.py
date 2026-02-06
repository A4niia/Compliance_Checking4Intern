"""
LLM Explanation Service
Generates natural language explanations of SHACL validation results using Mistral
"""

import os
import requests
import json
from typing import Dict, Optional


def explain_validation_result(
    rule_text: str,
    student_data: Dict,
    validation_result: Dict,
    fol_formula: Optional[str] = None
) -> str:
    """
    Generate natural language explanation of validation result using LLM.
    
    Args:
        rule_text: Original policy rule text
        student_data: Student information dict
        validation_result: pySHACL validation result
        fol_formula: Optional FOL representation
    
    Returns:
        Natural language explanation string
    """
    ollama_url = os.getenv("OLLAMA_HOST", "http://10.99.200.2:11434")
    
    # Build context
    conforms = validation_result.get('conforms', True)
    violations = validation_result.get('violations', [])
    
    student_info = f"""
Student ID: {student_data.get('id', 'Unknown')}
Name: {student_data.get('name', 'Unknown')}
Program: {student_data.get('program', 'Unknown')}
Fees Paid: {'Yes' if student_data.get('fees_paid') else 'No'}
Full-Time Status: {'Yes' if student_data.get('is_full_time') else 'No'}
"""
    
    # Construct prompt
    if conforms:
        prompt = f"""You are an academic policy compliance assistant. Explain this validation result in simple, friendly language.

POLICY RULE:
{rule_text}

STUDENT DATA:
{student_info}

VALIDATION RESULT: ✅ CONFORMS (Student meets the requirement)

Task: Write a 1-2 sentence explanation in plain English explaining WHY this student complies with the policy rule. Be friendly and clear.

Example format: "Alice Chen complies with this rule because she has paid her fees before the mid-semester deadline."

Your explanation:"""
    else:
        violations_text = "\n".join(violations[:3]) if violations else "Policy requirement not met"
        prompt = f"""You are an academic policy compliance assistant. Explain this validation failure in simple, actionable language.

POLICY RULE:
{rule_text}

STUDENT DATA:
{student_info}

VALIDATION RESULT: ❌ VIOLATION DETECTED

Technical Details:
{violations_text}

Task: Write 2-3 sentences explaining:
1. What the rule requires
2. Why the student doesn't comply
3. What action is needed (if applicable)

Be clear and helpful. Avoid technical jargon.

Your explanation:"""

    # Call LLM
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Slightly creative but consistent
                    "num_predict": 150,   # Short explanation
                    "stop": ["\n\n"]
                }
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            explanation = result.get("response", "").strip()
            return explanation if explanation else "Validation completed successfully."
        else:
            return "Unable to generate explanation at this time."
            
    except Exception as e:
        # Fallback to simple explanation
        if conforms:
            return f"✅ {student_data.get('name', 'Student')} complies with this policy requirement."
        else:
            return f"❌ {student_data.get('name', 'Student')} does not meet this policy requirement. Please review the violations above."


if __name__ == "__main__":
    # Test
    test_rule = "Students must pay all fees before the mid-semester break."
    test_student = {
        'id': 'ST001',
        'name': 'Alice Chen',
        'program': 'Master',
        'fees_paid': True,
        'is_full_time': True
    }
    test_result = {'conforms': True, 'violations': []}
    
    explanation = explain_validation_result(test_rule, test_student, test_result)
    print(f"Explanation: {explanation}")
