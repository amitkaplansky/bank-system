from sqlalchemy import Column, String, Integer, DECIMAL, Enum, ForeignKey, BigInteger, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import BaseModel

class TransactionStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Transaction(BaseModel):

    __tablename__ = "transactions"
    
    transaction_id = Column(BigInteger, nullable=False, unique=True)
    
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    from_balance_before = Column(DECIMAL(15, 2), nullable=False)
    from_balance_after = Column(DECIMAL(15, 2), nullable=False)
    to_balance_before = Column(DECIMAL(15, 2), nullable=False)
    to_balance_after = Column(DECIMAL(15, 2), nullable=False)
    
    amount = Column(DECIMAL(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="ILS")
    description = Column(Text, nullable=True)
    
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    processed_by = Column(String(100), nullable=False, default="bank-core-service")
    source = Column(String(100), nullable=False, default="api/v1/transfer")
    
    timestamp = Column(DateTime, nullable=False, default=func.now())
    
    from_account = relationship("Account", foreign_keys=[from_account_id], back_populates="outgoing_transactions")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="incoming_transactions")
    
    def to_kafka_event(self):
        """
        Convert transaction to Kafka event format
        """
        return {
            "event_type": "transaction",
            "timestamp": self.timestamp.isoformat() + "Z",
            "transaction_id": self.transaction_id,
            "from_account": {
                "id": self.from_account.id,
                "balance_before": float(self.from_balance_before),
                "balance_after": float(self.from_balance_after),
                "customer": self.from_account.customer.to_dict()
            },
            "to_account": {
                "id": self.to_account.id,
                "balance_before": float(self.to_balance_before),
                "balance_after": float(self.to_balance_after),
                "customer": self.to_account.customer.to_dict()
            },
            "amount": float(self.amount),
            "currency": self.currency,
            "description": self.description,
            "metadata": {
                "processed_by": self.processed_by,
                "source": self.source,
                "status": self.status.value
            }
        }
    
    @property
    def is_completed(self) -> bool:
        return self.status == TransactionStatus.COMPLETED
    
    @property
    def is_pending(self) -> bool:
        return self.status == TransactionStatus.PENDING
    
    @property
    def is_failed(self) -> bool:
        return self.status == TransactionStatus.FAILED
    
    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, amount={self.amount}, status='{self.status.value}')>"