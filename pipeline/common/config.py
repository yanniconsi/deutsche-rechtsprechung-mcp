import os
from pathlib import Path
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus der .env Datei
load_dotenv()

# --- 1. Basis-Verzeichnisse ---
# COMMON_DIR = pipeline/common
COMMON_DIR = Path(__file__).resolve().parent
# PIPELINE_DIR = pipeline
PIPELINE_DIR = COMMON_DIR.parent
# PROJECT_ROOT = Hauptordner (deutsche-rechtsprechung-mcp)
PROJECT_ROOT = PIPELINE_DIR.parent

# --- 2. Daten-Verzeichnisse ---
# MCP Verzeichnis für die final aufbereiteten Daten
MCP_DATA_DIR = PROJECT_ROOT / "mcp" / "data"

# BGH Spezifische Daten (ZIP, XML, Downloads)
BGH_DATA_DIR = PIPELINE_DIR / "providers" / "bgh" / "data"

# Hilfsfunktion, um Pfade für ein bestimmtes Bundesland zu bekommen
def get_state_data_dir(state_code: str, data_type: str = "raw") -> Path:
    """
    Gibt den Pfad zum Datenordner eines Bundeslands zurück.
    Beispiel: state_code='bw', data_type='markdown' -> mcp/data/bw/markdown
    """
    path = MCP_DATA_DIR / state_code / data_type
    path.mkdir(parents=True, exist_ok=True)
    return path

# --- 3. OpenSearch Konfiguration ---
OPENSEARCH_HOST = os.environ.get("OPENSEARCH_HOST", "opensearch-node1")
OPENSEARCH_PORT = int(os.environ.get("OPENSEARCH_PORT", 9200))
OPENSEARCH_USER = os.environ.get("OPENSEARCH_USER", "admin")
OPENSEARCH_PASSWORD = os.environ.get("OPENSEARCH_PASSWORD", "ComplexPassword123!")

# --- 4. Scraper API Konfiguration (für Bundesländer) ---
WEBSCRAPER_URL = os.environ.get("WEBSCRAPER_URL")
WEBSCRAPER_AUTH = os.environ.get("WEBSCRAPER_AUTH")