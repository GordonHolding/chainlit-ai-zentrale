# memory_triggers.py – Triggerlogik für MemoryAgent

import datetime
import schedule
import threading
import time
from agents.Infrastructure_Agents.MemoryAgent import (
    memory_log,
    memory_config,
    memory_agent,
    memory_cleanup
)
from agents.General_Agents.DriveAgent.drive_agent import DriveAgent

# 📌 Trigger bei Systemstart – Initialisierung des Memory Logs
def trigger_on_startup():
    timestamp = datetime.datetime.now().isoformat()
    memory_log.log_system_start(entries=[
        f"[MemoryAgent] Initialisiert um {timestamp}",
        "Trigger: trigger_on_startup()",
        "Status: GPT-Memory und Verlaufsprotokoll aktiv"
    ])
    print("✅ MemoryAgent bereit (Startup Trigger)")

# 🔁 Trigger bei neuer GPT-Nachricht (z. B. Chainlit oder Routing)
def trigger_on_gpt_message(user_id: str, user_message: str, gpt_reply: str):
    memory_agent.log_user_message(user_id, user_message)
    memory_agent.log_assistant_reply(user_id, gpt_reply)
    log_routing(user_id, user_message, gpt_reply)

# 📆 Wöchentlicher Memory Cleanup – montags 09:00 Uhr
def schedule_weekly_cleanup():
    schedule.every().monday.at("09:00").do(trigger_weekly_memory_cleanup)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=run_scheduler)
    thread.daemon = True
    thread.start()

# ▶ Manueller Aufruf des Memory Cleanups – z. B. über Chainlit-Button
def trigger_manual_memory_cleanup():
    result = memory_cleanup.run_memory_cleanup()
    log_cleanup("manual", result)
    return result

def trigger_weekly_memory_cleanup():
    result = memory_cleanup.run_memory_cleanup()
    log_cleanup("weekly", result)
    return result

# 🧾 GPT-Verlaufs-Log (Routing)
def log_routing(user_id, user_message, gpt_reply):
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "agent": "MemoryAgent",
        "trigger": "trigger_on_gpt_message",
        "user_id": user_id,
        "input": user_message[:100],
        "output": gpt_reply[:100]
    }
    agent = DriveAgent()
    agent.append_log_entry(
        log_path="Systemberichte/MEMORY/driveagent_routing_log.json",
        entry=log_entry
    )

# 📁 Log-Eintrag für Cleanup-Vorgang
def log_cleanup(trigger_type: str, result: list):
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "trigger": f"trigger_{trigger_type}_memory_cleanup",
        "agent": "MemoryAgent",
        "status": "✔ abgeschlossen",
        "details": result
    }
    agent = DriveAgent()
    agent.append_log_entry(
        log_path=f"Systemberichte/MEMORY/cleanup_reports/{datetime.datetime.now().date()}_report.json",
        entry=log_entry
    )
