from langfuse import Langfuse

# Initialisierung
langfuse = Langfuse()

# 1. Prompt aus Langfuse CMS abrufen
prompt = langfuse.get_prompt("kundenservice_antwort")
# 2. Variablen füllen
compiled_prompt = prompt.compile(frage="Wie sende ich mein Paket zurück?")

# 3. An deinen LiteLLM Proxy senden (wie gewohnt)
# Der Proxy kümmert sich um das Tracing, da 'langfuse' in den Callbacks aktiv ist
response = litellm.completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": compiled_prompt}],
    base_url="http://dein-litellm-proxy:4000"
)