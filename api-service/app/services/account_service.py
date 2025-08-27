from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from typing import Optional
import logging

import sys
sys.path.append('/app/db')

from db.models.account import Account, AccountStatus
from db.models.customer import Customer

logger = logging.getLogger(__name__)

class AccountService:
    """Service layer for account-related business logic"""
    
    @staticmethod
    async def get_account_by_id(
        session: AsyncSession, 
        account_id: int
    ) -> Optional[Account]:
        """Get account by ID with error handling"""
        try:
            result = await session.execute(
                select(Account).where(Account.id == account_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching account {account_id}: {e}")
            raise
    
    @staticmethod
    async def validate_account_for_transfer(
        session: AsyncSession,
        account_id: int,
        required_amount: Optional[Decimal] = None
    ) -> Account:
        """
        Validate account exists, is active, and has sufficient balance
        Returns the account if valid, raises exception otherwise
        """
        account = await AccountService.get_account_by_id(session, account_id)
        
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        if account.status != AccountStatus.ACTIVE:
            raise ValueError(f"Account {account_id} is not active (status: {account.status.value})")
        
        if required_amount and account.balance < required_amount:
            raise ValueError(
                f"Insufficient funds in account {account_id}. "
                f"Balance: {account.balance}, Required: {required_amount}"
            )
        
        return account
    
    @staticmethod
    async def update_account_balance(
        session: AsyncSession,
        account: Account,
        new_balance: Decimal
    ) -> Account:
        """Update account balance with validation"""
        if new_balance < 0:
            raise ValueError("Account balance cannot be negative")
        
        account.balance = new_balance
        await session.flush()
        return account
    
    @staticmethod
    async def check_daily_transfer_limits(
        session: AsyncSession,
        account: Account,
        amount: Decimal
    ) -> bool:
        """
        Check if transfer amount exceeds daily limits
        This is a placeholder for future implementation
        """
        if account.account_type.value == "vip":
            daily_limit = Decimal("1000000.00")  # 1M for VIP
        elif account.account_type.value == "business":
            daily_limit = Decimal("500000.00")   # 500K for business
        else:
            daily_limit = Decimal("100000.00")   # 100K for regular accounts
        
        if amount > daily_limit:
            raise ValueError(
                f"Transfer amount {amount} exceeds daily limit {daily_limit} "
                f"for account type {account.account_type.value}"
            )
        
        return True
    
    @staticmethod
    async def generate_account_number(session: AsyncSession) -> str:
        """Generate a unique account number"""
        import random
        import string
        
        while True:
            # Generate format: ACC-NNNN (where NNNN is 4 digits)
            number = f"ACC-{''.join(random.choices(string.digits, k=4))}"
            
            # Check if already exists
            result = await session.execute(
                select(Account).where(Account.account_number == number)
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                return number