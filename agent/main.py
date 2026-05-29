"""
J.A.V.I.S. — Main Entry Point
Starts the database, email poller, and FastAPI server together.
"""
import sys
import os
import uvicorn
import threading
import socket

# Add agent root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
from channels.email_handler import start_email_poller
from queue_bridge import queue_bridge
from config import PORT, DISPATCHER_HOST, DISPATCHER_PORT


def start_dispatcher_listener():
    """
    Listen for messages forwarded by the C dispatcher on the socket port.
    The C dispatcher sends JSON — we parse and re-process here.
    """
    import json
    from channels.sms_handler import handle_inbound_sms
    from ai.brain import draft_reply

    def listen():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((DISPATCHER_HOST, DISPATCHER_PORT))
            srv.listen(32)
            print(f"[JAVIS-Listener] Listening for C dispatcher on port {DISPATCHER_PORT}")
            while True:
                try:
                    conn, addr = srv.accept()
                    with conn:
                        data = conn.recv(8192).decode("utf-8", errors="replace").strip()
                        if not data:
                            continue
                        msg = json.loads(data)
                        channel = msg.get("channel", "")
                        sender  = msg.get("sender", "")
                        body    = msg.get("body", "")
                        subject = msg.get("subject", "")
                        if channel == "sms":
                            handle_inbound_sms(sender, body)
                        elif channel == "email":
                            contact_id = database.upsert_contact(sender, "email")
                            ai_draft   = draft_reply(sender, subject, body, "email")
                            database.save_inbound_message(contact_id, subject, body, ai_draft)
                except Exception as e:
                    print(f"[JAVIS-Listener] Error: {e}")

    t = threading.Thread(target=listen, daemon=True, name="c-dispatcher-listener")
    t.start()


def print_banner():
    print("""
╔══════════════════════════════════════════════════╗
║          J.A.V.I.S.  Business Assistant          ║
║       AI-Powered Email & SMS Handler v2.0        ║
╚══════════════════════════════════════════════════╝
""")


def main():
    print_banner()

    # 1. Initialise database
    database.init_db()
    database.log_event("startup", "J.A.V.I.S. started")

    # 2. Start C queue dispatcher listener
    start_dispatcher_listener()

    # 3. Start email poller (background thread)
    start_email_poller()

    # 4. Report C queue status
    if queue_bridge.is_available():
        print("[JAVIS] ✅ C message queue bridge active")
    else:
        print("[JAVIS] ⚠  C queue bridge inactive (compile core/ first — optional)")

    # 5. Start FastAPI server
    print(f"[JAVIS] 🚀 API server starting on http://localhost:{PORT}")
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
