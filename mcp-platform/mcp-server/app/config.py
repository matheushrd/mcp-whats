from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application settings
    CLIENT_NAME: str
    ENVIRONMENT: str = "development"
    
    # Database settings
    DATABASE_HOST: str
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    
    # Google Calendar settings
    GOOGLE_CALENDAR_API_KEY: Optional[str] = None
    GOOGLE_CALENDAR_ID: str
    GOOGLE_PROJECT_ID: str
    GOOGLE_PRIVATE_KEY: str
    GOOGLE_CLIENT_EMAIL: str
    
    # Gemini API settings
    GEMINI_API_KEY: str
    
    # WhatsApp Business API settings
    WHATSAPP_API_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "mcp_webhook_verify_token"
    
    # Redis settings
    REDIS_HOST: str = "redis-service"
    REDIS_PORT: int = 6379
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()