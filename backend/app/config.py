from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "NetPulse Incident Triage & RCA Platform"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "netpulse")
    
    # AI & Embeddings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
    EMBEDDING_DIMENSIONS: int = 768
    SYNTHESIS_MODEL: str = os.getenv("SYNTHESIS_MODEL", "gemini-2.5-flash")
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
