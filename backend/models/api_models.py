from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from models.db_models import MetricSnapshot, Anomaly, SeverityLevel

class RecommendationAction(BaseModel):
    action_type: str
    description: str
    sql_statement: Optional[str] = None

class Recommendation(BaseModel):
    issue_summary: str
    technical_diagnosis: str
    recommended_actions: List[RecommendationAction]
    risk_level: str
    confidence_score: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TriggerAnalysisResponse(BaseModel):
    status: str
    message: str
    anomalies_detected: int
    recommendations: Optional[Recommendation] = None

class ChatRequest(BaseModel):
    user_message: str
    session_id: str = "default_session"

class ChatResponse(BaseModel):
    generated_sql: Optional[str] = None
    explanation: str
    confidence: float = 0.0
    execution_time_ms: float = 0.0
    query_results_preview: List[Dict[str, Any]] = []
    error_message: Optional[str] = None
    suggested_chart_type: Optional[str] = None
