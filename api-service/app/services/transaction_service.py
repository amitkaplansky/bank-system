from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from datetime import datetime
from typing import Optional
import logging
import random

import sys
sys.path.append('/app/db')

from db.models.transaction import Transaction, TransactionStatus
from db.models.account import Account
from .account_service import AccountService
from ..kafka_client import kafka_producer, KafkaTopics

logger = logging.getLogger(__name__)

class TransactionService:
    """Service layer for transaction-related business logic"""
    
    @staticmethod
    async def execute_transfer(
        session: AsyncSession,
        from_account_id: int,
        to_account_id: int,
        amount: Decimal,
        description: Optional[str] = None,
        currency: str = "ILS"
    ) -> Transaction:
        """
        Execute a money transfer between two accounts
        This is the core banking operation
        """
        try:
            if amount <= 0:
                raise ValueError("Transfer amount must be positive")
            
            if from_account_id == to_account_id:
                raise ValueError("Cannot transfer to the same account")
            
            # Get and validate both accounts
            from_account = await AccountService.validate_account_for_transfer(
                session, from_account_id, amount
            )
            to_account = await AccountService.validate_account_for_transfer(
                session, to_account_id
            )
            
            # Check currency match
            if from_account.currency != currency or to_account.currency != currency:
                raise ValueError("Currency mismatch between accounts and transfer request")
            
            # Check daily limits
            await AccountService.check_daily_transfer_limits(session, from_account, amount)
            
            # Capture balances before transaction
            from_balance_before = from_account.balance
            to_balance_before = to_account.balance
            
            # Calculate new balances
            from_balance_after = from_balance_before - amount
            to_balance_after = to_balance_before + amount
            
            # Generate unique transaction ID
            transaction_id = await TransactionService._generate_transaction_id()
            
            # Create transaction record FIRST (for audit trail)
            transaction = Transaction(
                transaction_id=transaction_id,
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                from_balance_before=from_balance_before,
                from_balance_after=from_balance_after,
                to_balance_before=to_balance_before,
                to_balance_after=to_balance_after,
                amount=amount,
                currency=currency,
                description=description,
                status=TransactionStatus.PENDING,
                timestamp=datetime.utcnow(),
                processed_by="bank-core-service",
                source="api/v1/transfer"
            )
            
            session.add(transaction)
            await session.flush()  # Get the transaction ID
            
            # Update account balances atomically
            await AccountService.update_account_balance(
                session, from_account, from_balance_after
            )
            await AccountService.update_account_balance(
                session, to_account, to_balance_after
            )
            
            # Mark transaction as completed
            transaction.status = TransactionStatus.COMPLETED
            
            # Commit the entire transaction
            await session.commit()
            
            # Send Kafka event AFTER successful DB commit
            try:
                kafka_event = transaction.to_kafka_event()
                await kafka_producer.send_transaction_event(
                    topic=KafkaTopics.COMPLETED_TRANSACTIONS,
                    transaction_data=kafka_event,
                    transaction_id=transaction_id
                )
            except Exception as kafka_error:
                logger.warning(f"Failed to send Kafka event: {kafka_error}")
                # Don't fail the transaction if Kafka fails
            
            logger.info(
                f"Transfer completed: {transaction_id} - "
                f"From {from_account_id} to {to_account_id}, Amount: {amount} {currency}"
            )
            
            return transaction
            
        except Exception as e:
            await session.rollback()
            
            # If we have a transaction record, mark it as failed
            if 'transaction' in locals():
                transaction.status = TransactionStatus.FAILED
                await session.commit()
                
                # Send failed transaction event
                try:
                    failed_event = {
                        "event_type": "failed_transaction",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "transaction_id": transaction.transaction_id,
                        "error_message": str(e),
                        "retry_count": 0,
                        "original_event": transaction.to_kafka_event()
                    }
                    await kafka_producer.send_transaction_event(
                        topic=KafkaTopics.FAILED_TRANSACTIONS,
                        transaction_data=failed_event,
                        transaction_id=transaction.transaction_id
                    )
                except Exception as kafka_error:
                    logger.warning(f"Failed to send failed transaction event: {kafka_error}")
            
            logger.error(f"Transfer failed: {e}")
            raise
    
    @staticmethod
    async def get_transaction_history(
        session: AsyncSession,
        account_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Transaction]:
        """Get transaction history for an account"""
        try:
            result = await session.execute(
                select(Transaction)
                .where(
                    (Transaction.from_account_id == account_id) |
                    (Transaction.to_account_id == account_id)
                )
                .order_by(Transaction.timestamp.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error fetching transaction history for account {account_id}: {e}")
            raise
    
    @staticmethod
    async def get_transaction_by_id(
        session: AsyncSession,
        transaction_id: int
    ) -> Optional[Transaction]:
        """Get specific transaction by transaction_id"""
        try:
            result = await session.execute(
                select(Transaction).where(Transaction.transaction_id == transaction_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error fetching transaction {transaction_id}: {e}")
            raise
    
    @staticmethod
    async def _generate_transaction_id() -> int:
        """Generate a unique transaction ID"""
        # Generate a random transaction ID (in real system, would be sequential or UUID)
        return random.randint(100000, 999999)
    
    @staticmethod
    def validate_transfer_request(
        from_account_id: int,
        to_account_id: int,
        amount: Decimal
    ) -> bool:
        """Validate transfer request parameters"""
        if from_account_id <= 0 or to_account_id <= 0:
            raise ValueError("Account IDs must be positive integers")
        
        if from_account_id == to_account_id:
            raise ValueError("Cannot transfer to the same account")
        
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        
        if amount > Decimal("10000000.00"):  # 10M limit
            raise ValueError("Transfer amount exceeds maximum limit")
        
        return True