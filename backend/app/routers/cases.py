from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import AuditEvent, Case, CaseDecision, Transaction, User
from ..schemas import DecisionRequest
from ..services.integrations import integrations

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/{case_ref}/decisions", status_code=201)
def record_decision(
    case_ref: str,
    payload: DecisionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    case = db.scalar(select(Case).where(Case.case_ref == case_ref))
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    transaction = db.scalar(select(Transaction).where(Transaction.transaction_ref == case.transaction_ref))
    case.status = "closed_safe" if payload.decision == "safe" else "escalated"
    if transaction:
        transaction.status = "cleared" if payload.decision == "safe" else "blocked"
    decision = CaseDecision(case_id=case.id, analyst_id=user.id, decision=payload.decision, note=payload.note)
    audit = AuditEvent(actor=user.full_name, action=payload.decision, entity_type="case", entity_ref=case_ref, detail=payload.note)
    db.add_all([decision, audit])
    db.commit()
    integrations.publish("northstar.case-events", {"event_type": "case.decision_recorded", "case_ref": case_ref, "decision": payload.decision, "analyst": user.email})
    integrations.invalidate("dashboard:summary", "audit:recent")
    return {"case_ref": case_ref, "decision": payload.decision, "status": case.status, "audit_event_recorded": True}


@router.get("/audit/recent")
def recent_audit(
    limit: int = 10,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(min(max(limit, 1), 50))).all()
    return [
        {"actor": event.actor, "action": event.action, "entity_type": event.entity_type, "entity_ref": event.entity_ref, "detail": event.detail, "created_at": event.created_at}
        for event in events
    ]
