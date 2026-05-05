import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env (if present).
load_dotenv()

# Paths
COMMON_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = COMMON_DIR.parent
PROJECT_ROOT = PIPELINE_DIR.parent

# Final data directory mounted/served by MCP.
MCP_DATA_DIR = PROJECT_ROOT / "mcp" / "data"

# BGH provider cache (TOC/XML/ZIP downloads).
BGH_DATA_DIR = PIPELINE_DIR / "providers" / "bgh" / "data"

# States provider intermediate exports (e.g. from an external scraper/DB service).
STATES_DATA_DIR = PIPELINE_DIR / "providers" / "states" / "data"

def get_state_data_dir(state_code: str, data_type: str = "raw") -> Path:
    """Return the data directory for a state (e.g. bw/by/bb)."""
    path = MCP_DATA_DIR / state_code / data_type
    path.mkdir(parents=True, exist_ok=True)
    return path

# OpenSearch
OPENSEARCH_HOST = os.environ.get("OPENSEARCH_HOST", "opensearch-node1")
OPENSEARCH_PORT = int(os.environ.get("OPENSEARCH_PORT", 9200))
OPENSEARCH_USER = os.environ.get("OPENSEARCH_USER", "admin")
OPENSEARCH_PASSWORD = os.environ.get("OPENSEARCH_PASSWORD", "ComplexPassword123!")

# Optional: external service used to export HTML for state decisions.
WEBSCRAPER_URL = os.environ.get("WEBSCRAPER_URL")
WEBSCRAPER_AUTH = os.environ.get("WEBSCRAPER_AUTH")