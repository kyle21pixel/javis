"""
J.A.V.I.S. Configuration — loads all settings from .env
"""
import os
from dotenv import load_dotenv

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

# Email (Gmail IMAP/SMTP)
EMAIL_ADDRESS     = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD    = os.getenv("EMAIL_PASSWORD", "")   # App password
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
DATABASE_PATH     = os.getenv("DATABASE_PATH", "javis.db")

# C Queue dispatcher socket
DISPATCHER_HOST   = os.getenv("DISPATCHER_HOST", "127.0.0.1")
DISPATCHER_PORT   = int(os.getenv("DISPATCHER_PORT", 9000))
