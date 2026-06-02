"""
J.A.V.I.S. Database — SQLAlchemy storage for messages, conversations, contacts, logs, and users.
"""
import datetime
import json
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config import DATABASE_URL, ENABLE_REDIS_CACHE, DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASSWORD
from redis_client import redis_client
from hash_utils import get_password_hash

Base = declarative_base()
_engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    future=True,
)
SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, future=True)


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, default="")
    channel = Column(String, default="email")
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    total_msgs = Column(Integer, default=0)
    conversations = relationship("Conversation", back_populates="contact")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)
    subject = Column(String, default="")
    status = Column(String, default="open")
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    contact = relationship("Contact", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    direction = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    ai_draft = Column(Text, default="")
    status = Column(String, default="pending")
    created_at = Column(DateTime)
    conversation = relationship("Conversation", back_populates="messages")


class ActivityLog(Base):
    __tablename__ = "activity_log"
    id = Column(Integer, primary_key=True, index=True)
    event = Column(String, nullable=False)
    detail = Column(Text, default="")
    user = Column(String, default="")
    created_at = Column(DateTime)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="operator")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class DraftVersion(Base):
    """Audit trail for AI draft changes — allows rollback and history viewing"""
    __tablename__ = "draft_versions"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    draft_text = Column(Text, nullable=False)
    reason = Column(String, default="")  # "redraft", "edit", "ai_revision"
    created_by = Column(String, default="")  # username
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class MessageAnalytics(Base):
    """Message-level metrics for reporting and analytics"""
    __tablename__ = "message_analytics"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    channel = Column(String, nullable=False)  # "email" or "sms"
    ai_draft_generated_at = Column(DateTime)
    approved_at = Column(DateTime)
    sent_at = Column(DateTime)
    approval_time_seconds = Column(Integer)  # time between draft and approval
    total_time_seconds = Column(Integer)  # inbound → sent
    auto_sent = Column(Integer, default=0)  # 1 if auto-sent, 0 if manual
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=_engine)
    with SessionLocal() as session:
        if not session.query(User).filter(User.username == DEFAULT_ADMIN_USER).first():
            default_user = User(
                username=DEFAULT_ADMIN_USER,
                hashed_password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
                role="admin",
            )
            session.add(default_user)
            session.commit()
            print(f"[JAVIS-DB] Default admin user created: {DEFAULT_ADMIN_USER}")
    print("[JAVIS-DB] Database initialised:", DATABASE_URL)


def get_session():
    return SessionLocal()


def log_event(event: str, detail: str = "", user: str = ""):
    with get_session() as session:
        session.add(ActivityLog(event=event, detail=detail, user=user, created_at=datetime.datetime.utcnow()))
        session.commit()


def get_user_by_username(username: str):
    with get_session() as session:
        return session.query(User).filter(User.username == username).first()


def create_user(username: str, password: str, role: str = "operator"):
    with get_session() as session:
        hashed = get_password_hash(password)
        user = User(username=username, hashed_password=hashed, role=role)
        session.add(user)
        session.commit()
        return user


def upsert_contact(identifier: str, channel: str, name: str = "") -> int:
    now = datetime.datetime.utcnow()
    with get_session() as session:
        contact = session.query(Contact).filter(Contact.identifier == identifier).first()
        if contact:
            contact.last_seen = now
            contact.total_msgs += 1
            session.commit()
            return contact.id

        contact = Contact(
            identifier=identifier,
            name=name,
            channel=channel,
            first_seen=now,
            last_seen=now,
            total_msgs=1,
        )
        session.add(contact)
        session.commit()
        return contact.id


def save_inbound_message(contact_id: int, subject: str, body: str, ai_draft: str) -> int:
    now = datetime.datetime.utcnow()
    with get_session() as session:
        conv = (
            session.query(Conversation)
            .filter(Conversation.contact_id == contact_id, Conversation.status == "open")
            .order_by(Conversation.id.desc())
            .first()
        )
        if conv:
            conv.updated_at = now
            conv.subject = subject or conv.subject
        else:
            conv = Conversation(
                contact_id=contact_id,
                subject=subject,
                status="open",
                created_at=now,
                updated_at=now,
            )
            session.add(conv)
            session.flush()
        message = Message(
            conversation_id=conv.id,
            direction="inbound",
            body=body,
            ai_draft=ai_draft,
            status="pending",
            created_at=now,
        )
        session.add(message)
        session.commit()
        invalidate_stats_cache()
        return message.id


def mark_message_sent(msg_id: int, auto: bool = False):
    status = "auto_sent" if auto else "sent"
    with get_session() as session:
        message = session.query(Message).filter(Message.id == msg_id).first()
        if message:
            message.status = status
            session.commit()
            invalidate_stats_cache()


def update_ai_draft(msg_id: int, draft: str):
    with get_session() as session:
        message = session.query(Message).filter(Message.id == msg_id).first()
        if message:
            message.ai_draft = draft
            session.commit()
            invalidate_stats_cache()


def get_pending_messages():
    if redis_client:
        cached = redis_client.get("javis:pending")
        if cached:
            return json.loads(cached)
    with get_session() as session:
        rows = (
            session.query(Message, Conversation, Contact)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .join(Contact, Conversation.contact_id == Contact.id)
            .filter(Message.status == "pending")
            .order_by(Message.created_at.desc())
            .all()
        )
        results = [
            {
                "id": msg.id,
                "body": msg.body,
                "ai_draft": msg.ai_draft,
                "created_at": msg.created_at.isoformat(),
                "identifier": contact.identifier,
                "name": contact.name,
                "channel": contact.channel,
                "subject": conv.subject,
                "conv_id": conv.id,
            }
            for msg, conv, contact in rows
        ]
        if redis_client:
            redis_client.set("javis:pending", json.dumps(results), ex=10)
        return results


