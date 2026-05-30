"""
J.A.V.I.S. SMS Handler — supports Twilio and Africa's Talking
Receives webhooks and sends AI-drafted replies
"""
import time
import database
from ai.brain import draft_reply
from config import (
    SMS_PROVIDER,
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER,
    AT_API_KEY, AT_USERNAME, AT_SENDER_ID,
    AUTO_SEND_REPLIES,
    SEND_RETRY_COUNT, SEND_RETRY_BACKOFF,
)


# ── Twilio sender ────────────────────────────────────────────────────────────

def _send_twilio(to_number: str, body: str) -> bool:
    for attempt in range(1, SEND_RETRY_COUNT + 1):
        try:
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=body,
                from_=TWILIO_PHONE_NUMBER,
                to=to_number
            )
            print(f"[JAVIS-SMS] ✉ Twilio SMS sent to {to_number}")
            return True
        except Exception as e:
            print(f"[JAVIS-SMS] Twilio error (attempt {attempt}/{SEND_RETRY_COUNT}): {e}")
            if attempt < SEND_RETRY_COUNT:
                time.sleep(SEND_RETRY_BACKOFF ** (attempt - 1))
    return False


# ── Africa's Talking sender ──────────────────────────────────────────────────

def _send_africastalking(to_number: str, body: str) -> bool:
    for attempt in range(1, SEND_RETRY_COUNT + 1):
        try:
            import africastalking
            africastalking.initialize(AT_USERNAME, AT_API_KEY)
            sms = africastalking.SMS
            sms.send(body, [to_number], sender_id=AT_SENDER_ID or None)
            print(f"[JAVIS-SMS] ✉ Africa's Talking SMS sent to {to_number}")
            return True
        except Exception as e:
            print(f"[JAVIS-SMS] Africa's Talking error (attempt {attempt}/{SEND_RETRY_COUNT}): {e}")
            if attempt < SEND_RETRY_COUNT:
                time.sleep(SEND_RETRY_BACKOFF ** (attempt - 1))
    return False


# ── Unified send ─────────────────────────────────────────────────────────────

def send_sms(to_number: str, body: str) -> bool:
    """Send an SMS via the configured provider, with provider fallback when available."""
    if SMS_PROVIDER == "africastalking":
        return _send_africastalking(to_number, body)

    sent = _send_twilio(to_number, body)
    if not sent and AT_API_KEY and AT_USERNAME:
        print("[JAVIS-SMS] Twilio failed, falling back to Africa's Talking")
        return _send_africastalking(to_number, body)
    return sent


# ── Inbound webhook handler ──────────────────────────────────────────────────

def handle_inbound_sms(from_number: str, body: str) -> dict:
    """
    Called by the FastAPI webhook route when an SMS arrives.
    Saves to DB, drafts a reply, optionally auto-sends.
    Returns the AI draft and message ID.
    """
    print(f"[JAVIS-SMS] 📱 Inbound SMS from {from_number}: {body[:80]}")

    contact_id = database.upsert_contact(from_number, "sms")
    ai_draft   = draft_reply(from_number, "", body, channel="sms")
    msg_id     = database.save_inbound_message(contact_id, "SMS", body, ai_draft)

    if AUTO_SEND_REPLIES and ai_draft:
        ok = send_sms(from_number, ai_draft)
        if ok:
            database.mark_message_sent(msg_id, auto=True)
            database.log_event("sms_auto_sent", f"To: {from_number}")

    return {"msg_id": msg_id, "draft": ai_draft}
