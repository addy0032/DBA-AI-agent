from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config.settings import settings
from api.routes import router as legacy_router
from api import chat_routes
from api.server_routes import router as observability_router
from metrics_engine.engine import metrics_engine
from data_collection.poller import collector
from utils.logger import setup_logger

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Enterprise SQL DBA Observability Platform...")
    metrics_engine.start()  # New tiered polling engine
    collector.start()       # Keep legacy poller for backward compat (anomaly detection)
    yield
    # Shutdown
    logger.info("Shutting down platform...")
    metrics_engine.stop()
    collector.stop()

app = FastAPI(
    title="SQL Server DBA Observability Platform",
    description="Enterprise-grade SQL Server monitoring, observability, and AI analysis.",
    version="2.0.0",
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

# New observability endpoints
app.include_router(observability_router, tags=["Observability"])

# Legacy endpoints (anomalies, recommendations, triggers)
app.include_router(legacy_router, tags=["Legacy Agent"])

# Chat agent
app.include_router(chat_routes.router, prefix="/chat", tags=["Chat"])
