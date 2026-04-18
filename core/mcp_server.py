"""
MCP Server — Policy Rule Verification
Exposes pipeline tools via JSON-RPC over STDIO for MCP-compatible clients.

Tools:
    verify_rule       — Check if a text is a policy rule via local Ollama
    check_status      — Check Ollama availability and list models

Usage:
    python -m core.mcp_server --mcp
    python -m core.mcp_server          # interactive mode
"""

import json
import os
import re
import sys

import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
JSONRPC_VERSION = "2.0"

TOOLS = [
    {
        "name": "verify_rule",
        "description": (
            "Classify whether a text is a policy rule (obligation, permission, or prohibition) "
            "using a local Ollama LLM."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to classify"},
                "model": {
                    "type": "string",
                    "description": f"Ollama model to use (default: {DEFAULT_MODEL})",
                    "default": DEFAULT_MODEL,
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "check_status",
        "description": "Check if Ollama is reachable and list available models.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _query_ollama(prompt: str, model: str) -> str:
    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False,
              "options": {"temperature": 0.0, "seed": 42, "num_predict": 512}},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


def verify_rule(text: str, model: str = DEFAULT_MODEL) -> dict:
    prompt = (
        "You are a legal policy analyst. Classify whether the following sentence is a "
        "POLICY RULE (a binding obligation, permission, or prohibition) or NOT A RULE.\n\n"
        f'Sentence: "{text}"\n\n'
        'Respond ONLY with a JSON object:\n'
        '{"is_rule": true/false, "rule_type": "obligation"/"permission"/"prohibition"/null, '
        '"confidence": 0.0-1.0, "reasoning": "one sentence"}'
    )
    try:
        raw = _query_ollama(prompt, model)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"is_rule": False, "rule_type": None, "confidence": 0.0,
                "reasoning": "Failed to parse LLM response", "raw": raw[:200]}
    except Exception as exc:
        return {"is_rule": False, "rule_type": None, "confidence": 0.0, "error": str(exc)}


def check_status() -> dict:
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        return {"ollama_running": True, "available_models": models, "host": OLLAMA_HOST}
    except Exception:
        return {"ollama_running": False, "available_models": [], "host": OLLAMA_HOST}


# ---------------------------------------------------------------------------
# MCP dispatch
# ---------------------------------------------------------------------------

def _handle(tool_name: str, arguments: dict) -> dict:
    if tool_name == "verify_rule":
        text = arguments.get("text", "")
        model = arguments.get("model", DEFAULT_MODEL)
        return {"success": True, "result": verify_rule(text, model)}

    if tool_name == "check_status":
        return {"success": True, **check_status()}

    return {"success": False, "error": f"Unknown tool: {tool_name}"}


def run_mcp_server() -> None:
    print(json.dumps({
        "jsonrpc": JSONRPC_VERSION,
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "policy-rule-verifier", "version": "2.0.0"},
            "capabilities": {"tools": {}},
        },
    }), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            rid = request.get("id")

            if method == "tools/list":
                response = {"jsonrpc": JSONRPC_VERSION, "id": rid,
                            "result": {"tools": TOOLS}}
            elif method == "tools/call":
                result = _handle(params.get("name", ""), params.get("arguments", {}))
                response = {
                    "jsonrpc": JSONRPC_VERSION, "id": rid,
                    "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
                }
            else:
                response = {
                    "jsonrpc": JSONRPC_VERSION, "id": rid,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            continue
        except Exception as exc:
            print(json.dumps({"jsonrpc": JSONRPC_VERSION,
                               "error": {"code": -32603, "message": str(exc)}}), flush=True)


def interactive_mode() -> None:
    status = check_status()
    if not status["ollama_running"]:
        print(f"❌ Ollama not reachable at {OLLAMA_HOST}. Start with: ollama serve")
        return
    print(f"✅ Ollama running at {OLLAMA_HOST}. Models: {status['available_models']}")

    while True:
        text = input("\nEnter rule text (or 'q' to quit): ").strip()
        if text.lower() == "q":
            break
        result = verify_rule(text)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if "--mcp" in sys.argv:
        run_mcp_server()
    else:
        interactive_mode()
