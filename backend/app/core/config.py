"""
Application configuration using Pydantic Settings
Loads environment variables with sensible defaults
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # API Keys
    gemini_api_key: Optional[str] = None
    google_tts_key: Optional[str] = None
    google_tts_service_account_path: Optional[str] = None
    
    # Server Configuration
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    
    # Application Settings
    app_name: str = "Qrow IQ"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # WebSocket Settings
    websocket_ping_interval: int = 20
    websocket_ping_timeout: int = 10
    
    # Interview Settings
    max_questions: int = 10
    silence_threshold_seconds: float = 2.0
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Global settings instance
settings = Settings()
