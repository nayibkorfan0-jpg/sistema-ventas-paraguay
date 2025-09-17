import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "")
    
    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    backend_cors_origins: list = ["*"]
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Email
    mail_username: str = os.getenv("MAIL_USERNAME", "")
    mail_password: str = os.getenv("MAIL_PASSWORD", "")
    mail_from: str = os.getenv("MAIL_FROM", "")
    mail_port: int = int(os.getenv("MAIL_PORT", 587))
    mail_server: str = os.getenv("MAIL_SERVER", "")
    
    class Config:
        case_sensitive = True

settings = Settings()