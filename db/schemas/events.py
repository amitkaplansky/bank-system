from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal

class CustomerSchema(BaseModel):
    """Customer schema matching JSON format - supports VIP tier for both individual and business"""
    id: int
    name: str
    type: Literal["individual", "business"]
    personal_id: Optional[str] = None
    business_number: Optional[str] = None
    vip_tier: Optional[str] = None

class AccountSchema(BaseModel):
    id: int
    balance_before: Decimal = Field(..., description="Account balance before transaction")
    balance_after: Decimal = Field(..., description="Account balance after transaction")
    customer: CustomerSchema

class TransactionMetadata(BaseModel):
    processed_by: str = Field(default="bank-core-service")
    source: str = Field(default="api/v1/transfer")
    status: Optional[str] = None

class TransactionEvent(BaseModel):
    event_type: Literal["transaction"] = "transaction"
    timestamp: str = Field(..., description="ISO 8601 timestamp with Z suffix")
    transaction_id: int
    from_account: AccountSchema
    to_account: AccountSchema
    amount: Decimal = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field(default="ILS", description="Currency code")
    description: Optional[str] = None
    metadata: TransactionMetadata

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "event_type": "transaction",
                "timestamp": "2025-07-30T13:45:00Z",
                "transaction_id": 98765,
                "from_account": {
                    "id": 1001,
                    "balance_before": 1500.00,
                    "balance_after": 1200.00,
                    "customer": {
                        "id": 501,
                        "name": "David Levi",
                        "type": "individual",
                        "personal_id": "203948293"
                    }
                },
                "to_account": {
                    "id": 2002,
                    "balance_before": 8000.00,
                    "balance_after": 8300.00,
                    "customer": {
                        "id": 502,
                        "name": "TechnoCorp Ltd.",
                        "type": "business",
                        "business_number": "514857392",
                        "vip_tier": "Platinum"
                    }
                },
                "amount": 300.00,
                "currency": "ILS",
                "description": "Monthly service payment",
                "metadata": {
                    "processed_by": "bank-core-service",
                    "source": "api/v1/transfer"
                }
            }
        }

class FailedTransactionEvent(BaseModel):
    event_type: Literal["failed_transaction"] = "failed_transaction"
    timestamp: str
    transaction_id: int
    error_message: str
    retry_count: int
    original_event: TransactionEvent

class CompletedTransactionEvent(TransactionEvent):
    event_type: Literal["completed_transaction"] = "completed_transaction"
    completion_timestamp: str