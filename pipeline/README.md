# Pipeline zur Datenaufbereitung & Ingestion

Dieses Verzeichnis enthält die automatisierte Pipeline zum Beschaffen, Aufbereiten und Indizieren deutscher Gerichtsurteile für den MCP-Server.

## Architektur

Die Pipeline läuft in einem eigenen Docker-Container (`data-preparer`) und wird von einem Scheduler gesteuert. Der Prozess läuft **einmal täglich um 03:00 Uhr** und führt folgende Schritte sequenziell aus:

1.  **Inhaltsverzeichnis aktualisieren**: Löscht das alte TOC und lädt `rii-toc.xml` neu herunter.
2.  **Downloads**: Lädt neue ZIP-Dateien herunter (existierende Dateien werden übersprungen).
3.  **Extraktion**: Entpackt die XML-Dateien.
4.  **Konvertierung**: Wandelt XML in Markdown und JSON-Metadaten um.
5.  **Ingestion**: Lädt die verarbeiteten Daten in den OpenSearch-Index.

## Skripte

Die Pipeline besteht aus folgenden Python-Skripten:

*   **`scheduler.py`**: Der Hauptprozess. Er nutzt die `schedule`-Bibliothek, um die Pipeline täglich zu starten. Er führt die anderen Skripte als Subprozesse aus, um eine saubere Speicherverwaltung zu gewährleisten.
*   **`extract_links.py`**: Lädt `rii-toc.xml` herunter und extrahiert Download-Links nach `data/links.txt`.
*   **`download_files.py`**: Lädt Dateien aus `data/links.txt` parallel herunter. Beachtet Rate-Limits und Retries.
*   **`extract_zips.py`**: Entpackt ZIP-Archive aus `data/downloads` nach `data/extracted`.
*   **`convert_all_to_md.py`**: Konvertiert XML-Dateien zu Markdown (für LLMs) und JSON (für Metadaten). Speichert das Ergebnis im `markdown`-Volume, das mit dem MCP-Server geteilt wird.
*   **`ingest.py`**: Indiziert die Markdown/JSON-Dateien in der OpenSearch-Instanz.

## Datenstruktur (Docker Volumes)

*   `/app/prepare_data/data`: Persistenter Cache für Downloads und extrahierte XMLs. Verhindert unnötiges erneutes Herunterladen.
*   `/app/mcp/markdown`: Geteiltes Volume mit dem `mcp-server`. Hier landen die fertigen Markdown-Dateien.

## Konfiguration

Die Konfiguration erfolgt primär über Umgebungsvariablen im `docker-compose.yml`:

| Variable | Beschreibung | Standard |
| :--- | :--- | :--- |
| `OPENSEARCH_HOST` | Hostname des OpenSearch-Servers | `opensearch-node1` |
| `OPENSEARCH_PORT` | Port des OpenSearch-Servers | `9200` |
| `OPENSEARCH_USER` | Benutzername | `admin` |
| `OPENSEARCH_PASSWORD` | Passwort | `ComplexPassword123!` |

## Manuelle Ausführung

Zum Testen oder für einmalige Läufe können Sie den Scheduler umgehen und Skripte direkt im Container ausführen:

```bash
# In den Container wechseln
docker exec -it data-preparer bash

# Einzelne Schritte ausführen
python extract_links.py
python download_files.py
python ingest.py
# usw.
```

## Bekannte Limitierungen

*   **Vollständige Verarbeitung**: Derzeit scannen die Konvertierungs- und Ingestion-Skripte bei jedem Lauf alle Dateien. Bei sehr großen Datenmengen sollte dies auf inkrementelle Verarbeitung (nur geänderte Dateien) umgestellt werden.
