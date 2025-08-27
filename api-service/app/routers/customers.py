from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging

import sys
sys.path.append('/app/db')

from db.models.customer import Customer, CustomerType
from ..database import get_db_session
from ..schemas.customer_schemas import CustomerCreate, CustomerUpdate, CustomerResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer_data: CustomerCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new customer (individual, business, or VIP)"""
    try:
        customer = Customer(
            name=customer_data.name,
            customer_type=CustomerType(customer_data.customer_type),
            personal_id=customer_data.personal_id,
            business_number=customer_data.business_number,
            vip_tier=customer_data.vip_tier,
            email=customer_data.email,
            phone=customer_data.phone,
            address=customer_data.address
        )
        
        session.add(customer)
        await session.commit()
        await session.refresh(customer)
        
        logger.info(f"Created customer: {customer.id} ({customer.name})")
        return CustomerResponse.from_orm(customer)
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = 0,
    limit: int = 100,
    customer_type: str = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get all customers with optional filtering"""
    try:
        query = select(Customer).offset(skip).limit(limit)
        
        if customer_type:
            query = query.where(Customer.customer_type == CustomerType(customer_type))
            
        result = await session.execute(query)
        customers = result.scalars().all()
        
        return [CustomerResponse.from_orm(customer) for customer in customers]
        
    except Exception as e:
        logger.error(f"Error getting customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Get a specific customer by ID"""
    try:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
            
        return CustomerResponse.from_orm(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    session: AsyncSession = Depends(get_db_session)
):
    """Update a customer's information"""
    try:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Update only provided fields
        for field, value in customer_data.dict(exclude_unset=True).items():
            setattr(customer, field, value)
        
        await session.commit()
        await session.refresh(customer)
        
        logger.info(f"Updated customer: {customer_id}")
        return CustomerResponse.from_orm(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating customer {customer_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Delete a customer"""
    try:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        await session.delete(customer)
        await session.commit()
        
        logger.info(f"Deleted customer: {customer_id}")
        return {"message": f"Customer {customer_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))