# Google ADK Agent - Experte für deutsche Rechtsprechung

Dieser Agent demonstriert die Nutzung des **Google Agent Development Kit (ADK)** in Kombination mit dem **Model Context Protocol (MCP)**.

Der Agent agiert als Experte für deutsche Rechtsprechung. Er nutzt einen über MCP angebundenen Tool-Server (`court-decisions-mcp`), um Gerichtsurteile zu recherchieren, Volltexte zu analysieren und rechtliche Einschätzungen zu Sachverhalten abzugeben.

## Funktionsweise

Der Agent ist so instruiert, dass er:
1.  Einen Sachverhalt analysiert und relevante rechtliche Schlagworte identifiziert.
2.  Über das Tool `search_decisions` nach passenden Urteilen sucht.
3.  Mittels `get_decision_by_doknr` die Volltexte relevanter Entscheidungen abruft.
4.  Relevante Urteile mit Aktenzeichen, Gericht und Datum zusammenfasst.
5.  Eine fundierte rechtliche Einschätzung auf Basis der gefundenen Rechtsprechung erstellt.
6.  Komplexe juristische Sachverhalte für Nicht-Juristen verständlich erklärt.

Er verwendet dabei das Modell `gemini-3.1-flash-lite-preview` (siehe `agent/agent.py`).

## Voraussetzungen

*   Python 3.10+
*   Installiertes `google-adk`
*   Zugriff auf Google Gemini Modelle (Vertex AI oder AI Studio API Key). Einen API Key kannst du unter [ai.google.dev/gemini-api/docs/api-key](https://ai.google.dev/gemini-api/docs/api-key) erstellen.
*   Interner oder externer Zugriff auf den konfigurierten MCP-Server (konfigurierbar über die Umgebungsvariable `MCP_URL`).

    - BGH MCP: `http://localhost:8002/mcp`
    - States MCP: `http://localhost:8004/mcp`

    Hinweis: Wenn du im States-MCP suchst, kannst du (optional) den `states` Parameter nutzen, um die Suche auf bestimmte Bundesländer einzuschränken (z.B. `['bw']`).

## Installation & Nutzung

1.  **Navigieren in das Verzeichnis:**
    ```bash
    cd google-adk-agent/agent
    ```

2.  **Agent starten:**
    ```bash
    export GEMINI_API_KEY=<YOUR_API_KEY_HERE>
    export MCP_URL=http://localhost:8004/mcp
    adk web
    ```

    PowerShell (Windows) Beispiel:
    ```powershell
    $env:GEMINI_API_KEY = "<YOUR_API_KEY_HERE>"
    $env:MCP_URL = "http://localhost:8004/mcp"
    adk web
    ```

## Code-Struktur

Die Definition des Agenten befindet sich in `agent/agent.py`:

*   **`MCPToolset`**: Verbindet den Agenten mit dem externen MCP-Server.
*   **`LlmAgent`**: Konfiguriert den Agenten mit Modell (`gemini-3.1-flash-lite-preview`), Namen und spezifischen Instruktionen (System Prompt).

```python
# Auszug aus agent/agent.py
toolset = MCPToolset(connection_params=StreamableHTTPConnectionParams(url='...'))

root_agent = LlmAgent(
    model="gemini-3.1-flash-lite-preview",
    instruction="Du bist Experte für deutsche Rechtsprechung...",
    tools=[toolset],
)
```
