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

    # Phase 2: Polling & Baseline
    POLL_INTERVAL_SECONDS: int = 10
    MAX_HISTORY_SNAPSHOTS: int = 100
    BASELINE_WINDOW_SIZE: int = 5
    WAIT_SPIKE_MULTIPLIER: float = 2.0
    QUERY_REGRESSION_MULTIPLIER: float = 1.5

    # Phase 5: Tiered Polling (Enterprise Redesign)
    FAST_POLL_SECONDS: int = 5
    MEDIUM_POLL_SECONDS: int = 30
    SLOW_POLL_SECONDS: int = 300

    # Phase 4: Z-Score & Delta Modeling
    CPU_ZSCORE_THRESHOLD: float = 2.0
    QUERY_REGRESSION_STD_MULTIPLIER: float = 3.0
    WAIT_RATE_THRESHOLD_PER_SEC: float = 100.0  # ms/sec threshold
    WAIT_DOMINANCE_PERCENT_THRESHOLD: float = 50.0 # 50%
    WAIT_SUSTAINED_INTERVALS: int = 3
    
    # Phase 4: Chat Agent System
    CHAT_MAX_CONTEXT_LENGTH: int = 16000
    CHAT_MEMORY_WINDOW: int = 10
    CHAT_MAX_RESULT_ROWS: int = 1000
    CHAT_ALLOWED_OPERATIONS: str = "SELECT"
    CHAT_ENABLE_DML: bool = False
    QUERY_TIMEOUT_SECONDS: int = 15

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
