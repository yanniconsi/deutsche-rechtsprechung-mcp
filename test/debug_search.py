import json
import os

from opensearchpy import OpenSearch

# Configuration
OPENSEARCH_HOST = os.environ.get('OPENSEARCH_HOST', 'localhost')
OPENSEARCH_PORT = int(os.environ.get('OPENSEARCH_PORT', 9200))
OPENSEARCH_USER = os.environ.get('OPENSEARCH_USER', 'admin')
OPENSEARCH_PASSWORD = os.environ.get('OPENSEARCH_PASSWORD', 'ComplexPassword123!')
INDEX_NAME = 'court-decisions'

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

def fetch_sample_docs(limit=3):
    client = get_opensearch_client()
    print(f"Connecting to {OPENSEARCH_HOST}:{OPENSEARCH_PORT}...")
    
    try:
        # Check if index exists
        if not client.indices.exists(index=INDEX_NAME):
            print(f"Index '{INDEX_NAME}' does not exist.")
            return

        # Fetch documents
        response = client.search(
            index=INDEX_NAME,
            body={
                "size": limit,
                "query": {"match_all": {}}
            }
        )
        
        hits = response['hits']['hits']
        print(f"Found {response['hits']['total']['value']} documents. Showing {len(hits)} sample(s):\n")
        
        for i, hit in enumerate(hits, 1):
            print(f"--- Document {i} (ID: {hit['_id']}) ---")
            print(json.dumps(hit['_source'], ensure_ascii=False, indent=2))
            print("\n")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_sample_docs(limit=5)
