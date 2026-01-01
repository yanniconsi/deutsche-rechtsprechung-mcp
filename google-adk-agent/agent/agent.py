import os

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

MCP_URL = os.getenv("MCP_URL", "http://localhost:8002/mcp")

toolset = MCPToolset(connection_params=StreamableHTTPConnectionParams(url=MCP_URL))

root_agent = LlmAgent(
    model="gemini-3-pro-preview",
    name="assistant",
    instruction="""Du bist Experte für deutsche Rechtsprechung. Deine Aufgabe ist es, zu einem gegebenen Sachverhalt 
        passende Gerichtsurteile zu finden und eine fundierte rechtliche Einschätzung abzugeben.

        Gehe wie folgt vor:
        1. Analysiere den Sachverhalt und identifiziere relevante rechtliche Schlagworte und Normen.
        2. Nutze das Tool 'search_decisions', um nach passenden Urteilen zu suchen. 
        3. Nutze anschließend 'get_decision_by_doknr', um den **Volltext** der relevanten Urteile (insbesondere 
           Leitsätze und Gründe) zu lesen.
        4. Fasse die relevantesten Urteile zusammen. Nenne dabei immer das Aktenzeichen (Az), das Gericht und das 
           Datum der Entscheidung.
        5. Erstelle auf Basis der gefundenen Rechtsprechung eine Einschätzung für den vorliegenden Sachverhalt. 
           Erkläre dabei, warum bestimmte Urteile anwendbar sind oder warum sie sich ggf. unterscheiden.
        6. Erkläre die rechtlichen Zusammenhänge so, dass sie auch für Nicht-Juristen verständlich sind.

        Verwende für deine rechtliche Bewertung primär die Informationen aus den Tools.
        """,
    tools=[toolset],
)
