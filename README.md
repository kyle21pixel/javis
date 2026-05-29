# J.A.V.I.S. — Just A Very Intelligent System
### AI-Powered Business Email & SMS Assistant

Built with **Python** (AI brain + API) · **C** (message queue engine) · **React + Node.js** (dashboard)

---

## 🗂 Project Structure

```
JAVIS/
├── core/           ← C message queue engine (ring buffer + dispatcher)
├── agent/          ← Python AI brain (Gemini, email, SMS, FastAPI)
└── dashboard/      ← React + Vite web dashboard
```

---

## ⚡ Quick Start

### 1. Set up Python Agent

```bash
cd agent
copy .env.example .env
# → Edit .env with your real credentials

pip install -r requirements.txt
python main.py
```

> API runs at **http://localhost:8000**

---

### 2. Start the React Dashboard

```bash
cd dashboard
npm install
npm run dev
```

> Dashboard runs at **http://localhost:5173**

---

### 3. (Optional) Compile the C Queue Engine

Requires GCC / MinGW on Windows:

```bash
cd core
make all
```

This produces `javis_queue.dll` (Windows) used by Python for high-speed message routing.

---

## 🔑 Environment Variables (`agent/.env`)

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (free at ai.google.dev) |
| `EMAIL_ADDRESS` | Your Gmail address |
| `EMAIL_PASSWORD` | Gmail **App Password** (not your real password) |
| `AUTO_SEND_REPLIES` | `true` = auto-send · `false` = draft approval mode |
| `SMS_PROVIDER` | `twilio` or `africastalking` |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number |
| `BUSINESS_NAME` | Your business name (tunes AI responses) |
| `OWNER_NAME` | Your name (used in AI sign-offs) |

---

## 📱 SMS Webhooks

Point your SMS provider's webhook to:

- **Twilio**: `POST http://your-server:8000/webhook/sms/twilio`
- **Africa's Talking**: `POST http://your-server:8000/webhook/sms/at`

Use [ngrok](https://ngrok.com) for local testing:
```bash
ngrok http 8000
```

---

## 📧 Gmail Setup

1. Go to **Google Account → Security → 2-Step Verification** → enable it
2. Go to **App Passwords** → create one for "Mail"
3. Use that App Password as `EMAIL_PASSWORD` in `.env`

---

## 🧠 How It Works

```
Inbound Email/SMS
      ↓
C Ring Buffer Queue (high-speed)
      ↓
Python AI Brain (Gemini)
   → Classifies: INQUIRY / ORDER / COMPLAINT / BOOKING / SPAM
   → Drafts professional reply
      ↓
Draft saved to SQLite DB
      ↓
  AUTO_SEND=true?
   Yes → Sends immediately
   No  → Queued in dashboard for your approval
      ↓
React Dashboard shows live feed
You review → Edit → Approve & Send
```

---

## 🚀 API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/stats` | Live stats |
| GET | `/api/conversations` | All conversations |
| GET | `/api/pending` | Messages awaiting approval |
| POST | `/api/approve` | Approve & send a draft |
| POST | `/api/reject/{id}` | Dismiss a message |
| POST | `/api/redraft/{id}` | Regenerate AI draft |
| POST | `/api/send/email` | Send email manually |
| POST | `/api/send/sms` | Send SMS manually |
| POST | `/webhook/sms/twilio` | Twilio inbound webhook |
| POST | `/webhook/sms/at` | Africa's Talking webhook |
