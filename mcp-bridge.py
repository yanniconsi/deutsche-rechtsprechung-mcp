import sys
import json
import requests
import re

MCP_URL = "http://localhost:8002/mcp"

def send_response(response):
    print(json.dumps(response), flush=True)

def main():
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            
            if request.get("method") == "initialize":
                send_response({
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "deutsche-rechtsprechung",
                            "version": "1.0.0"
                        }
                    }
                })
                
            elif request.get("method") == "tools/list":
                send_response({
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "search_decisions",
                                "description": "Search for German court decisions",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string"},
                                        "limit": {"type": "number", "default": 10}
                                    },
                                    "required": ["query"]
                                }
                            },
                            {
                                "name": "get_decision_by_doknr",
                                "description": "Get full text of a decision by document number",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "doknr": {"type": "string"}
                                    },
                                    "required": ["doknr"]
                                }
                            }
                        ]
                    }
                })
                
            elif request.get("method") == "tools/call":
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
                
                response = requests.post(MCP_URL, headers=headers, json=request, timeout=30)
                text = response.text.strip()
                
                # Parse SSE format - extract JSON after "data: "
                if "data: " in text:
                    # Find the JSON part after "data: "
                    match = re.search(r'data:\s*({.*})\s*$', text, re.DOTALL)
                    if match:
                        text = match.group(1)
                
                result = json.loads(text)
                send_response(result)
                
        except json.JSONDecodeError as e:
            send_response({
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"JSON parse error: {str(e)}, response was: {text[:500] if 'text' in locals() else 'N/A'}"
                }
            })
        except Exception as e:
            send_response({
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Error: {str(e)}"
                }
            })

if __name__ == "__main__":
    main()