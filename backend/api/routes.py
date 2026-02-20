from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from models.db_models import MetricSnapshot, Anomaly
from models.api_models import Recommendation, TriggerAnalysisResponse
from data_collection.snapshot import snapshot_manager
from data_collection.poller import collector
from agent.graph import dba_agent
from agent.memory import anomaly_memory
from agent.recommendations import recommendation_manager

router = APIRouter()

@router.get("/metrics/current", response_model=MetricSnapshot)
async def get_current_metrics():
    snapshot = snapshot_manager.get_latest()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No metric snapshots available yet.")
    return snapshot

@router.get("/metrics/history", response_model=List[MetricSnapshot])
async def get_metrics_history(count: int = 10):
    return snapshot_manager.get_history(count)

@router.get("/anomalies", response_model=List[Anomaly])
async def get_active_anomalies():
    snapshot = snapshot_manager.get_latest()
    if not snapshot:
        return []
    from anomaly_detection.detector import detector
    from config.settings import settings
    history = snapshot_manager.get_history(settings.BASELINE_WINDOW_SIZE)
    return detector.detect(snapshot, history)

@router.get("/recommendations", response_model=Optional[Recommendation])
async def get_latest_recommendation():
    return recommendation_manager.get_latest()

@router.get("/recommendations/history", response_model=List[Recommendation])
async def get_recommendation_history(limit: int = 10):
    return recommendation_manager.get_history(limit)

@router.post("/trigger-analysis", response_model=TriggerAnalysisResponse)
async def trigger_analysis():
    
    initial_state = {"current_snapshot": None}
    
    # Run graph synchronously
    final_state = dba_agent.invoke(initial_state)
    
    anomalies_detected = len(final_state.get("detected_anomalies", []))
    recommendation = final_state.get("current_recommendation")
    errors = final_state.get("errors", [])
    
    if errors:
        return TriggerAnalysisResponse(
            status="error",
            message="; ".join(errors),
            anomalies_detected=anomalies_detected,
            recommendations=recommendation
        )
        
    return TriggerAnalysisResponse(
        status="success",
        message=f"Analysis complete. {anomalies_detected} anomalies found." if anomalies_detected > 0 else "Analysis complete. Database operates normally.",
        anomalies_detected=anomalies_detected,
        recommendations=recommendation
    )

@router.get("/health")
async def health_check():
    return {"status": "ok", "poller_running": collector.is_running}
