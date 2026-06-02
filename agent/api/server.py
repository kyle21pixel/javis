"""
J.A.V.I.S. FastAPI Server — REST API for the React dashboard
"""
import sys
import os
import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
import traceback

import database
from channels.email_handler import send_email
from channels.sms_handler import handle_inbound_sms, send_sms
from ai.brain import draft_reply
from security import authenticate_user, create_access_token, get_current_user
from rate_limiter import RateLimiter
from health import health_status
from errors import AuthenticationError, AuthorizationError, NotFoundError, ValidationError, RateLimitError, ExternalServiceError
from logging_config import logger

app = FastAPI(
    title="J.A.V.I.S. Business Assistant API",
    description="AI-powered email & SMS handler for your business",
    version="2.0.0"
)

limiter = RateLimiter()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        database.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(status_code=429, detail="Too many requests")
    return await call_next(request)


@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Catch and log all exceptions"""
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        # Convert custom exceptions to HTTP exceptions
        if isinstance(exc, AuthenticationError):
            raise exc.to_http_exception()
        if isinstance(exc, AuthorizationError):
            raise exc.to_http_exception()
        if isinstance(exc, NotFoundError):
            raise exc.to_http_exception()
        if isinstance(exc, ValidationError):
            raise exc.to_http_exception()
        if isinstance(exc, RateLimitError):
            raise exc.to_http_exception()
        if isinstance(exc, ExternalServiceError):
            raise exc.to_http_exception()
        # Generic error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Log HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}", extra={"path": request.url.path})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ── Request Models ────────────────────────────────────────────────────────────

class AuthRequest(BaseModel):
    username: str
    password: str


class ApproveRequest(BaseModel):
    msg_id: int
    edited_draft: str = ""   # optional — use edited version instead of original


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str


class SendSMSRequest(BaseModel):
    to: str
    body: str


# ── Health & Diagnostics ──────────────────────────────────────────────────────

@app.get("/health")
async def health_probe():
    """Kubernetes/Docker liveness probe"""
    await health_status.refresh()
    if health_status.is_healthy:
        return {"status": "ok", "details": health_status.to_dict()}
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "error", "details": health_status.to_dict()},
    )


@app.get("/readiness")
async def readiness_probe():
    """Kubernetes/Docker readiness probe"""
    await health_status.refresh()
    if health_status.is_ready:
        return {"ready": True, "timestamp": datetime.datetime.utcnow().isoformat()}
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"ready": False, "reason": "Dependencies unavailable"},
    )


@app.get("/version")
def version_info():
    """API version and build info"""
    return {
        "version": "2.0.0",
        "service": "J.A.V.I.S. Business Assistant",
        "environment": os.getenv("ENV", "development"),
    }


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "running", "service": "J.A.V.I.S. Business Assistant"}


@app.post("/api/token")
def login(credentials: AuthRequest):
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        logger.warning(f"Login failed for user {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": user.username})
    database.log_event("login", f"User {user.username} logged in", user.username)
    logger.info(f"User {user.username} logged in")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/me")
def me(current_user=Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats(current_user=Depends(get_current_user)):
    database.log_event("stats_view", f"User {current_user.username} viewed stats", current_user.username)
    return database.get_stats()


# ── Conversations ─────────────────────────────────────────────────────────────

@app.get("/api/conversations")
def get_conversations(limit: int = 50, current_user=Depends(get_current_user)):
    database.log_event("conversations_view", f"User {current_user.username} viewed conversations", current_user.username)
    return database.get_all_conversations(limit)


# ── Pending messages (awaiting approval) ─────────────────────────────────────

@app.get("/api/pending")
def get_pending(current_user=Depends(get_current_user)):
    database.log_event("pending_view", f"User {current_user.username} viewed pending messages", current_user.username)
    return database.get_pending_messages()


# ── Approve & send a draft ────────────────────────────────────────────────────

@app.post("/api/approve")
async def approve_message(req: ApproveRequest, current_user=Depends(get_current_user)):
    pending = database.get_pending_messages()
    target  = next((m for m in pending if m["id"] == req.msg_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Message not found or already sent")

    body_to_send = req.edited_draft.strip() if req.edited_draft.strip() else target["ai_draft"]
    channel      = target["channel"]
    identifier   = target["identifier"]

    if channel == "email":
        ok = send_email(identifier, target["subject"], body_to_send)
    else:
        ok = send_sms(identifier, body_to_send)

    if ok:
        database.mark_message_sent(req.msg_id, auto=False)
        return {"success": True, "msg_id": req.msg_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to send message")


# ── Reject / dismiss a draft ──────────────────────────────────────────────────

@app.post("/api/reject/{msg_id}")
def reject_message(msg_id: int, current_user=Depends(get_current_user)):
    database.mark_message_sent(msg_id, auto=False)   # mark resolved without sending
    return {"success": True, "msg_id": msg_id}


# ── Manual send ───────────────────────────────────────────────────────────────

@app.post("/api/send/email")
def manual_send_email(req: SendEmailRequest, current_user=Depends(get_current_user)):
    ok = send_email(req.to, req.subject, req.body)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send email")
    return {"success": True}


@app.post("/api/send/sms")
def manual_send_sms(req: SendSMSRequest, current_user=Depends(get_current_user)):
    ok = send_sms(req.to, req.body)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send SMS")
    return {"success": True}


# ── Twilio SMS inbound webhook ────────────────────────────────────────────────

@app.post("/webhook/sms/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    from_number = form.get("From", "")
    body        = form.get("Body", "")
    if from_number and body:
        handle_inbound_sms(from_number, body)
        database.log_event("twilio_webhook", f"Inbound Twilio SMS from {from_number}", "webhook")
    return JSONResponse(content={"status": "received"})


# ── Africa's Talking SMS inbound webhook ──────────────────────────────────────

@app.post("/webhook/sms/at")
async def at_webhook(request: Request):
    form = await request.form()
    from_number = form.get("from", "")
    body        = form.get("text", "")
    if from_number and body:
        handle_inbound_sms(from_number, body)
        database.log_event("africastalking_webhook", f"Inbound AT SMS from {from_number}", "webhook")
    return JSONResponse(content={"status": "received"})


# ── AI re-draft endpoint ──────────────────────────────────────────────────────

@app.post("/api/redraft/{msg_id}")
def redraft_message(msg_id: int, current_user=Depends(get_current_user)):
    pending = database.get_pending_messages()
    target  = next((m for m in pending if m["id"] == msg_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Message not found")
    new_draft = draft_reply(target["identifier"], target["subject"], target["body"], target["channel"])
    database.update_ai_draft(msg_id, new_draft)
    database.log_event("redraft", f"User {current_user.username} redrafted msg {msg_id}", current_user.username)
    return {"draft": new_draft}


# ── Analytics & Reporting ───────────────────────────────────────────────────────

@app.get("/api/analytics/summary")
def analytics_summary(days: int = 7, current_user=Depends(get_current_user)):
    """Get performance metrics for the last N days (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    database.log_event("analytics_view", f"User {current_user.username} viewed analytics", current_user.username)
    return database.get_analytics_summary(days)


@app.get("/api/analytics/draft-history/{msg_id}")
def draft_history(msg_id: int, current_user=Depends(get_current_user)):
    """Get draft version history for a message"""
    history = database.get_draft_history(msg_id)
    if not history:
        raise HTTPException(status_code=404, detail="Message not found or no draft history")
    database.log_event("draft_history_view", f"User {current_user.username} viewed draft history for msg {msg_id}", current_user.username)
    return {"msg_id": msg_id, "versions": history}
