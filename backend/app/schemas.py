from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    analyst: dict[str, str]


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_ref: str
    customer_name: str
    customer_ref: str
    amount: Decimal
    currency: str
    route: str
    transaction_type: str
    risk_score: int
    risk_level: str
    primary_signal: str
    signal_detail: str
    channel: str
    status: str
    occurred_at: datetime


class DecisionRequest(BaseModel):
    decision: Literal["safe", "blocked", "escalated"]
    note: str = Field(min_length=3, max_length=1000)


class ScreenTransactionRequest(BaseModel):
    transaction_ref: str = Field(min_length=4, max_length=40)
    customer_name: str
    customer_ref: str
    source_account_ref: str
    destination_ref: str
    amount: Decimal = Field(gt=0)
    route: str
    transaction_type: str = "Bank transfer"
    channel: str = "NetBanking"
    device_ref: str | None = None
    transactions_last_10m: int = Field(default=1, ge=0)
    pass_through_ratio: float = Field(default=0, ge=0, le=1)
    new_device: bool = False
    distance_km: float = Field(default=0, ge=0)
    minutes_since_last_location: int = Field(default=60, ge=0)
    known_risky_beneficiary: bool = False
    dormant_days: int = Field(default=0, ge=0)
    profile_mismatch: bool = False


class ScreenResult(BaseModel):
    transaction_ref: str
    risk_score: int
    risk_level: str
    signals: list[dict[str, str | int]]
    case_ref: str | None = None
