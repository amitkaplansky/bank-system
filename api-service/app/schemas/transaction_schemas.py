from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal

class TransferRequest(BaseModel):
    from_account_id: int = Field(..., gt=0)
    to_account_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="ILS", max_length=3)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return round(v, 2)
    
    @validator('to_account_id')
    def validate_different_accounts(cls, v, values):
        if 'from_account_id' in values and v == values['from_account_id']:
            raise ValueError('Cannot transfer to the same account')
        return v

class TransferResponse(BaseModel):
    transaction_id: int
    from_account_id: int
    to_account_id: int
    amount: Decimal
    currency: str
    description: Optional[str]
    status: str
    timestamp: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class TransactionResponse(BaseModel):
    id: int
    transaction_id: int
    from_account_id: int
    to_account_id: int
    from_balance_before: Decimal
    from_balance_after: Decimal
    to_balance_before: Decimal
    to_balance_after: Decimal
    amount: Decimal
    currency: str
    description: Optional[str]
    status: str
    processed_by: str
    source: str
    timestamp: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }