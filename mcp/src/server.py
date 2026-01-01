import json
import os

from mcp.server.fastmcp import FastMCP
from opensearchpy import OpenSearch

# Configuration
OPENSEARCH_HOST = os.environ.get('OPENSEARCH_HOST', 'localhost')
OPENSEARCH_PORT = int(os.environ.get('OPENSEARCH_PORT', 9200))
OPENSEARCH_USER = os.environ.get('OPENSEARCH_USER', 'admin')
OPENSEARCH_PASSWORD = os.environ.get('OPENSEARCH_PASSWORD', 'ComplexPassword123!')
INDEX_NAME = 'court-decisions'

# Initialize FastMCP
mcp = FastMCP("court-decisions-mcp", stateless_http=True, host='0.0.0.0', port=8002, debug=True)

def get_opensearch_client():
    return OpenSearch(
        hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT, 'scheme': 'https'}],
        http_compress=True,
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False
    )

@mcp.tool()
def search_decisions(query: str, limit: int = 10) -> str:
    """Search for German court decisions by text or metadata.
    
    Args:
        query: The search query (e.g. 'Insolvenzverfahren', 'BGH IX ZB 72/08').
        limit: Number of results to return (default 10).
    """
    client = get_opensearch_client()
    
    # Simple multi-match query
    search_body = {
        "size": limit,
        "query": {
            "multi_match": {
                "query": query,
                "fields": [
                    "title^2", "leitsatz^2", "full_text", 
                    "az", "doknr", "normen"
                ]
            }
        },
        "highlight": {
            "fields": {
                "full_text": {}
            }
        }
    }
    
    try:
        response = client.search(index=INDEX_NAME, body=search_body)
        hits = response['hits']['hits']
        
        results_list = []
        for hit in hits:
            source = hit['_source']
            score = hit['_score']
            title = source.get('title', 'No Title')
            az = source.get('az', 'N/A')
            doknr = source.get('doknr', 'N/A')
            datum = source.get('datum', 'N/A')
            gericht = source.get('gericht', 'N/A')
            normen = source.get('normen', 'N/A')
            
            # Get highlight if available
            snippet = ""
            if 'highlight' in hit and 'full_text' in hit['highlight']:
                snippet = "... " + " ... ".join(hit['highlight']['full_text']) + " ..."
            else:
                snippet = source.get('full_text', '')[:200] + "..."
            
            results_list.append({
                "title": title,
                "az": az,
                "gericht": gericht,
                "normen": normen,
                "doknr": doknr,
                "date": datum,
                "score": score,
                "snippet": snippet
            })
        
        if not results_list:
            return "No results found."

        return json.dumps(results_list, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"Error searching OpenSearch: {str(e)}"

@mcp.tool()
def get_decision_by_doknr(doknr: str) -> str:
    """Get the full text of a court decision by its document number (DokNr).
    
    Args:
        doknr: The document number (e.g. 'KARE600052872').
    """
    client = get_opensearch_client()
    
    search_body = {
        "query": {
            "term": {
                "doknr": doknr
            }
        }
    }
    
    try:
        response = client.search(index=INDEX_NAME, body=search_body)
        hits = response['hits']['hits']
        
        if not hits:
            return f"No decision found with DokNr: {doknr}"
        
        # Return the first match (should be unique)
        source = hits[0]['_source']
        return json.dumps(source, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"Error retrieving decision: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")