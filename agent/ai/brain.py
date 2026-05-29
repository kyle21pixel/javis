"""
J.A.V.I.S. AI Brain — Google Gemini integration for message classification & reply drafting
"""
import google.generativeai as genai
from config import GEMINI_API_KEY, AI_MODEL
from ai.prompts import SYSTEM_PROMPT, CLASSIFY_PROMPT, DRAFT_REPLY_PROMPT

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

_model = genai.GenerativeModel(
    model_name=AI_MODEL,
    system_instruction=SYSTEM_PROMPT
)


def classify_message(body: str) -> str:
    """
    Classify an inbound message into one of:
    INQUIRY | ORDER | COMPLAINT | BOOKING | PARTNERSHIP | SPAM | OTHER
    """
    try:
        prompt = CLASSIFY_PROMPT.format(message=body[:2000])  # cap length
        response = _model.generate_content(prompt)
        category = response.text.strip().upper()
        valid = {"INQUIRY", "ORDER", "COMPLAINT", "BOOKING", "PARTNERSHIP", "SPAM", "OTHER"}
        return category if category in valid else "OTHER"
    except Exception as e:
        print(f"[JAVIS-Brain] classify error: {e}")
        return "OTHER"


def draft_reply(sender: str, subject: str, body: str, channel: str = "email") -> str:
    """
    Generate a professional AI-drafted reply for an inbound message.
    Returns empty string for SPAM or on error.
    """
    try:
        category = classify_message(body)
        if category == "SPAM":
            print(f"[JAVIS-Brain] SPAM detected from {sender} — skipping")
            return ""

        length_hint = (
            "Keep the reply under 160 characters (SMS limit)."
            if channel == "sms"
            else "Write 2–4 short paragraphs. Use a professional email format with greeting and closing."
        )

        prompt = DRAFT_REPLY_PROMPT.format(
            channel=channel,
            sender=sender,
            subject=subject,
            body=body[:3000],
            length_hint=length_hint
        )

        response = _model.generate_content(prompt)
        draft = response.text.strip()
        print(f"[JAVIS-Brain] Drafted {channel} reply for [{category}] from {sender}")
        return draft

    except Exception as e:
        print(f"[JAVIS-Brain] draft_reply error: {e}")
        return ""


def summarise_conversation(messages: list[dict]) -> str:
    """
    Produce a short summary of a conversation thread for the dashboard.
    messages: list of {direction, body}
    """
    try:
        thread = "\n".join(
            f"[{m['direction'].upper()}]: {m['body'][:300]}"
            for m in messages
        )
        prompt = f"Summarise this business conversation in 1–2 sentences:\n\n{thread}"
        response = _model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[JAVIS-Brain] summarise error: {e}")
        return "No summary available."
