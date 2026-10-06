import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import EventReceipt, User

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/recent")
def recent_events(
    limit: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    receipts = db.scalars(select(EventReceipt).order_by(EventReceipt.received_at.desc()).limit(limit)).all()
    return [
        {
            "topic": receipt.topic,
            "event_type": receipt.event_type,
            "entity_ref": receipt.entity_ref,
            "payload": json.loads(receipt.payload),
            "received_at": receipt.received_at,
        }
        for receipt in receipts
    ]
