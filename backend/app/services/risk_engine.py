from dataclasses import asdict, dataclass

from ..schemas import ScreenTransactionRequest


@dataclass(frozen=True)
class RiskSignal:
    code: str
    label: str
    points: int
    explanation: str


def classify(score: int) -> str:
    if score >= 90:
        return "critical"
    if score >= 75:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


def evaluate_transaction(payload: ScreenTransactionRequest) -> tuple[int, str, list[dict[str, str | int]]]:
    signals: list[RiskSignal] = []

    if payload.transactions_last_10m >= 10:
        signals.append(RiskSignal("VELOCITY_SPIKE", "Velocity spike", 24, f"{payload.transactions_last_10m} transfers in 10 minutes"))
    elif payload.transactions_last_10m >= 5:
        signals.append(RiskSignal("ELEVATED_VELOCITY", "Elevated velocity", 12, f"{payload.transactions_last_10m} transfers in 10 minutes"))
    if payload.pass_through_ratio >= 0.9:
        signals.append(RiskSignal("RAPID_PASS_THROUGH", "Rapid pass-through", 20, f"{payload.pass_through_ratio:.0%} of received value moved onward"))
    if payload.new_device:
        signals.append(RiskSignal("NEW_DEVICE", "New device", 10, "The device has not been seen on this customer profile"))
    if payload.minutes_since_last_location > 0:
        speed = payload.distance_km / (payload.minutes_since_last_location / 60)
        if payload.distance_km >= 500 and speed > 900:
            signals.append(RiskSignal("IMPOSSIBLE_TRAVEL", "Location anomaly", 18, f"{payload.distance_km:.0f} km in {payload.minutes_since_last_location} minutes"))
    if payload.known_risky_beneficiary:
        signals.append(RiskSignal("KNOWN_ASSOCIATION", "Known risky beneficiary", 25, "Beneficiary is linked to a previous confirmed case"))
    if payload.dormant_days >= 90:
        signals.append(RiskSignal("DORMANCY_BREAK", "Dormancy break", 12, f"Account reactivated after {payload.dormant_days} days"))
    if payload.profile_mismatch:
        signals.append(RiskSignal("PROFILE_MISMATCH", "Profile mismatch", 12, "Activity does not match the customer's expected profile"))
    if payload.amount >= 500_000:
        signals.append(RiskSignal("HIGH_VALUE", "High-value transfer", 8, "Amount exceeds the enhanced-monitoring threshold"))

    score = min(sum(signal.points for signal in signals), 100)
    return score, classify(score), [asdict(signal) for signal in signals]
