# gpt_response_parser.py

"""
GPT Response Parser – robuste Analyse- und Kontextextraktion für GPT-Antworten
Verarbeitet beliebige GPT-Antwortformate (Text, Liste, Dict) und extrahiert relevante Systemdaten
Aktuell fokussiert auf GPTAgent-only-Betrieb – vorbereitet auf spätere Agentenstruktur
"""

from agents.GPTAgent.context_manager import get_context_value
from agents.GPTAgent import startup_loader  # Für "refresh system"

# Optionaler Import: MemoryAgent-Logging
try:
    from agents.Infrastructure_Agents.MemoryAgent.memory_log import log_interaction
except ImportError:
    def log_interaction(**kwargs):
        pass  # Fallback ohne Logging


def get_system_context() -> dict:
    """
    Holt aktuelle Kontextdaten aus GPTAgent-Speicher.
    """
    return {
        "identity": get_context_value("system_identity"),
        "index": get_context_value("index"),
        "json_index": get_context_value("json_index"),
        "agent_registry": get_context_value("agent_registry"),
        "system_modules": get_context_value("system_modules"),
        "session": get_context_value("session_context"),
        "conversation": get_context_value("conversation_context"),
        "memory_log": get_context_value("memory_log"),
        "gpt_config": get_context_value("gpt_config")
    }


def extract_role(response: str, identity_data: dict) -> str:
    """
    Erkennt, auf welche Systemrolle (Agent) sich GPT in seiner Antwort bezieht.
    """
    rollen = identity_data.get("rollen", {})
    for key, definition in rollen.items():
        if isinstance(definition, dict):
            for sub_key in definition.keys():
                if sub_key.lower() in response.lower():
                    return sub_key
        elif isinstance(definition, list):
            for sub_item in definition:
                if sub_item.lower() in response.lower():
                    return sub_item
        else:
            if key.lower() in response.lower():
                return key
    return "unbekannt"


def detect_system_trigger(response: str) -> str:
    """
    Prüft, ob GPT-Antwort systemrelevante Schlüsselwörter enthält (Trigger wie save, export, route etc.)
    """
    trigger_keywords = ["save", "export", "memory", "route", "trigger", "workflow", "loop"]
    for keyword in trigger_keywords:
        if keyword in response.lower():
            return keyword
    return ""


def log_response_analysis(user_input: str, gpt_reply: str) -> None:
    """
    Übergibt Analyseergebnis zur Protokollierung an MemoryAgent (falls aktiv)
    """
    log_interaction(
        user="GPTParser",
        prompt=user_input,
        response=gpt_reply,
        path="gpt_agent_memory_log.json"
    )


def parse_gpt_response(user_input: str, gpt_reply) -> dict:
    """
    Hauptfunktion: Robuste Verarbeitung von GPT-Antworten (Text, Liste, Dict) zu strukturierter Systemantwort
    """

    # 🔁 Spezialfall: Live-Refresh über GPTCommand
    if isinstance(user_input, str) and "refresh system" in user_input.lower():
        refreshed = startup_loader.initialize_system_context()
        return {
            "user_input": user_input,
            "raw_response": "✅ Systemkontext wurde aktualisiert.",
            "used_prompt": get_context_value("gpt_config", {}).get("PROMPT_PATH", "gpt_agent_prompt.json"),
            "summary": "Systemkontext wurde neu geladen.",
            "refreshed_keys": list(refreshed.keys()),
            "status": "success",
            "trigger": "refresh",
            "role": "GPTAgent"
        }

    # ⬇️ Normale Analyse bei GPT-Antwort
    context = get_system_context()
    log_response_analysis(str(user_input), str(gpt_reply))

    parsed = {
        "user_input": user_input,
        "raw_response": gpt_reply,
        "used_prompt": context.get("gpt_config", {}).get("PROMPT_PATH", "gpt_agent_prompt.json"),
        "summary": str(gpt_reply)[:200],
        "context_project_count": len(context.get("index", {})),
        "memory_context_available": bool(context.get("memory_log")),
        "agents_available": list(context.get("agent_registry", {}).keys())
            if isinstance(context.get("agent_registry", {}), dict) else [],
        "modules_loaded": list(context.get("system_modules", {}).keys())
            if isinstance(context.get("system_modules", {}), dict) else []
    }

    # Textantwort (Fließtext)
    if isinstance(gpt_reply, str):
        parsed.update({
            "role": extract_role(gpt_reply, context.get("identity", {})),
            "trigger": detect_system_trigger(gpt_reply),
            "messages": [gpt_reply]
        })
        return parsed

    # Liste (z. B. Agenten- oder Taskvorschläge)
    if isinstance(gpt_reply, list):
        parsed.update({
            "role": "Liste",
            "trigger": "liste",
            "tasks": gpt_reply
        })
        return parsed

    # Dict (strukturierte GPT-Antwort)
    if isinstance(gpt_reply, dict):
        parsed.update({
            "role": gpt_reply.get("role", "GPT"),
            "trigger": gpt_reply.get("trigger", ""),
        })
        parsed.update(gpt_reply)
        return parsed

    # Fallback: Unbekannter Typ
    parsed.update({
        "role": "unbekannt",
        "trigger": "unbekannt",
        "messages": ["⚠️ Unbekanntes Antwortformat"]
    })
    return parsed
