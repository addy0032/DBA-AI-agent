from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database
    SQL_SERVER: str = r"ADDY\SQLEXPRESS"
    SQL_DATABASE: str = "AdventureWorks2025"
    SQL_USER: str = ""
    SQL_PASSWORD: str = ""
    SQL_DRIVER: str = "ODBC Driver 17 for SQL Server"
    
    # Optional: Windows Authentication (Trusted_Connection)
    SQL_USE_WINDOWS_AUTH: bool = True

    # Polling & Baseline
    POLL_INTERVAL_SECONDS: int = 10
    MAX_HISTORY_SNAPSHOTS: int = 100
    BASELINE_WINDOW_SIZE: int = 5
    WAIT_SPIKE_MULTIPLIER: float = 2.0
    QUERY_REGRESSION_MULTIPLIER: float = 1.5

    # LLM (Groq)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b" # A suitable default 
    
    # API & Agent
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    RECOMMENDATION_HISTORY_LIMIT: int = 50
    ALLOWED_CORS_ORIGINS: str = "http://localhost:3000"
    
    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
