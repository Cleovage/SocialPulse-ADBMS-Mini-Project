import os

class Settings:
    PROJECT_NAME: str = "SocialPulse Analytics - Social Media Trend & Influencer Analytics Platform"
    PROJECT_SUBTITLE: str = "Advanced Database Management System (ADBMS) Mini Project"
    VERSION: str = "1.0.0"
    
    # MongoDB Settings
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("MONGO_DB_NAME", "socialpulse_analytics_db")
    
    # Server Settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))

settings = Settings()
