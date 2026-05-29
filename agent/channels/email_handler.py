"""
J.A.V.I.S. Email Handler — IMAP polling (read) + SMTP sending (Gmail)
"""
import imaplib
import smtplib
import email
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header

import database
from ai.brain import draft_reply
from config import (
    EMAIL_ADDRESS, EMAIL_PASSWORD,
    IMAP_HOST, IMAP_PORT,
    SMTP_HOST, SMTP_PORT,
    EMAIL_POLL_SECS, AUTO_SEND_REPLIES
)


def _decode_header_value(value: str) -> str:
    parts = decode_header(value)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(str(part))
    return " ".join(decoded)


def send_email(to_addr: str, subject: str, body: str) -> bool:
    """Send an email reply via SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = EMAIL_ADDRESS
        msg["To"]      = to_addr
        msg["Subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_addr, msg.as_string())

        print(f"[JAVIS-Email] ✉ Sent reply to {to_addr}")
        database.log_event("email_sent", f"To: {to_addr} | Subject: {subject}")
        return True
    except Exception as e:
        print(f"[JAVIS-Email] Send error: {e}")
        database.log_event("email_error", str(e))
        return False


def _process_email(mail_msg) -> None:
    """Parse a single email message and hand it to the AI brain."""
    try:
        sender  = mail_msg.get("From", "unknown")
        subject = _decode_header_value(mail_msg.get("Subject", "(no subject)"))
        body    = ""

        if mail_msg.is_multipart():
            for part in mail_msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
        else:
            body = mail_msg.get_payload(decode=True).decode("utf-8", errors="replace")

        body = body.strip()[:4000]
        if not body:
            return

        print(f"[JAVIS-Email] 📨 New email from {sender} | {subject}")

        # Save contact + message
        contact_id = database.upsert_contact(sender, "email")
        ai_draft   = draft_reply(sender, subject, body, channel="email")
        msg_id     = database.save_inbound_message(contact_id, subject, body, ai_draft)

        # Auto-send or queue for approval
        if AUTO_SEND_REPLIES and ai_draft:
            ok = send_email(sender, subject, ai_draft)
            if ok:
                database.mark_message_sent(msg_id, auto=True)
        else:
            print(f"[JAVIS-Email] Draft queued for approval (msg_id={msg_id})")

    except Exception as e:
        print(f"[JAVIS-Email] Process error: {e}")


def _poll_inbox() -> None:
    """Connect to IMAP and fetch unseen emails."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")

        _, msg_nums = mail.search(None, "UNSEEN")
        ids = msg_nums[0].split()

        if ids:
            print(f"[JAVIS-Email] Found {len(ids)} new email(s)")

        for num in ids:
            _, data = mail.fetch(num, "(RFC822)")
            raw = data[0][1]
            mail_msg = email.message_from_bytes(raw)
            _process_email(mail_msg)
            # Mark as seen
            mail.store(num, "+FLAGS", "\\Seen")

        mail.logout()
    except Exception as e:
        print(f"[JAVIS-Email] Poll error: {e}")


def start_email_poller() -> None:
    """Run email polling in a background thread forever."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("[JAVIS-Email] ⚠ No email credentials — email handler disabled.")
        return

    def loop():
        print(f"[JAVIS-Email] Polling {EMAIL_ADDRESS} every {EMAIL_POLL_SECS}s")
        while True:
            _poll_inbox()
            time.sleep(EMAIL_POLL_SECS)

    t = threading.Thread(target=loop, daemon=True, name="email-poller")
    t.start()
