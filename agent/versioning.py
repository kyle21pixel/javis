"""
J.A.V.I.S. Version Control for Drafts
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from agent.database import Base


class DraftVersion(Base):
    """
    Audit trail for AI draft changes — allows rollback and history viewing
    """
    __tablename__ = "draft_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)  # 1, 2, 3, ...
    draft_text = Column(Text, nullable=False)
    reason = Column(String, default="")  # "redraft", "edit", "ai_revision"
    created_by = Column(String, default="")  # username who triggered this version
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class MessageAnalytics(Base):
    """
    Message-level metrics for reporting and analytics
    """
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
