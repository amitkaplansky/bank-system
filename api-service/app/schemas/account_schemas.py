from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal

class AccountBase(BaseModel):
    account_number: str = Field(..., min_length=5, max_length=50)
    account_type: Literal["checking", "savings", "business", "vip"] = "checking"
    currency: str = Field(default="ILS", max_length=3)

class AccountCreate(AccountBase):
    customer_id: int
    balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    
    @validator('balance')
    def validate_balance(cls, v):
        if v < 0:
            raise ValueError('Balance cannot be negative')
        return round(v, 2)

class AccountUpdate(BaseModel):
    status: Optional[Literal["active", "inactive", "frozen", "closed"]] = None

class AccountResponse(AccountBase):
    id: int
    customer_id: int
    balance: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }