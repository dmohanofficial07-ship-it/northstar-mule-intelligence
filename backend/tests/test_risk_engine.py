from decimal import Decimal

from backend.app.schemas import ScreenTransactionRequest
from backend.app.services.risk_engine import classify, evaluate_transaction


def transaction(**overrides) -> ScreenTransactionRequest:
    values = {
        "transaction_ref": "TXN-TEST-001",
        "customer_name": "Test Customer",
        "customer_ref": "CUS-TEST",
        "source_account_ref": "ACC-SOURCE",
        "destination_ref": "BEN-TARGET",
        "amount": Decimal("10000"),
        "route": "Mumbai, IN",
    }
    values.update(overrides)
    return ScreenTransactionRequest(**values)


def test_normal_activity_stays_low_risk() -> None:
    score, level, signals = evaluate_transaction(transaction())
    assert score == 0
    assert level == "low"
    assert signals == []


def test_coordinated_mule_signals_create_critical_score() -> None:
    score, level, signals = evaluate_transaction(transaction(
        amount=Decimal("800000"),
        transactions_last_10m=12,
        pass_through_ratio=0.96,
        new_device=True,
        known_risky_beneficiary=True,
        dormant_days=180,
        profile_mismatch=True,
    ))
    assert score == 100
    assert level == "critical"
    assert {signal["code"] for signal in signals} >= {"VELOCITY_SPIKE", "RAPID_PASS_THROUGH", "KNOWN_ASSOCIATION"}


def test_risk_bands_have_stable_boundaries() -> None:
    assert classify(49) == "low"
    assert classify(50) == "medium"
    assert classify(75) == "high"
    assert classify(90) == "critical"
