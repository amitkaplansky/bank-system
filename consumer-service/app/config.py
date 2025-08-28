import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Consumer service configuration"""
    
    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "mysql+asyncmy://banking_user:banking_pass@mysql:3306/banking_db"
    )
    
    # Kafka configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_GROUP_ID: str = os.getenv("KAFKA_GROUP_ID", "banking-consumer")
    
    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Consumer settings
    CONSUMER_BATCH_SIZE: int = int(os.getenv("CONSUMER_BATCH_SIZE", 10))
    CONSUMER_TIMEOUT_MS: int = int(os.getenv("CONSUMER_TIMEOUT_MS", 10000))
    
    # Retry settings
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", 3))
    RETRY_BACKOFF_MS: int = int(os.getenv("RETRY_BACKOFF_MS", 1000))
    
    PENDING_TRANSACTIONS_TOPIC: str = "pendingTransactions"
    COMPLETED_TRANSACTIONS_TOPIC: str = "completedTransactions"
    FAILED_TRANSACTIONS_TOPIC: str = "failedTransactions"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()