# MCP Server for Rule Verification
# Provides tools for policy rule extraction and verification via MCP protocol

"""
This MCP server provides the following tools:
1. verify_rule - Check if a text is a policy rule using Ollama
2. formalize_rule - Generate FOL representation for a rule
3. batch_verify - Process multiple rules
4. create_gold_standard - Create annotation template
5. calculate_metrics - Compute evaluation metrics

To use with MCP-compatible clients, run:
    python scripts/mcp_rule_server.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from verify_rules import (
    verify_rule,
    formalize_rule,
    check_ollama_running,
    get_available_models,
    create_gold_standard_template,
    calculate_metrics,
    MODEL_NAME,
    RESEARCH_DIR
)

# MCP Protocol Constants
JSONRPC_VERSION = "2.0"

# Tool definitions
TOOLS = [
    {
        "name": "verify_rule",
        "description": "Check if a text is a policy rule using local Ollama LLM. Returns classification, confidence, and extracted components.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to analyze for policy rule content"
                },
                "model": {
                    "type": "string",
                    "description": "Ollama model to use (default: llama3.2)",
                    "default": MODEL_NAME
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "formalize_rule",
        "description": "Generate First-Order Logic (FOL) representation for a verified policy rule.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The policy rule text"
                },
                "subject": {
                    "type": "string",
                    "description": "Who the rule applies to"
                },
                "condition": {
                    "type": "string",
                    "description": "The trigger condition"
                },
                "action": {
                    "type": "string",
                    "description": "What must/may/cannot happen"
                },
                "rule_type": {
                    "type": "string",
                    "enum": ["obligation", "prohibition", "permission", "recommendation"],
                    "description": "Type of rule"
                }
            },
            "required": ["text", "rule_type"]
        }
    },
    {
        "name": "batch_verify_rules",
        "description": "Verify multiple rules from extracted_rules.json file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of rules to process",
                    "default": 10
                },
                "start_index": {
                    "type": "integer",
                    "description": "Starting index in the rules list",
                    "default": 0
                }
            }
        }
    },
    {
        "name": "create_gold_standard",
        "description": "Create a gold standard annotation template for evaluation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sample_size": {
                    "type": "integer",
                    "description": "Number of rules to sample",
                    "default": 100
                }
            }
        }
    },
    {
        "name": "get_evaluation_metrics",
        "description": "Calculate precision, recall, F1, and Cohen's Kappa from annotated gold standard.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "gold_standard_file": {
                    "type": "string",
                    "description": "Path to gold standard JSON file"
                }
            },
            "required": ["gold_standard_file"]
        }
    },
    {
        "name": "check_system_status",
        "description": "Check if Ollama is running and list available models.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    """Handle a tool call and return the result."""
    
    if tool_name == "verify_rule":
        text = arguments.get("text", "")
        model = arguments.get("model", MODEL_NAME)
        result = verify_rule(text, model)
        return {"success": True, "result": result}
    
    elif tool_name == "formalize_rule":
        verification = {
            "is_rule": True,
            "original_text": arguments.get("text", ""),
            "subject": arguments.get("subject", ""),
            "condition": arguments.get("condition", ""),
            "action": arguments.get("action", ""),
            "rule_type": arguments.get("rule_type", "")
        }
        result = formalize_rule(verification)
        return {"success": True, "result": result}
    
    elif tool_name == "batch_verify_rules":
        limit = arguments.get("limit", 10)
        start_index = arguments.get("start_index", 0)
        
        rules_file = RESEARCH_DIR / "extracted_rules.json"
        if not rules_file.exists():
            return {"success": False, "error": f"Rules file not found: {rules_file}"}
        
        with open(rules_file, 'r', encoding='utf-8') as f:
            all_rules = json.load(f)
        
        rules_to_process = all_rules[start_index:start_index + limit]
        results = []
        
        for rule in rules_to_process:
            verification = verify_rule(rule["original_text"])
            results.append({
                "rule_id": rule["rule_id"],
                "is_rule": verification.get("is_rule"),
                "confidence": verification.get("confidence"),
                "rule_type": verification.get("rule_type"),
                "reasoning": verification.get("reasoning")
            })
        
        return {"success": True, "processed": len(results), "results": results}
    
    elif tool_name == "create_gold_standard":
        sample_size = arguments.get("sample_size", 100)
        result = create_gold_standard_template(sample_size)
        return {
            "success": True, 
            "message": f"Created gold standard template with {sample_size} samples",
            "file": str(RESEARCH_DIR / "gold_standard_template.json")
        }
    
    elif tool_name == "get_evaluation_metrics":
        file_path = arguments.get("gold_standard_file")
        if not file_path:
            file_path = str(RESEARCH_DIR / "gold_standard_template.json")
        
        result = calculate_metrics(file_path)
        return {"success": True, "metrics": result}
    
    elif tool_name == "check_system_status":
        ollama_running = check_ollama_running()
        models = get_available_models() if ollama_running else []
        return {
            "success": True,
            "ollama_running": ollama_running,
            "available_models": models,
            "default_model": MODEL_NAME
        }
    
    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}


# Simple STDIO-based MCP server
def run_mcp_server():
    """Run the MCP server (simplified STDIO version)."""
    print(json.dumps({
        "jsonrpc": JSONRPC_VERSION,
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "thesis-rule-verifier",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {}
            }
        }
    }), flush=True)
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "tools/list":
                response = {
                    "jsonrpc": JSONRPC_VERSION,
                    "id": request_id,
                    "result": {"tools": TOOLS}
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = handle_tool_call(tool_name, arguments)
                response = {
                    "jsonrpc": JSONRPC_VERSION,
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                    }
                }
            else:
                response = {
                    "jsonrpc": JSONRPC_VERSION,
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
            
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(json.dumps({
                "jsonrpc": JSONRPC_VERSION,
                "error": {"code": -32603, "message": str(e)}
            }), flush=True)


# For direct usage without MCP
def interactive_mode():
    """Interactive CLI mode for testing."""
    print("\n" + "="*60)
    print("RULE VERIFICATION SYSTEM - Interactive Mode")
    print("="*60)
    
    # Check system status
    status = handle_tool_call("check_system_status", {})
    if not status["ollama_running"]:
        print("❌ Ollama is not running. Please start with: ollama serve")
        return
    
    print(f"✅ Ollama running. Available models: {status['available_models']}")
    
    while True:
        print("\nOptions:")
        print("1. Verify a rule")
        print("2. Batch verify (10 rules)")
        print("3. Create gold standard (100)")
        print("4. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            text = input("Enter rule text: ")
            result = handle_tool_call("verify_rule", {"text": text})
            print(json.dumps(result, indent=2))
        
        elif choice == "2":
            result = handle_tool_call("batch_verify_rules", {"limit": 10})
            print(json.dumps(result, indent=2))
        
        elif choice == "3":
            result = handle_tool_call("create_gold_standard", {"sample_size": 100})
            print(json.dumps(result, indent=2))
        
        elif choice == "4":
            break


if __name__ == "__main__":
    if "--mcp" in sys.argv:
        run_mcp_server()
    else:
        interactive_mode()
