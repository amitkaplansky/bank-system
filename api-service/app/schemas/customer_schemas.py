from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime

class CustomerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    customer_type: Literal["individual", "business"]
    personal_id: Optional[str] = None
    business_number: Optional[str] = None
    vip_tier: Optional[str] = None  # Gold, Platinum, Diamond
    
    @validator('personal_id')
    def validate_personal_id(cls, v, values):
        if values.get('customer_type') == 'individual' and not v:
            raise ValueError('personal_id is required for individual customers')
        return v
    
    @validator('business_number')
    def validate_business_number(cls, v, values):
        if values.get('customer_type') == 'business' and not v:
            raise ValueError('business_number is required for business customers')
        return v
    
    @validator('vip_tier')
    def validate_vip_tier(cls, v):
        if v and v not in ['Gold', 'Platinum', 'Diamond']:
            raise ValueError('vip_tier must be Gold, Platinum, or Diamond')
        return v

class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    vip_tier: Optional[str] = None
    
    @validator('vip_tier')
    def validate_vip_tier(cls, v):
        if v and v not in ['Gold', 'Platinum', 'Diamond']:
            raise ValueError('vip_tier must be Gold, Platinum, or Diamond')
        return v

class CustomerResponse(CustomerBase):
    id: int
    customer_type: str
    personal_id: Optional[str] = None
    business_number: Optional[str] = None
    vip_tier: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True