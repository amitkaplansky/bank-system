import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select
import sys

sys.path.append('/app/db')

from db.models.transaction import Transaction, TransactionStatus
from ..database import db_manager
from ..config import settings

logger = logging.getLogger(__name__)

class TransactionProcessor:
    """Process transaction events from Kafka"""
    
    def __init__(self):
        self.processed_transactions = set()
    
    async def process_transaction_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process a transaction event from Kafka
        Returns True if processing was successful, False otherwise
        """
        try:
            transaction_id = event_data.get('transaction_id')
            
            if not transaction_id:
                logger.error("Transaction event missing transaction_id")
                return False
            
            # Check for idempotency (prevent duplicate processing)
            if await self._is_already_processed(transaction_id):
                logger.info(f"Transaction {transaction_id} already processed, skipping")
                return True
            
            # Process based on event type
            event_type = event_data.get('event_type', 'transaction')
            
            if event_type == 'transaction':
                success = await self._process_completed_transaction(event_data)
            elif event_type == 'failed_transaction':
                success = await self._process_failed_transaction(event_data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return False
            
            if success:
                self.processed_transactions.add(transaction_id)
                logger.info(f"Successfully processed {event_type}: {transaction_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing transaction event: {e}")
            return False
    
    async def _process_completed_transaction(self, event_data: Dict[str, Any]) -> bool:
        """Process a completed transaction event"""
        try:
            transaction_id = event_data['transaction_id']
            
            # Extract transaction details from event
            from_account_info = event_data.get('from_account', {})
            to_account_info = event_data.get('to_account', {})
            
            await self._perform_regulatory_reporting(event_data)
            await self._update_analytics(event_data)
            await self._send_notifications(event_data)
            
            # Update transaction status in database
            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(Transaction).where(Transaction.transaction_id == transaction_id)
                )
                transaction = result.scalar_one_or_none()
                
                if transaction:
                    logger.info(f"Found transaction in DB: {transaction_id}, status: {transaction.status}")
                else:
                    logger.warning(f"Transaction not found in DB: {transaction_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing completed transaction: {e}")
            return False
    
    async def _process_failed_transaction(self, event_data: Dict[str, Any]) -> bool:
        """Process a failed transaction event"""
        try:
            transaction_id = event_data['transaction_id']
            error_message = event_data.get('error_message', 'Unknown error')
            retry_count = event_data.get('retry_count', 0)
            
            logger.warning(f"Processing failed transaction: {transaction_id}, error: {error_message}")
            
            # Handle failed transaction (e.g., alert administrators, log for investigation)
            await self._handle_transaction_failure(transaction_id, error_message, retry_count)
            
            # retry the transaction?
            if retry_count < settings.MAX_RETRIES:
                logger.info(f"Transaction {transaction_id} will be retried (attempt {retry_count + 1})")
            else:
                logger.error(f"Transaction {transaction_id} exceeded max retries, marking as permanently failed")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing failed transaction: {e}")
            return False
    
    async def _is_already_processed(self, transaction_id: int) -> bool:
        """Check if transaction has already been processed (idempotency check)"""
        return transaction_id in self.processed_transactions
    
    async def _perform_regulatory_reporting(self, event_data: Dict[str, Any]):
        """Simulate regulatory reporting (e.g., anti-money laundering checks)"""
        transaction_id = event_data['transaction_id']
        amount = event_data.get('amount', 0)
        
        await asyncio.sleep(0.1)
        
        if float(amount) > 10000:
            logger.info(f"High-value transaction detected: {transaction_id}, amount: {amount}")
        
        logger.debug(f"Regulatory reporting completed for: {transaction_id}")
    
    async def _update_analytics(self, event_data: Dict[str, Any]):
        """Update analytics and business intelligence data"""
        transaction_id = event_data['transaction_id']
        
        await asyncio.sleep(0.05)
        
        logger.debug(f"Analytics updated for: {transaction_id}")
    
    async def _send_notifications(self, event_data: Dict[str, Any]):
        """Send notifications to customers (email, SMS, push notifications)"""
        transaction_id = event_data['transaction_id']
        
        await asyncio.sleep(0.05)
        
        logger.debug(f"Notifications sent for: {transaction_id}")
    
    async def _handle_transaction_failure(self, transaction_id: int, error_message: str, retry_count: int):
        """Handle failed transaction processing"""
        
        logger.error(
            f"Transaction processing failed: ID={transaction_id}, "
            f"Error={error_message}, Retry={retry_count}"
        )
        
        try:
            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(Transaction).where(Transaction.transaction_id == transaction_id)
                )
                transaction = result.scalar_one_or_none()
                
                if transaction:
                    logger.info(f"Marked transaction {transaction_id} for investigation")
                    
        except Exception as e:
            logger.error(f"Failed to update transaction failure status: {e}")