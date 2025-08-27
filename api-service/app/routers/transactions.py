from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging

# Add db to path for imports
import sys
sys.path.append('/app/db')

from db.models.transaction import Transaction
from ..database import get_db_session
from ..schemas.transaction_schemas import TransferRequest, TransferResponse, TransactionResponse
from ..services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/transfer", response_model=TransferResponse, status_code=201)
async def transfer_money(
    transfer_request: TransferRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Execute a money transfer between two accounts
    This is the main banking operation
    """
    try:
        # Validate request
        TransactionService.validate_transfer_request(
            transfer_request.from_account_id,
            transfer_request.to_account_id,
            transfer_request.amount
        )
        
        # Execute transfer
        transaction = await TransactionService.execute_transfer(
            session=session,
            from_account_id=transfer_request.from_account_id,
            to_account_id=transfer_request.to_account_id,
            amount=transfer_request.amount,
            description=transfer_request.description,
            currency=transfer_request.currency
        )
        
        logger.info(
            f"Transfer successful: Transaction ID {transaction.transaction_id}"
        )
        
        return TransferResponse(
            transaction_id=transaction.transaction_id,
            from_account_id=transaction.from_account_id,
            to_account_id=transaction.to_account_id,
            amount=transaction.amount,
            currency=transaction.currency,
            description=transaction.description,
            status=transaction.status.value,
            timestamp=transaction.timestamp
        )
        
    except ValueError as e:
        logger.warning(f"Transfer validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Transfer failed: {e}")
        raise HTTPException(status_code=500, detail="Transfer failed")

@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Get details of a specific transaction"""
    try:
        transaction = await TransactionService.get_transaction_by_id(
            session, transaction_id
        )
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return TransactionResponse.from_orm(transaction)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction {transaction_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounts/{account_id}/transactions", response_model=List[TransactionResponse])
async def get_account_transactions(
    account_id: int,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session)
):
    """Get transaction history for a specific account"""
    try:
        transactions = await TransactionService.get_transaction_history(
            session, account_id, skip, limit
        )
        
        return [TransactionResponse.from_orm(tx) for tx in transactions]
        
    except Exception as e:
        logger.error(f"Error getting transactions for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_all_transactions(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get all transactions with optional status filtering"""
    try:
        query = select(Transaction).offset(skip).limit(limit).order_by(Transaction.timestamp.desc())
        
        if status:
            # Import here to avoid circular import
            from db.models.transaction import TransactionStatus
            query = query.where(Transaction.status == TransactionStatus(status))
        
        result = await session.execute(query)
        transactions = result.scalars().all()
        
        return [TransactionResponse.from_orm(tx) for tx in transactions]
        
    except Exception as e:
        logger.error(f"Error getting all transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
