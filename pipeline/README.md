# Pipeline zur Datenaufbereitung & Ingestion

Dieses Verzeichnis enthält die automatisierte Pipeline zum Beschaffen, Aufbereiten und Indizieren deutscher Gerichtsurteile für den MCP-Server.

## Architektur

Die Pipeline läuft in einem eigenen Docker-Container (`data-preparer`) und wird von einem Scheduler (`pipeline/scheduler.py`) gesteuert.

- Standardbetrieb: täglich um **03:00 Uhr** (konfigurierbar über `RUN_AT`).
- One-shot: `RUN_ONCE=true` führt genau einen Lauf aus und beendet den Container.

Der Prozess führt folgende Schritte sequenziell aus:

1.  **Inhaltsverzeichnis aktualisieren**: Löscht das alte TOC und lädt `rii-toc.xml` neu herunter.
2.  **Downloads**: Lädt neue ZIP-Dateien herunter (existierende Dateien werden übersprungen).
3.  **Extraktion**: Entpackt die XML-Dateien.
4.  **Konvertierung**: Wandelt XML in Markdown und JSON-Metadaten um.
5.  **Ingestion**: Lädt die verarbeiteten Daten in den OpenSearch-Index.

## Skripte

Die Pipeline besteht aus folgenden Python-Skripten (Orchestrierung + Provider + Ingest):

*   **`scheduler.py`**: Startet die Pipeline via `schedule`. Nutzt `RUN_ONCE`/`RUN_AT`.
*   **`run_all.py`**: Führt BGH + States nacheinander aus.
*   **BGH**: `providers/bgh/bgh_scraper_links.py` → `bgh_scraper_download.py` → `bgh_extractor.py` → `bgh_parser.py` → `ingest/ingest_bgh.py`
*   **Bundesländer**: `providers/states/api_client.py` → `raw_fetcher.py` → Parser (`bw/by/bb`) → `ingest/ingest_states.py`

## Datenstruktur (Docker Volumes)

*   `pipeline/providers/bgh/data`: Persistenter Cache für BGH-TOC/Links/ZIP-Downloads (z.B. `downloads/`).
*   `mcp/data/bgh/raw`: Entpackte BGH-XMLs.
*   `mcp/data/bgh/markdown`: Konvertierte BGH-Markdown + JSON-Metadaten.
*   `mcp/data/<state>/raw`: Roh-HTML pro Bundesland (z.B. `bw/raw`).
*   `mcp/data/<state>/markdown`: Konvertiertes Markdown + JSON-Metadaten pro Bundesland.

## Konfiguration

Die Konfiguration erfolgt primär über Umgebungsvariablen im Root-`docker-compose.yml` und über eine `.env` Datei (siehe `.env.example`).

| Variable | Beschreibung | Standard |
| :--- | :--- | :--- |
| `OPENSEARCH_HOST` | Hostname des OpenSearch-Servers | `opensearch-node1` |
| `OPENSEARCH_PORT` | Port des OpenSearch-Servers | `9200` |
| `OPENSEARCH_USER` | Benutzername | `admin` |
| `OPENSEARCH_PASSWORD` | Passwort | `ComplexPassword123!` |
| `WEBSCRAPER_URL` | Basis-URL deines WebScraper-Services (Bundesländer) | - |
| `WEBSCRAPER_AUTH` | Auth Header/Token für den WebScraper | - |
| `RUN_ONCE` | Wenn `true`: genau ein Lauf, dann Exit | `false` |
| `RUN_AT` | Uhrzeit für tägliche Läufe (HH:MM) | `03:00` |
| `MAX_WORKERS` | Parallelität (Download/Parsing) | abhängig von Skript |

## Ausführung via Docker Compose

Empfohlener One-shot Lauf über das Root-Compose:

```bash
docker compose --profile pipelinerun up --build data-preparer
```

## Manuelle Ausführung

Zum Testen oder für einmalige Läufe können Sie den Scheduler umgehen und Skripte direkt im Container ausführen:

```bash
# In den Container wechseln
docker exec -it data-preparer bash

# Komplettlauf (BGH + Bundesländer)
python run_all.py

# Nur BGH
python main_bgh.py

# Nur Bundesländer
python main_states.py
```

## Bekannte Limitierungen

*   **Vollständige Verarbeitung**: Derzeit scannen die Konvertierungs- und Ingestion-Skripte bei jedem Lauf alle Dateien. Bei sehr großen Datenmengen sollte dies auf inkrementelle Verarbeitung (nur geänderte Dateien) umgestellt werden.
