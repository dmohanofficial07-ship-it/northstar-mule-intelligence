from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(40), default="risk_analyst")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_ref: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(120), index=True)
    customer_ref: Mapped[str] = mapped_column(String(40), index=True)
    source_account_ref: Mapped[str] = mapped_column(String(40), index=True)
    destination_ref: Mapped[str] = mapped_column(String(40), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    route: Mapped[str] = mapped_column(String(160))
    transaction_type: Mapped[str] = mapped_column(String(80))
    risk_score: Mapped[int] = mapped_column(Integer, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), index=True)
    primary_signal: Mapped[str] = mapped_column(String(100))
    signal_detail: Mapped[str] = mapped_column(String(180))
    channel: Mapped[str] = mapped_column(String(40))
    device_ref: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending_review")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_ref: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    transaction_ref: Mapped[str] = mapped_column(String(40), ForeignKey("transactions.transaction_ref"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    risk_score: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    assigned_to: Mapped[str] = mapped_column(String(120), default="Unassigned")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    decisions: Mapped[list["CaseDecision"]] = relationship(back_populates="case")


class CaseDecision(Base):
    __tablename__ = "case_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    analyst_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    case: Mapped[Case] = relationship(back_populates="decisions")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_ref: Mapped[str] = mapped_column(String(40), index=True)
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_date: Mapped[str] = mapped_column(String(10), unique=True)
    accounts_analyzed: Mapped[int] = mapped_column(Integer)
    suspected_mules: Mapped[int] = mapped_column(Integer)
    suspicious_funds: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    average_investigation_seconds: Mapped[int] = mapped_column(Integer)
    low_risk: Mapped[int] = mapped_column(Integer)
    medium_risk: Mapped[int] = mapped_column(Integer)
    high_risk: Mapped[int] = mapped_column(Integer)


class EventReceipt(Base):
    __tablename__ = "event_receipts"
    __table_args__ = (UniqueConstraint("topic", "partition", "offset", name="uq_event_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(120), index=True)
    partition: Mapped[int] = mapped_column(Integer)
    offset: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    entity_ref: Mapped[str] = mapped_column(String(80), index=True)
    payload: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
