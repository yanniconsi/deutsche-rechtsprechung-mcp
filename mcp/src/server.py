import json
import os
import logging
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from opensearchpy import OpenSearch

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger('mcp').setLevel(logging.DEBUG)
logging.getLogger('mcp.server').setLevel(logging.DEBUG)
logging.getLogger('mcp.server.fastmcp').setLevel(logging.DEBUG)

# Configuration
OPENSEARCH_HOST = os.environ.get('OPENSEARCH_HOST', 'localhost')
OPENSEARCH_PORT = int(os.environ.get('OPENSEARCH_PORT', 9200))
OPENSEARCH_USER = os.environ.get('OPENSEARCH_USER', 'admin')
OPENSEARCH_PASSWORD = os.environ.get('OPENSEARCH_PASSWORD', 'ComplexPassword123!')
# Defaults to the combined states index.
INDEX_NAME = os.environ.get('INDEX_NAME', 'court-decisions-states')
STATIC_SERVER_EXTERNAL_URL = os.environ.get('STATIC_SERVER_EXTERNAL_URL') or 'http://localhost:8003'


def _state_filter_enabled() -> bool:
    allow = os.environ.get("ALLOW_STATE_FILTER")
    if allow is not None:
        return allow.strip().lower() in {"1", "true", "yes", "y", "on"}

    return "states" in (INDEX_NAME or "").lower()

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
def search_decisions(query: str, states: list[str] = None, limit: int = 10) -> str:
    """Search for German court decisions by text or metadata.
    
    Args:
        query: The search query (e.g. 'Insolvenzverfahren', 'BGH IX ZB 72/08').
        states: Optional list of state abbreviations to restrict the search (e.g. ['bw', 'by']). If empty, searches all states.
        limit: Number of results to return (default 10).
    """
    print(f"[PRINT] search_decisions called with query='{query}', states='{states}'", flush=True)

    client = get_opensearch_client()
    
    base_query = {
        "multi_match": {
            "query": query,
            "fields": [
                "title^2", "leitsatz^2", "full_text", 
                "az", "doknr", "normen"
            ]
        }
    }
    
    query_body = {"bool": {"must": base_query}}
    
    if states and _state_filter_enabled():
        clean_states = [s.strip().lower() for s in states if isinstance(s, str)]
        if clean_states:
            query_body["bool"]["filter"] = {
                "terms": {"state": clean_states}
            }
            
    search_body = {
        "size": limit,
        "query": query_body,
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
            state = source.get('state', 'N/A') 
            source_file = source.get('source_file', 'N/A')
            
            if source_file != 'N/A':
                source_file = source_file.replace("\\", "/")
            
            decision_url = f"{STATIC_SERVER_EXTERNAL_URL}/decisions/{source_file}" if source_file != 'N/A' else None
            
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
                "state": state,
                "score": score,
                "snippet": snippet,
                "source": source_file,
                "url": decision_url, 
                "resource_uri": f"decision://{doknr}" 

            })
        
        if not results_list:
            return "No results found."
        
        result_json = json.dumps(results_list, ensure_ascii=False, indent=2)
        
        sources_with_urls = [
            f"- [{r['az']}]({r['url']})" if r.get('url') else f"- {r['az']}"
            for r in results_list if r.get('url')
        ]
        sources_section = "\n\n## Sources\n" + "\n".join(sources_with_urls) if sources_with_urls else ""
        
        logger.info(f"Returning {len(results_list)} results for query '{query}'")
        return result_json + sources_section
        
    except Exception as e:
        logger.error(f"Error in search_decisions: {e}", exc_info=True)
        return f"Error searching OpenSearch: {str(e)}"


@mcp.tool()
def get_decision_by_doknr(doknr: str) -> str:
    """Get the full text of a court decision by its document number (DokNr).
    
    Args:
        doknr: The document number (e.g. 'KARE600052872').
    """
    print(f"[PRINT] get_decision_by_doknr called with doknr='{doknr}'", flush=True)

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
        source_file = source.get('source_file', 'N/A')
        if source_file != 'N/A':
            source_file = source_file.replace("\\", "/")
            
        decision_url = f"{STATIC_SERVER_EXTERNAL_URL}/decisions/{source_file}" if source_file != 'N/A' else None
        
        result = json.dumps(source, ensure_ascii=False, indent=2)
        
        if decision_url:
            result += f"\n\n## Source\n- [View full text]({decision_url})"
        else:
            result += f"\n\n## Source\n- {source_file}"
        
        logger.info(f"Returning decision for doknr='{doknr}'")
        return result
    
    except Exception as e:
        logger.error(f"Error in get_decision_by_doknr: {e}", exc_info=True)
        return f"Error retrieving decision: {str(e)}"
    

@mcp.resource("decision://{doknr}")
def get_decision_resource(doknr: str) -> str:
    """Provide a decision document as a resource."""
    client = get_opensearch_client()
    
    search_body = {
        "query": {
            "term": {
                "doknr": doknr
            }
        }
    }
    
    response = client.search(index=INDEX_NAME, body=search_body)
    hits = response['hits']['hits']
    
    if not hits:
        return f"Decision not found: {doknr}"
    
    source = hits[0]['_source']
    
    markdown = f"""# {source.get('title', 'Untitled')}

**Court:** {source.get('gericht', 'N/A')}  
**Docket:** {source.get('az', 'N/A')}  
**Date:** {source.get('datum', 'N/A')}  
**DokNr:** {source.get('doknr', 'N/A')}  
**Norms:** {source.get('normen', 'N/A')}

## Headnote
{source.get('leitsatz', '')}

## Full text
{source.get('full_text', '')}
"""
    return markdown

@mcp.resource("decision://list")
def list_decisions_resource() -> list:
    """List available decision resources."""
    return []

if __name__ == "__main__":
    mcp.run(transport="streamable-http")