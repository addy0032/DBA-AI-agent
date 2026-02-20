from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config.settings import settings
from api.routes import router
from data_collection.poller import collector
from utils.logger import setup_logger

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SQL DBA AI Agent API...")
    collector.start()
    yield
    # Shutdown
    logger.info("Shutting down SQL DBA AI Agent API...")
    collector.stop()

app = FastAPI(
    title="SQL Server DBA AI Agent",
    description="Real-Time AI-Powered DBA monitoring and anomaly resolution.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = [origin.strip() for origin in settings.ALLOWED_CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, tags=["DBA Agent"])
