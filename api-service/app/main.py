from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from contextlib import asynccontextmanager

sys.path.append('/app')
sys.path.append('/app/db')

from .routers import health, customers, accounts, transactions
from .kafka_client import kafka_producer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await kafka_producer.start()
    yield
    # Shutdown
    await kafka_producer.stop()

app = FastAPI(
    title="Banking System API",
    description="Digital Banking System supporting Individual, Business and VIP customers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["customers"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["accounts"])
app.include_router(transactions.router, prefix="/api/v1", tags=["transactions"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Banking System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)