from sqlalchemy import Column, String, Integer, DECIMAL, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class AccountType(enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"
    VIP = "vip"

class AccountStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    FROZEN = "frozen"
    CLOSED = "closed"

class Account(BaseModel):
    __tablename__ = "accounts"
    
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    account_number = Column(String(50), nullable=False, unique=True)
    account_type = Column(Enum(AccountType), nullable=False, default=AccountType.CHECKING)
    balance = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="ILS")
    status = Column(Enum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE)
    
    customer = relationship("Customer", back_populates="accounts")
    
    outgoing_transactions = relationship(
        "Transaction", 
        foreign_keys="Transaction.from_account_id",
        back_populates="from_account"
    )
    
    incoming_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.to_account_id", 
        back_populates="to_account"
    )
    
    @property
    def is_active(self) -> bool:
        return self.status == AccountStatus.ACTIVE
    
    def can_transfer(self, amount: float) -> bool:
        """Check if account can transfer the specified amount"""
        return (
            self.is_active and 
            float(self.balance) >= amount and
            amount > 0
        )
    
    def to_dict_with_customer(self):
        """Convert to dict format matching JSON schema with customer info"""
        return {
            "id": self.id,
            "account_number": self.account_number,
            "balance_before": float(self.balance),
            "balance_after": float(self.balance),
            "customer": self.customer.to_dict() if self.customer else None
        }
    
    def __repr__(self):
        return f"<Account(id={self.id}, number='{self.account_number}', balance={self.balance})>"