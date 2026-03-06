import glob
import json
import logging
import os
import time

from opensearchpy import OpenSearch, helpers

# Configuration
OPENSEARCH_HOST = os.environ.get('OPENSEARCH_HOST', 'localhost')
OPENSEARCH_PORT = int(os.environ.get('OPENSEARCH_PORT', 9200))
OPENSEARCH_USER = os.environ.get('OPENSEARCH_USER', 'admin')
OPENSEARCH_PASSWORD = os.environ.get('OPENSEARCH_PASSWORD', 'ComplexPassword123!')
MARKDOWN_DIR = os.environ.get('MARKDOWN_DIR_BW', '../mcp/markdown_bw')
INDEX_NAME = 'court-decisions-bw'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_opensearch_client():
    client = OpenSearch(
        hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT, 'scheme': 'https'}],
        http_compress=True,
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False
    )
    return client

def wait_for_opensearch(client):
    logger.info(f"Waiting for OpenSearch at {OPENSEARCH_HOST}:{OPENSEARCH_PORT}...")
    while True:
        try:
            if client.ping():
                logger.info("OpenSearch is up!")
                break
        except Exception as e:
            logger.info(f"Waiting... ({e})")
        time.sleep(5)

def create_index(client):
    index_body = {
        'settings': {
            'index': {
                'number_of_shards': 1,
                'number_of_replicas': 0
            }
        },
        'mappings': {
            'properties': {
                'title': {'type': 'text', 'analyzer': 'german'},
                'full_text': {'type': 'text', 'analyzer': 'german'},
                'doknr': {'type': 'keyword'},
                'ecli': {'type': 'keyword'},
                'az': {'type': 'keyword'},
                'datum': {'type': 'date', 'format': 'basic_date'}, # 20100114
                'gericht': {'type': 'keyword'},
                'spruchkoerper': {'type': 'keyword'},
                'normen': {'type': 'text', 'analyzer': 'german'},
                'leitsatz': {'type': 'text', 'analyzer': 'german'},
                'sonstosatz': {'type': 'text', 'analyzer': 'german'},
                'tenor': {'type': 'text', 'analyzer': 'german'},
                'tatbestand': {'type': 'text', 'analyzer': 'german'},
                'entscheidungsgruende': {'type': 'text', 'analyzer': 'german'},
                'gruende': {'type': 'text', 'analyzer': 'german'},
                'abwmeinung': {'type': 'text', 'analyzer': 'german'},
                'sonstlt': {'type': 'text', 'analyzer': 'german'},
                'source_file': {'type': 'keyword'}
            }
        }
    }
    
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(index=INDEX_NAME, body=index_body)
        logger.info(f"Index '{INDEX_NAME}' created.")
    else:
        logger.info(f"Index '{INDEX_NAME}' already exists.")

def ingest_files(client):
    logger.info(f"Scanning files in {MARKDOWN_DIR}...")
    files = glob.iglob(os.path.join(MARKDOWN_DIR, '**', '*.md'), recursive=True)
    
    def generate_actions():
        count = 0
        for md_path in files:
            try:
                # Construct JSON path from MD path
                json_path = os.path.splitext(md_path)[0] + ".json"
                
                if not os.path.exists(json_path):
                    continue

                # Load Metadata from JSON
                with open(json_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Load Full Text from Markdown
                with open(md_path, 'r', encoding='utf-8') as f:
                    full_text = f.read()


                # NEW
                relative_path = os.path.relpath(md_path, MARKDOWN_DIR)
                
                doc = {
                    'title': metadata.get('title'),
                    'full_text': full_text,
                    'doknr': metadata.get('doknr'),
                    'ecli': metadata.get('ecli'),
                    'az': metadata.get('aktenzeichen'),
                    'datum': metadata.get('datum'),
                    'gericht': f"{metadata.get('gertyp', '')} {metadata.get('gerort', '')}".strip(),
                    'spruchkoerper': metadata.get('spruchkoerper'),
                    'normen': metadata.get('norm'),
                    'leitsatz': metadata.get('leitsatz'),
                    'sonstosatz': metadata.get('sonstosatz'),
                    'tenor': metadata.get('tenor'),
                    'tatbestand': metadata.get('tatbestand'),
                    'entscheidungsgruende': metadata.get('entscheidungsgruende'),
                    'gruende': metadata.get('gruende'),
                    'abwmeinung': metadata.get('abwmeinung'),
                    'sonstlt': metadata.get('sonstlt'),
                    'source_file': relative_path  # NEU: Relativer Pfad zur Quelldatei
                }
                
                if not doc.get('datum'):
                    doc.pop('datum', None)

                action = {
                    "_index": INDEX_NAME,
                    "_source": doc
                }
                
                if not doc.get("doknr"):
                    logger.warning(f"Skipping {md_path}: 'doknr' metadata is missing.")
                    continue

                action = {"_index": INDEX_NAME, "_id": doc["doknr"], "_source": doc}

                yield action
                count += 1
                if count % 100 == 0:
                    logger.info(f"Prepared {count} documents...")
                    
            except Exception as e:
                logger.error(f"Error processing {md_path}: {e}")

    logger.info("Starting bulk ingestion...")
    success, failed = helpers.bulk(client, generate_actions(), stats_only=True)
    logger.info(f"Ingestion complete. Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    logger.info('Starting ingestion process!')
    client = get_opensearch_client()
    wait_for_opensearch(client)
    create_index(client)
    # Always run ingest to allow updates
    ingest_files(client)
