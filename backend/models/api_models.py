from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
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
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TriggerAnalysisResponse(BaseModel):
    status: str
    message: str
    anomalies_detected: int
    recommendations: Optional[Recommendation] = None
