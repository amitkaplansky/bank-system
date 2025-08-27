import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "mysql+asyncmy://banking_user:banking_pass@mysql:3306/banking_db"
    )
    
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", 20))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", 0))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", 3600))
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()