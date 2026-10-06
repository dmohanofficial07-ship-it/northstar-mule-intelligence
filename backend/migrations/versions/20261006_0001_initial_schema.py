"""Create the Northstar operational schema.

Revision ID: 20261006_0001
Revises:
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20261006_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_ref", sa.String(40), nullable=False),
        sa.Column("customer_name", sa.String(120), nullable=False),
        sa.Column("customer_ref", sa.String(40), nullable=False),
        sa.Column("source_account_ref", sa.String(40), nullable=False),
        sa.Column("destination_ref", sa.String(40), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("route", sa.String(160), nullable=False),
        sa.Column("transaction_type", sa.String(80), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("primary_signal", sa.String(100), nullable=False),
        sa.Column("signal_detail", sa.String(180), nullable=False),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("device_ref", sa.String(40), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("transaction_ref"),
    )
    for name in ("transaction_ref", "customer_name", "customer_ref", "source_account_ref", "destination_ref", "risk_score", "risk_level"):
        op.create_index(f"ix_transactions_{name}", "transactions", [name])

    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_ref", sa.String(40), nullable=False),
        sa.Column("transaction_ref", sa.String(40), sa.ForeignKey("transactions.transaction_ref"), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("assigned_to", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_ref"),
    )
    op.create_index("ix_cases_case_ref", "cases", ["case_ref"], unique=True)
    op.create_index("ix_cases_transaction_ref", "cases", ["transaction_ref"])
    op.create_index("ix_cases_status", "cases", ["status"])

    op.create_table(
        "case_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("analyst_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", sa.String(30), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_case_decisions_case_id", "case_decisions", ["case_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_ref", sa.String(40), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_entity_ref", "audit_events", ["entity_ref"])

    op.create_table(
        "daily_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("metric_date", sa.String(10), nullable=False),
        sa.Column("accounts_analyzed", sa.Integer(), nullable=False),
        sa.Column("suspected_mules", sa.Integer(), nullable=False),
        sa.Column("suspicious_funds", sa.Numeric(14, 2), nullable=False),
        sa.Column("average_investigation_seconds", sa.Integer(), nullable=False),
        sa.Column("low_risk", sa.Integer(), nullable=False),
        sa.Column("medium_risk", sa.Integer(), nullable=False),
        sa.Column("high_risk", sa.Integer(), nullable=False),
        sa.UniqueConstraint("metric_date"),
    )

    op.create_table(
        "event_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("topic", sa.String(120), nullable=False),
        sa.Column("partition", sa.Integer(), nullable=False),
        sa.Column("offset", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("entity_ref", sa.String(80), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("topic", "partition", "offset", name="uq_event_position"),
    )
    op.create_index("ix_event_receipts_topic", "event_receipts", ["topic"])
    op.create_index("ix_event_receipts_event_type", "event_receipts", ["event_type"])
    op.create_index("ix_event_receipts_entity_ref", "event_receipts", ["entity_ref"])


def downgrade() -> None:
    op.drop_index("ix_event_receipts_entity_ref", table_name="event_receipts")
    op.drop_index("ix_event_receipts_event_type", table_name="event_receipts")
    op.drop_index("ix_event_receipts_topic", table_name="event_receipts")
    op.drop_table("event_receipts")
    op.drop_table("daily_metrics")
    op.drop_index("ix_audit_events_entity_ref", table_name="audit_events")
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_case_decisions_case_id", table_name="case_decisions")
    op.drop_table("case_decisions")
    op.drop_index("ix_cases_status", table_name="cases")
    op.drop_index("ix_cases_transaction_ref", table_name="cases")
    op.drop_index("ix_cases_case_ref", table_name="cases")
    op.drop_table("cases")
    for name in reversed(("transaction_ref", "customer_name", "customer_ref", "source_account_ref", "destination_ref", "risk_score", "risk_level")):
        op.drop_index(f"ix_transactions_{name}", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
