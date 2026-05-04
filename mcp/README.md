# MCP Server

Dieses Verzeichnis enthält den MCP-Server (FastMCP) und den Static Server.

## Services

- MCP Server (FastMCP): läuft im Container auf Port `8002`
  - BGH MCP (Host): `http://localhost:8002/mcp`
  - States MCP (Host): `http://localhost:8004/mcp`
- Static Server (Flask): Port `8003`

## Tools

Der MCP Server stellt folgende Tools bereit:

- `search_decisions(query: str, states: list[str] | None = None, limit: int = 10)`
  - `states` filtert nach Bundesland-Kürzeln (z.B. `['bw', 'by']`).
  - Der Filter wird standardmäßig nur im States-Index angewendet (siehe `INDEX_NAME`).
- `get_decision_by_doknr(doknr: str)`

Zusätzlich gibt es Resource-URIs:

- `decision://{doknr}` (liefert ein formatiertes Markdown-Dokument)

## Konfiguration (Environment)

- `OPENSEARCH_HOST`, `OPENSEARCH_PORT`, `OPENSEARCH_USER`, `OPENSEARCH_PASSWORD`
- `INDEX_NAME` (z.B. `court-decisions` oder `court-decisions-states`)
- `STATIC_SERVER_EXTERNAL_URL` (Default: `http://localhost:8003`)
- `ALLOW_STATE_FILTER` (optional): Aktiviert den `states`-Filter unabhängig vom Index-Namen

## Start (empfohlen)

Siehe Root-Compose im Projekt-Root:

```bash
docker compose up --build
```
