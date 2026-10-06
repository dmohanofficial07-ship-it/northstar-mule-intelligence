from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import AuditEvent, Case, Transaction, User
from ..schemas import ScreenResult, ScreenTransactionRequest, TransactionResponse
from ..services.integrations import integrations
from ..services.risk_engine import evaluate_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    risk_level: str | None = Query(default=None, pattern="^(critical|high|medium|low)$"),
    q: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=50, ge=1, le=200),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Transaction]:
    statement = select(Transaction).where(Transaction.risk_score >= 50).order_by(Transaction.risk_score.desc(), Transaction.occurred_at.desc())
    if risk_level:
        statement = statement.where(Transaction.risk_level == risk_level)
    if q:
        term = f"%{q.strip()}%"
        statement = statement.where(or_(Transaction.transaction_ref.ilike(term), Transaction.customer_name.ilike(term), Transaction.customer_ref.ilike(term)))
    return list(db.scalars(statement.limit(limit)).all())


@router.post("/screen", response_model=ScreenResult, status_code=status.HTTP_201_CREATED)
def screen_transaction(
    payload: ScreenTransactionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScreenResult:
    if db.scalar(select(Transaction.id).where(Transaction.transaction_ref == payload.transaction_ref)):
        raise HTTPException(status_code=409, detail="Transaction reference already exists")
    ten_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
    observed_velocity = db.scalar(
        select(func.count()).select_from(Transaction).where(
            Transaction.customer_ref == payload.customer_ref,
            Transaction.occurred_at >= ten_minutes_ago,
        )
    ) or 0
    known_device = True
    if payload.device_ref:
        known_device = bool(db.scalar(select(Transaction.id).where(
            Transaction.customer_ref == payload.customer_ref,
            Transaction.device_ref == payload.device_ref,
        ).limit(1)))
    risky_beneficiary = bool(db.scalar(select(Transaction.id).where(
        Transaction.destination_ref == payload.destination_ref,
        Transaction.risk_score >= 75,
    ).limit(1)))
    derived_payload = payload.model_copy(update={
        "transactions_last_10m": max(payload.transactions_last_10m, observed_velocity + 1),
        "new_device": payload.new_device or (bool(payload.device_ref) and not known_device),
        "known_risky_beneficiary": payload.known_risky_beneficiary or risky_beneficiary,
    })
    score, risk_level, signals = evaluate_transaction(derived_payload)
    primary = max(signals, key=lambda signal: int(signal["points"])) if signals else {"label": "No material anomaly", "explanation": "No configured rule exceeded its threshold"}
    transaction = Transaction(
        transaction_ref=payload.transaction_ref,
        customer_name=payload.customer_name,
        customer_ref=payload.customer_ref,
        source_account_ref=payload.source_account_ref,
        destination_ref=payload.destination_ref,
        amount=payload.amount,
        route=payload.route,
        transaction_type=payload.transaction_type,
        risk_score=score,
        risk_level=risk_level,
        primary_signal=str(primary["label"]),
        signal_detail=str(primary["explanation"]),
        channel=payload.channel,
        device_ref=payload.device_ref,
        status="pending_review" if score >= 50 else "approved",
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(transaction)
    case_ref = None
    if score >= 75:
        case_ref = f"AUTO-{payload.transaction_ref[-12:]}"
        db.add(Case(case_ref=case_ref, transaction_ref=payload.transaction_ref, title=f"Automated review: {primary['label']}", risk_score=score, assigned_to=user.full_name))
    db.add(AuditEvent(actor=user.full_name, action="screened", entity_type="transaction", entity_ref=payload.transaction_ref, detail=f"Risk score {score}; {len(signals)} rule signals."))
    db.commit()
    event = {"event_type": "transaction.screened", "transaction_ref": payload.transaction_ref, "risk_score": score, "risk_level": risk_level, "case_ref": case_ref}
    integrations.publish("northstar.risk-events", event)
    integrations.invalidate("dashboard:summary")
    return ScreenResult(transaction_ref=payload.transaction_ref, risk_score=score, risk_level=risk_level, signals=signals, case_ref=case_ref)