def get_all_conversations(limit: int = 50):
    with get_session() as session:
        rows = (
            session.query(
                Conversation.id,
                Conversation.subject,
                Conversation.status,
                Conversation.updated_at,
                Contact.identifier,
                Contact.name,
                Contact.channel,
                func.count(Message.id).label("msg_count"),
            )
            .join(Contact, Conversation.contact_id == Contact.id)
            .outerjoin(Message, Message.conversation_id == Conversation.id)
            .group_by(Conversation.id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.id,
                "subject": row.subject,
                "status": row.status,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "identifier": row.identifier,
                "name": row.name,
                "channel": row.channel,
                "msg_count": row.msg_count,
            }
            for row in rows
        ]


def get_stats():
    if redis_client:
        cached = redis_client.get("javis:stats")
        if cached:
            return json.loads(cached)
    with get_session() as session:
        today = datetime.datetime.utcnow().date()
        stats = {
            "total_messages": session.query(func.count(Message.id)).scalar() or 0,
            "pending_approval": session.query(func.count(Message.id)).filter(Message.status == "pending").scalar() or 0,
            "sent_today": session.query(func.count(Message.id)).filter(
                Message.status.in_(["sent", "auto_sent"]),
                func.date(Message.created_at) == today,
            ).scalar() or 0,
            "open_conversations": session.query(func.count(Conversation.id)).filter(Conversation.status == "open").scalar() or 0,
            "total_contacts": session.query(func.count(Contact.id)).scalar() or 0,
        }
        if redis_client:
            redis_client.set("javis:stats", json.dumps(stats), ex=15)
        return stats


def invalidate_stats_cache():
    if redis_client:
        redis_client.delete("javis:stats")
        redis_client.delete("javis:pending")


# ── Draft Versioning ──────────────────────────────────────────────────────────

def save_draft_version(msg_id: int, draft_text: str, reason: str = "", created_by: str = "") -> int:
    """Save a new draft version"""
    with get_session() as session:
        # Get current highest version number
        max_version = session.query(func.max(DraftVersion.version_number)).filter(
            DraftVersion.message_id == msg_id
        ).scalar() or 0
        
        version = DraftVersion(
            message_id=msg_id,
            version_number=max_version + 1,
            draft_text=draft_text,
            reason=reason,
            created_by=created_by,
        )
        session.add(version)
        session.commit()
        return version.id


def get_draft_history(msg_id: int):
    """Get all versions of a draft"""
    with get_session() as session:
        versions = session.query(DraftVersion).filter(
            DraftVersion.message_id == msg_id
        ).order_by(DraftVersion.version_number.desc()).all()
        return [
            {
                "version": v.version_number,
                "text": v.draft_text,
                "reason": v.reason,
                "created_by": v.created_by,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ]


# ── Message Analytics ────────────────────────────────────────────────────────

def create_message_analytics(msg_id: int, channel: str):
    """Create analytics record when message arrives"""
    with get_session() as session:
        analytics = MessageAnalytics(
            message_id=msg_id,
            channel=channel,
            ai_draft_generated_at=datetime.datetime.utcnow(),
        )
        session.add(analytics)
        session.commit()


def record_approval(msg_id: int):
    """Record when user approves a message"""
    with get_session() as session:
        analytics = session.query(MessageAnalytics).filter(
            MessageAnalytics.message_id == msg_id
        ).first()
        if analytics:
            analytics.approved_at = datetime.datetime.utcnow()
            if analytics.ai_draft_generated_at:
                delta = analytics.approved_at - analytics.ai_draft_generated_at
                analytics.approval_time_seconds = int(delta.total_seconds())
            session.commit()


def record_sent(msg_id: int, auto: bool = False):
    """Record when message is sent"""
    with get_session() as session:
        analytics = session.query(MessageAnalytics).filter(
            MessageAnalytics.message_id == msg_id
        ).first()
        if analytics:
            analytics.sent_at = datetime.datetime.utcnow()
            analytics.auto_sent = 1 if auto else 0
            if analytics.ai_draft_generated_at:
                delta = analytics.sent_at - analytics.ai_draft_generated_at
                analytics.total_time_seconds = int(delta.total_seconds())
            session.commit()


def get_analytics_summary(days: int = 7):
    """Get analytics for last N days"""
    with get_session() as session:
        since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        analytics = session.query(MessageAnalytics).filter(
            MessageAnalytics.created_at >= since
        ).all()
        
        if not analytics:
            return {
                "period_days": days,
                "total_messages": 0,
                "auto_sent_count": 0,
                "manual_sent_count": 0,
                "avg_approval_time_seconds": 0,
                "avg_total_time_seconds": 0,
                "by_channel": {},
            }
        
        total = len(analytics)
        auto_count = sum(1 for a in analytics if a.auto_sent)
        manual_count = sum(1 for a in analytics if not a.auto_sent)
        
        approval_times = [a.approval_time_seconds for a in analytics if a.approval_time_seconds]
        total_times = [a.total_time_seconds for a in analytics if a.total_time_seconds]
        
        by_channel = {}
        for channel in ["email", "sms"]:
            channel_analytics = [a for a in analytics if a.channel == channel]
            by_channel[channel] = {
                "count": len(channel_analytics),
                "auto_sent": sum(1 for a in channel_analytics if a.auto_sent),
            }
        
        return {
            "period_days": days,
            "total_messages": total,
            "auto_sent_count": auto_count,
            "manual_sent_count": manual_count,
            "avg_approval_time_seconds": int(sum(approval_times) / len(approval_times)) if approval_times else 0,
            "avg_total_time_seconds": int(sum(total_times) / len(total_times)) if total_times else 0,
            "by_channel": by_channel,
        }
