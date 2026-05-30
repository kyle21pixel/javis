"""
J.A.V.I.S. Configuration — loads all settings from .env
"""
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken

load_dotenv()

# Server
PORT = int(os.getenv("PORT", 8000))

# AI
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")
AI_MODEL          = os.getenv("AI_MODEL", "gemini-1.5-flash")
AUTO_SEND_REPLIES = os.getenv("AUTO_SEND_REPLIES", "false").lower() == "true"

# Business identity
BUSINESS_NAME     = os.getenv("BUSINESS_NAME", "My Business")
BUSINESS_TYPE     = os.getenv("BUSINESS_TYPE", "general")
OWNER_NAME        = os.getenv("OWNER_NAME", "Kyle")

# Auth
JWT_SECRET                = os.getenv("JWT_SECRET", "change-this-secret")
JWT_ALGORITHM             = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
DEFAULT_ADMIN_USER        = os.getenv("DEFAULT_ADMIN_USER", "admin")
DEFAULT_ADMIN_PASSWORD    = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

# Email (Gmail IMAP/SMTP)
EMAIL_ADDRESS     = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD    = os.getenv("EMAIL_PASSWORD", "")   # App password or encrypted value
IMAP_HOST         = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT         = int(os.getenv("IMAP_PORT", 993))
SMTP_HOST         = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT         = int(os.getenv("SMTP_PORT", 587))
EMAIL_POLL_SECS   = int(os.getenv("EMAIL_POLL_SECS", 30))

# SMS — Twilio
TWILIO_ACCOUNT_SID  = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# SMS — Africa's Talking (alternative)
AT_API_KEY          = os.getenv("AT_API_KEY", "")
AT_USERNAME         = os.getenv("AT_USERNAME", "")
AT_SENDER_ID        = os.getenv("AT_SENDER_ID", "")
SMS_PROVIDER        = os.getenv("SMS_PROVIDER", "twilio")   # "twilio" | "africastalking"

# Database
DATABASE_PATH       = os.getenv("DATABASE_PATH", "javis.db")
DATABASE_URL        = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# Redis cache / rate limiting
REDIS_URL           = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ENABLE_REDIS_CACHE  = os.getenv("ENABLE_REDIS_CACHE", "false").lower() == "true"
RATE_LIMIT_WINDOW_SECS = int(os.getenv("RATE_LIMIT_WINDOW_SECS", 60))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 60))

# Retry strategy for outbound sends
SEND_RETRY_COUNT    = int(os.getenv("SEND_RETRY_COUNT", 3))
SEND_RETRY_BACKOFF  = int(os.getenv("SEND_RETRY_BACKOFF", 2))

# C Queue dispatcher socket
DISPATCHER_HOST   = os.getenv("DISPATCHER_HOST", "127.0.0.1")
DISPATCHER_PORT   = int(os.getenv("DISPATCHER_PORT", 9000))

# Encryption helpers
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")


def _decrypt_if_needed(value: str) -> str:
    if not value or not value.startswith("ENC(") or not value.endswith(")"):
        return value
    if not ENCRYPTION_KEY:
        raise RuntimeError("Encrypted secret provided but ENCRYPTION_KEY is not set.")
    token = value[4:-1]
    try:
        return Fernet(ENCRYPTION_KEY.encode()).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("Failed to decrypt secret from environment. Check ENCRYPTION_KEY.") from exc

EMAIL_PASSWORD = _decrypt_if_needed(EMAIL_PASSWORD)
TWILIO_AUTH_TOKEN = _decrypt_if_needed(TWILIO_AUTH_TOKEN)
AT_API_KEY = _decrypt_if_needed(AT_API_KEY)
