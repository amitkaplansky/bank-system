from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class CustomerType(enum.Enum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"

class Customer(BaseModel):
    """
    Customer model supporting Individual and Business customers.
    Both types can have VIP tier (Gold, Platinum, Diamond).
    """
    __tablename__ = "customers"
    
    name = Column(String(255), nullable=False)
    customer_type = Column(Enum(CustomerType), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(500), nullable=True)
    
    personal_id = Column(String(20), nullable=True, unique=True)
    
    business_number = Column(String(20), nullable=True, unique=True)
    
    vip_tier = Column(String(50), nullable=True)  # Gold, Platinum, Diamond
    
    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    
    @property
    def is_individual(self) -> bool:
        return self.customer_type == CustomerType.INDIVIDUAL
    
    @property
    def is_business(self) -> bool:
        return self.customer_type == CustomerType.BUSINESS
    
    @property
    def is_vip(self) -> bool:
        return self.vip_tier is not None
    
    def to_dict(self):
        base_dict = super().to_dict()
        
        base_dict['type'] = self.customer_type.value
        
        # Add type-specific fields
        if self.is_individual:
            base_dict['personal_id'] = self.personal_id
        
        if self.is_business:
            base_dict['business_number'] = self.business_number
            
        if self.is_vip:
            base_dict['vip_tier'] = self.vip_tier
            
        return base_dict
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', type='{self.customer_type.value}')>"