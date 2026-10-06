from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AuditEvent, Case, DailyMetric, Transaction, User
from .security import hash_password


GRAPH_NODES = [
    {"id": "CUS-18429", "type": "Account", "name": "Rohan Khanna", "label": "Rohan K.", "role": "Origin", "score": 94, "summary": "Origin account. Twelve outward transfers followed three recent cash deposits.", "signal": "Velocity spike", "value": "₹2.48L", "position": "a"},
    {"id": "CUS-73108", "type": "Account", "name": "Kavya Rao", "label": "Kavya R.", "role": "Layer 1", "score": 81, "summary": "Newly active account that forwarded 96 percent of received funds.", "signal": "Rapid pass-through", "value": "₹1.76L", "position": "b"},
    {"id": "DEV-9A71", "type": "Device", "name": "Android device", "label": "DEV-9A71", "role": "Shared device", "score": 88, "summary": "Shared device used by three customer profiles in the same hour.", "signal": "Shared device", "value": "3 accounts", "position": "c"},
    {"id": "ACC-33018", "type": "Account", "name": "Aarav Trading", "label": "Aarav Trading", "role": "Aggregator", "score": 94, "summary": "Central collection account. Funds from six unrelated customers converged here.", "signal": "Many-to-one flow", "value": "₹8.6L", "position": "d"},
    {"id": "ACC-88410", "type": "Account", "name": "Nova Services", "label": "Nova Services", "role": "Layer 2", "score": 79, "summary": "Recently opened business account with no matching invoice history.", "signal": "Profile mismatch", "value": "₹1.12L", "position": "e"},
    {"id": "BEN-00391", "type": "Beneficiary", "name": "Orion Exports", "label": "Orion Exports", "role": "Exit point", "score": 91, "summary": "Final beneficiary linked to two previously closed fraud cases.", "signal": "Known association", "value": "₹5.94L", "position": "f"},
    {"id": "CUS-55193", "type": "Account", "name": "Imran Sheikh", "label": "Imran S.", "role": "Layer 1", "score": 76, "summary": "Dormant account became active and moved funds within four minutes.", "signal": "Dormancy break", "value": "₹94K", "position": "g"},
]

GRAPH_EDGES = [
    {"source": "CUS-18429", "target": "ACC-33018", "type": "TRANSFERRED_TO", "amount": 248000},
    {"source": "CUS-73108", "target": "ACC-33018", "type": "TRANSFERRED_TO", "amount": 176000},
    {"source": "DEV-9A71", "target": "CUS-18429", "type": "ACCESSED", "amount": 0},
    {"source": "ACC-33018", "target": "ACC-88410", "type": "TRANSFERRED_TO", "amount": 112000},
    {"source": "ACC-33018", "target": "BEN-00391", "type": "TRANSFERRED_TO", "amount": 594000},
    {"source": "CUS-55193", "target": "ACC-33018", "type": "TRANSFERRED_TO", "amount": 94000},
    {"source": "DEV-9A71", "target": "ACC-88410", "type": "ACCESSED", "amount": 0},
]


def seed_database(db: Session) -> None:
    if not db.scalar(select(User.id).limit(1)):
        db.add(User(email="analyst@northstarfintech.com", password_hash=hash_password("DemoPass123!"), full_name="Arjun Mehta", role="risk_analyst"))

    if not db.scalar(select(Transaction.id).limit(1)):
        now = datetime.now(timezone.utc)
        rows = [
            ("TXN-829104", "Rohan Khanna", "CUS-18429", "ACC-18429", "BEN-00391", "248000", "Mumbai, IN → Lagos, NG", "International transfer", 94, "critical", "Velocity spike", "12 transfers / 8 min", "NetBanking", "DEV-9A71", 2),
            ("TXN-829087", "Sneha Patel", "CUS-29104", "ACC-29104", "MER-8821", "84500", "Bengaluru, IN", "Card payment", 82, "high", "New device", "First seen 4 min ago", "Card", "DEV-72F2", 8),
            ("TXN-829061", "Arun Verma", "CUS-84012", "ACC-84012", "BEN-6712", "112000", "Delhi, IN → Dubai, AE", "UPI transfer", 78, "high", "Location anomaly", "1,900 km in 22 min", "UPI", "DEV-19Q4", 14),
            ("TXN-829044", "Nisha Fernandes", "CUS-61982", "ACC-61982", "MER-1183", "36200", "Chennai, IN", "Card payment", 64, "medium", "Merchant risk", "Elevated category risk", "Card", "DEV-55B8", 21),
        ]
        for row in rows:
            db.add(Transaction(
                transaction_ref=row[0], customer_name=row[1], customer_ref=row[2], source_account_ref=row[3], destination_ref=row[4],
                amount=Decimal(row[5]), route=row[6], transaction_type=row[7], risk_score=row[8], risk_level=row[9],
                primary_signal=row[10], signal_detail=row[11], channel=row[12], device_ref=row[13], occurred_at=now - timedelta(minutes=row[14]),
            ))
        db.flush()
        db.add_all([
            Case(case_ref="MULE-2048", transaction_ref="TXN-829104", title="Connected mule-account cluster", risk_score=94, assigned_to="Arjun Mehta"),
            Case(case_ref="CASE-829087", transaction_ref="TXN-829087", title="New device review", risk_score=82, assigned_to="Arjun Mehta"),
            Case(case_ref="CASE-829061", transaction_ref="TXN-829061", title="Location anomaly review", risk_score=78, assigned_to="Arjun Mehta"),
            Case(case_ref="CASE-829044", transaction_ref="TXN-829044", title="Merchant risk review", risk_score=64, assigned_to="Arjun Mehta"),
        ])

    if not db.scalar(select(DailyMetric.id).limit(1)):
        db.add(DailyMetric(metric_date=datetime.now(timezone.utc).date().isoformat(), accounts_analyzed=24892, suspected_mules=143, suspicious_funds=Decimal("1280000"), average_investigation_seconds=272, low_risk=22104, medium_risk=2645, high_risk=143))

    if not db.scalar(select(AuditEvent.id).limit(1)):
        db.add_all([
            AuditEvent(actor="Meera S.", action="cleared", entity_type="transaction", entity_ref="TXN-828991", detail="Marked safe; analyst note added."),
            AuditEvent(actor="Vikram R.", action="blocked", entity_type="transaction", entity_ref="TXN-828946", detail="Blocked and escalated to AML."),
        ])
    db.commit()


def seed_graph(driver) -> None:
    if not driver:
        return
    with driver.session() as session:
        for node in GRAPH_NODES:
            session.run("MERGE (n:Entity {id: $id}) SET n += $props", id=node["id"], props=node)
        for edge in GRAPH_EDGES:
            session.run(
                "MATCH (a:Entity {id: $source}), (b:Entity {id: $target}) "
                "MERGE (a)-[r:LINKED_TO {case_ref: 'MULE-2048', kind: $type}]->(b) SET r.amount = $amount",
                **edge,
            )
