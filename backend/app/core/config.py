"""
Mora Backend - Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    PUBLIC_URL: Optional[str] = None  # Public URL for webhooks (e.g., ngrok URL)
    USE_DEMO_TWIML: bool = False  # Fallback to demo TwiML if no public URL
    
    # Database
    DATABASE_URL: str
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    # LiveKit
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    
    # Deepgram (Speech-to-Text)
    DEEPGRAM_API_KEY: Optional[str] = None
    
    # ElevenLabs (Text-to-Speech)
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVEN_API_KEY: Optional[str] = None  # Alternative name used by livekit
    
    # LLM
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None  # Alternative name for Gemini
    LLM_PROVIDER: str = "openai"  # or "gemini"
    
    # Storage
    STORAGE_MODE: str = "local"  # or "s3"
    LOCAL_STORAGE_PATH: str = "./storage"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
