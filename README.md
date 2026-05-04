# Rechtsprechung MCP Server

Ein [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/spec) Server, der die Daten von [Rechtsprechung im Internet](https://www.rechtsprechung-im-internet.de) (Entscheidungen des Bundesverfassungsgerichts, der obersten Gerichtshöfe des Bundes sowie des Bundespatentgerichts ab dem Jahr 2010) durchsuchbar und für LLMs (Large Language Models) zugänglich macht.

## Projektübersicht

Dieses Projekt stellt eine Schnittstelle bereit, über die KI-Agenten und Anwendungen auf eine umfangreiche Datenbank deutscher Rechtsprechung zugreifen können. Es besteht aus drei Hauptkomponenten:

1.  **MCP Server**: Der Kern des Projekts. Ein FastMCP-Server, der Tools zur Suche und zum Abruf von Volltexten bereitstellt.
2.  **Data Preprocessing**: Eine Pipeline, um Urteile von "Rechtsprechung im Internet" herunterzuladen, zu bereinigen und in ein durchsuchbares Format zu konvertieren.
3.  **Beispiel-Agent**: Ein Google ADK Agent, der demonstriert, wie man den MCP Server nutzen kann, um juristische Fragestellungen zu beantworten.

## 1. MCP Server

Der Server läuft in einem Docker-Container und nutzt OpenSearch als Backend für schnelle und flexible Volltextsuchen.

### Funktionen (Tools)

*   `search_decisions(query: str, states: list[str] | None, limit: int)`: Sucht nach Urteilen basierend auf Text, Aktenzeichen oder Normen.
    *   `states` ist optional (z.B. `['bw', 'by']`). Der Filter wird standardmäßig nur im **States**-Index angewendet.
*   `get_decision_by_doknr(doknr: str)`: Ruft den vollständigen Text (Leitsätze, Gründe, Metadaten) eines spezifischen Urteils ab.

Die Tool-Antworten enthalten u.a.:

*   `doknr` (Dokumentnummer)
*   `source` (relativer Dateipfad im geteilten `mcp/data` Volume)
*   `url` (klickbarer Volltext-Link über den Static Server)
*   `resource_uri` (z.B. `decision://<doknr>`)

### Technologie

*   **Python**: Implementierung des Servers mit `mcp.server.fastmcp`.
*   **OpenSearch**: Speicherung und Indizierung der Urteile.
*   **Docker Compose**: Orchestrierung von Server und Datenbank.

### Starten des Servers

```bash
docker compose up --build
```

BGH MCP: `http://localhost:8002/mcp` • States MCP: `http://localhost:8004/mcp` • Static Server: `http://localhost:8003/health`

Hinweis: Das Root-`docker-compose.yml` ist der empfohlene Einstiegspunkt.

### Beispiele

- Suche in States (mit Filter): `search_decisions("Kündigung Eigenbedarf", states=["bw"], limit=10)`
- Suche in BGH: `search_decisions("BGH IX ZB 72/08", limit=10)`
- Volltext: `get_decision_by_doknr("<DOKNR>")`

## 2. Data Preprocessing

Bevor der Server nützlich ist, müssen Daten ingestiert werden. Dafür gibt es die Pipeline im Ordner `pipeline/`.

Ein einmaliger Lauf (One-shot) über Docker Compose:

```bash
docker compose --profile pipelinerun up --build data-preparer
```

*   **Quelle**: [Rechtsprechung im Internet](https://www.rechtsprechung-im-internet.de/) (Open Data).
*   **Prozess (high-level)**: Download/Update → Extraktion/Parsing → Markdown/JSON erzeugen → In OpenSearch indizieren.

Detaillierte Anweisungen finden sich in `pipeline/README.md`.

## 3. Beispiel-Agent (Google ADK)

Im Ordner `google-adk-agent/` befindet sich ein Referenz-Agent, der zeigt, wie man den MCP-Server in eine Anwendung integriert.

*   **Framework**: Google Agent Development Kit (ADK).
*   **Modell**: `gemini-3.1-flash-lite-preview` (in `google-adk-agent/agent/agent.py` konfiguriert).
*   **Funktion**: Der Agent analysiert Sachverhalte, sucht selbstständig passende Urteile und gibt eine rechtliche Einschätzung ab.

Siehe `google-adk-agent/agent/README.md` für Details zur Einrichtung.

## Voraussetzung

*   Docker & Docker Compose
*   Python 3.10+ (für lokale Entwicklung/Preprocessing)
*   Zugriff auf Gemini API (für den Agenten)

Für den Pipeline-Lauf (Bundesländer) wird zusätzlich eine `.env` Datei benötigt (Vorlage: `.env.example`).

## Lizenz

Dieses Projekt ist unter der [MIT License](LICENSE) lizenziert. Die Daten stammen vom Bundesministerium der Justiz und dem Bundesamt für Justiz.
