from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Case, DailyMetric, User
from ..services.integrations import integrations

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    cached = integrations.get_cached("dashboard:summary")
    if cached:
        return cached
    metric = db.scalar(select(DailyMetric).order_by(DailyMetric.id.desc()).limit(1))
    open_cases = db.scalar(select(func.count()).select_from(Case).where(Case.status == "open")) or 0
    result = {
        "accounts_analyzed": metric.accounts_analyzed,
        "suspected_mules": metric.suspected_mules,
        "suspicious_funds": float(metric.suspicious_funds),
        "average_investigation_seconds": metric.average_investigation_seconds,
        "risk_distribution": {"low": metric.low_risk, "medium": metric.medium_risk, "high": metric.high_risk},
        "open_cases": open_cases,
        "model_health": {"precision": 97.2, "recall": 93.8, "false_positive_rate": 1.8, "status": "healthy"},
    }
    integrations.set_cached("dashboard:summary", result)
    return result
