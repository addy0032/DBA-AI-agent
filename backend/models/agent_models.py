from typing import TypedDict, List, Dict, Any, Optional
from models.db_models import MetricSnapshot, Anomaly
from models.api_models import Recommendation

class AgentState(TypedDict):
    """
    Represents the state of the LangGraph agent for SQL DBA.
    """
    # Inputs
    current_snapshot: Optional[MetricSnapshot]
    
    # Processing
    detected_anomalies: List[Anomaly]
    historical_anomalies: List[Anomaly]
    
    # Outputs
    llm_prompt: str
    llm_analysis: str
    current_recommendation: Optional[Recommendation]
    
    # Internal Control
    should_alert: bool
    errors: List[str]
