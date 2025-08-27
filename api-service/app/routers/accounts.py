from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List
import logging

# Add db to path for imports
import sys
sys.path.append('/app/db')

from db.models.account import Account, AccountType, AccountStatus
from db.models.customer import Customer
from ..database import get_db_session
from ..schemas.account_schemas import AccountCreate, AccountUpdate, AccountResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=AccountResponse, status_code=201)
async def create_account(
    account_data: AccountCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new account for a customer"""
    try:
        # Verify customer exists
        result = await session.execute(
            select(Customer).where(Customer.id == account_data.customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Create account instance
        account = Account(
            customer_id=account_data.customer_id,
            account_number=account_data.account_number,
            account_type=AccountType(account_data.account_type),
            balance=account_data.balance,
            currency=account_data.currency,
            status=AccountStatus.ACTIVE
        )
        
        session.add(account)
        await session.commit()
        await session.refresh(account)
        
        logger.info(f"Created account: {account.id} ({account.account_number})")
        return AccountResponse.from_orm(account)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating account: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[AccountResponse])
async def get_accounts(
    skip: int = 0,
    limit: int = 100,
    customer_id: int = None,
    status: str = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get all accounts with optional filtering"""
    try:
        query = select(Account).offset(skip).limit(limit)
        
        if customer_id:
            query = query.where(Account.customer_id == customer_id)
            
        if status:
            query = query.where(Account.status == AccountStatus(status))
            
        result = await session.execute(query)
        accounts = result.scalars().all()
        
        return [AccountResponse.from_orm(account) for account in accounts]
        
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Get a specific account by ID"""
    try:
        result = await session.execute(
            select(Account).where(Account.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
            
        return AccountResponse.from_orm(account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer/{customer_id}", response_model=List[AccountResponse])
async def get_customer_accounts(
    customer_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Get all accounts for a specific customer"""
    try:
        # Verify customer exists
        customer_result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Get customer accounts
        result = await session.execute(
            select(Account).where(Account.customer_id == customer_id)
        )
        accounts = result.scalars().all()
        
        return [AccountResponse.from_orm(account) for account in accounts]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting accounts for customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    session: AsyncSession = Depends(get_db_session)
):
    """Update an account (mainly status changes)"""
    try:
        result = await session.execute(
            select(Account).where(Account.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Update only provided fields
        for field, value in account_data.dict(exclude_unset=True).items():
            if field == "status":
                setattr(account, field, AccountStatus(value))
            else:
                setattr(account, field, value)
        
        await session.commit()
        await session.refresh(account)
        
        logger.info(f"Updated account: {account_id}")
        return AccountResponse.from_orm(account)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating account {account_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Delete an account (soft delete by setting status to closed)"""
    try:
        result = await session.execute(
            select(Account).where(Account.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Check if account has balance
        if account.balance > 0:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete account with positive balance"
            )
        
        # Soft delete by setting status to closed
        account.status = AccountStatus.CLOSED
        await session.commit()
        
        logger.info(f"Closed account: {account_id}")
        return {"message": f"Account {account_id} closed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error closing account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
