import json
import os
import logging
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from opensearchpy import OpenSearch

# Logging configuration (improved debug visibility for MCP)
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

# Defaults to the combined states index
INDEX_NAME = os.environ.get('INDEX_NAME', 'court-decisions-states')
STATIC_SERVER_EXTERNAL_URL = os.environ.get('STATIC_SERVER_EXTERNAL_URL') or 'http://localhost:8003'

def _state_filter_enabled() -> bool:
    """Check if state filtering is supported by the index configuration."""
    allow = os.environ.get("ALLOW_STATE_FILTER")
    if allow is not None:
        return allow.strip().lower() in {"1", "true", "yes", "y", "on"}
    return "states" in (INDEX_NAME or "").lower()

# Initialize FastMCP
mcp = FastMCP("court-decisions-mcp", stateless_http=True, host='0.0.0.0', port=8002, debug=True)

def get_opensearch_client():
    """Create and return an OpenSearch client instance."""
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
def search_decisions(
    query: str = None, 
    states: list[str] = None,
    aktenzeichen: str = None, 
    gericht: str = None, 
    normen: str = None, 
    datum_von: str = None, 
    datum_bis: str = None, 
    limit: int = 10
) -> str:
    """
    Search for German court decisions using combined text and metadata filters.
    
    Args:
        query: General text search query (e.g., 'Insolvenzverfahren').
        states: Optional list of state abbreviations (e.g., ['bw', 'by']).
        aktenzeichen: Search for a specific docket number (Aktenzeichen).
        gericht: Filter by court name (e.g., 'BGH', 'OLG Stuttgart').
        normen: Filter by legal norms/paragraphs (e.g., 'BGB § 280').
        datum_von: Start date filter in YYYY-MM-DD format.
        datum_bis: End date filter in YYYY-MM-DD format.
        limit: Number of results to return (default 10).
    """
    print(f"[PRINT] search_decisions: query='{query}', states='{states}', az='{aktenzeichen}'", flush=True)

    client = get_opensearch_client()
    
    must_clauses = []
    filter_clauses = []

    # 1. Text Search (Affects scoring)
    if query:
        must_clauses.append({
            "multi_match": {
                "query": query,
                "fields": ["title^2", "leitsatz^2", "full_text", "az", "normen"],
                "type": "best_fields"
            }
        })
    else:
        must_clauses.append({"match_all": {}})

    # 2. Filters (Strict criteria, no impact on score)
    
    # State filter logic
    if states and _state_filter_enabled():
        clean_states = [s.strip().lower() for s in states if isinstance(s, str)]
        if clean_states:
            filter_clauses.append({"terms": {"state": clean_states}})

    # Metadata filters
    if aktenzeichen:
        filter_clauses.append({"term": {"az": aktenzeichen}})
        
    if gericht:
        filter_clauses.append({"term": {"gericht": gericht}})
        
    if normen:
        filter_clauses.append({"match_phrase": {"normen": normen}})
        
    # Date range conversion (mapping expects basic_date format yyyyMMdd)
    if datum_von or datum_bis:
        date_range = {}
        if datum_von:
            date_range["gte"] = datum_von.replace("-", "") 
        if datum_bis:
            date_range["lte"] = datum_bis.replace("-", "")
        filter_clauses.append({"range": {"datum": date_range}})

    # Final query construction
    search_body = {
        "size": limit,
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
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
            
            # Clean file paths for URL generation
            source_file = source.get('source_file', 'N/A')
            if source_file != 'N/A':
                source_file = source_file.replace("\\", "/")
            
            decision_url = f"{STATIC_SERVER_EXTERNAL_URL}/decisions/{source_file}" if source_file != 'N/A' else None
            
            # Highlight snippet generation
            snippet = ""
            if 'highlight' in hit and 'full_text' in hit['highlight']:
                snippet = "... " + " ... ".join(hit['highlight']['full_text']) + " ..."
            else:
                snippet = source.get('full_text', '')[:200] + "..."
            
            results_list.append({
                "title": source.get('title', 'Kein Titel'),
                "az": source.get('az', 'N/A'),
                "gericht": source.get('gericht', 'N/A'),
                "normen": source.get('normen', 'N/A'),
                "doknr": source.get('doknr', 'N/A'),
                "date": source.get('datum', 'N/A'),
                "state": source.get('state', 'N/A'),
                "score": score,
                "snippet": snippet,
                "url": decision_url,
                "resource_uri": f"decision://{source.get('doknr')}"
            })
        
        if not results_list:
            return "No matching results found."
        
        result_json = json.dumps(results_list, ensure_ascii=False, indent=2)
        
        # Build markdown sources section
        sources_with_urls = [
            f"- [{r['az']}]({r['url']})" if r.get('url') else f"- {r['az']}"
            for r in results_list
        ]
        sources_section = "\n\n## Quellen\n" + "\n".join(sources_with_urls)
        
        logger.info(f"Search completed: {len(results_list)} results returned.")
        return result_json + sources_section
        
    except Exception as e:
        logger.error(f"Error in search_decisions: {e}", exc_info=True)
        return f"Error searching OpenSearch: {str(e)}"

@mcp.tool()
def get_decision_by_doknr(doknr: str) -> str:
    """Retrieve full text of a decision using its unique document number (DokNr)."""
    client = get_opensearch_client()
    search_body = {"query": {"term": {"doknr": doknr}}}
    
    try:
        response = client.search(index=INDEX_NAME, body=search_body)
        hits = response['hits']['hits']
        if not hits:
            return f"No decision found with DokNr {doknr}."
        
        source = hits[0]['_source']
        source_file = source.get('source_file', 'N/A').replace("\\", "/")
        decision_url = f"{STATIC_SERVER_EXTERNAL_URL}/decisions/{source_file}" if source_file != 'N/A' else None
        
        result = json.dumps(source, ensure_ascii=False, indent=2)
        if decision_url:
            result += f"\n\n## Quelle\n- [Volltext öffnen]({decision_url})"
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        return f"Error: {str(e)}"

@mcp.resource("decision://{doknr}")
def get_decision_resource(doknr: str) -> str:
    """Provide a decision document as an MCP resource."""
    client = get_opensearch_client()
    search_body = {"query": {"term": {"doknr": doknr}}}
    response = client.search(index=INDEX_NAME, body=search_body)
    hits = response['hits']['hits']
    
    if not hits:
        return f"Not found: {doknr}"
    
    s = hits[0]['_source']
    return f"""# {s.get('title', 'Entscheidung')}
**Gericht:** {s.get('gericht', 'N/A')} | **AZ:** {s.get('az', 'N/A')} | **Datum:** {s.get('datum', 'N/A')}
**Bundesland:** {s.get('state', 'N/A')} | **Normen:** {s.get('normen', 'N/A')}

## Leitsatz
{s.get('leitsatz', 'Kein Leitsatz verfügbar.')}

## Volltext
{s.get('full_text', 'Kein Volltext verfügbar.')}
"""

if __name__ == "__main__":
    mcp.run(transport="streamable-http")