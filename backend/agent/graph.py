import json
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END
from models.agent_models import AgentState
from models.api_models import Recommendation, RecommendationAction
from models.db_models import Anomaly
from data_collection.poller import collector
from data_collection.snapshot import snapshot_manager
from anomaly_detection.detector import detector
from llm.groq_client import groq_client
from agent.persona import DBA_SYSTEM_PROMPT
from agent.memory import anomaly_memory
from agent.recommendations import recommendation_manager
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Node 1: Collect Metrics
def collect_metrics_node(state: AgentState) -> AgentState:
    logger.info("Executing Graph Node: collect_metrics")
    # For manual trigger, we fetch fresh. 
    if not state.get("current_snapshot"):
        state["current_snapshot"] = collector.collect_now()
    
    # Initialize necessary lists if absent
    if "errors" not in state:
        state["errors"] = []
    if "historical_anomalies" not in state:
        state["historical_anomalies"] = []
    return state

# Node 2: Detect Anomalies
def detect_anomalies_node(state: AgentState) -> AgentState:
    logger.info("Executing Graph Node: detect_anomalies_baseline")
    if not state.get("current_snapshot"):
        state["should_alert"] = False
        return state

    history = snapshot_manager.get_history(settings.BASELINE_WINDOW_SIZE)
    anomalies = detector.detect(state["current_snapshot"], history)
    
    # Filter by memory to prevent spam
    new_anomalies = []
    for anomaly in anomalies:
        if anomaly_memory.should_alert(anomaly.root_resource):
            new_anomalies.append(anomaly)
            
    state["detected_anomalies"] = new_anomalies
    state["should_alert"] = len(new_anomalies) > 0
    return state

# Conditional Edge
def check_anomalies(state: AgentState) -> str:
    if state.get("should_alert", False):
        return "prepare_llm_prompt"
    return "finalize_response"

# Node 3: Prepare LLM Prompt
def prepare_llm_prompt_node(state: AgentState) -> AgentState:
    logger.info("Executing Graph Node: prepare_enriched_llm_prompt")
    
    # Compress anomaly data to prevent token explosion
    anomalies_data = []
    for a in state["detected_anomalies"]:
        dump = a.model_dump()
        # Truncate overly long SQL text in the context wrapper just in case
        if "sql_text" in dump.get("context_data", {}) and dump["context_data"]["sql_text"]:
            dump["context_data"]["sql_text"] = dump["context_data"]["sql_text"][:1000] + "...(truncated)"
        anomalies_data.append(dump)
    
    # Rich Top Waits Summary
    waits_summary = [
        f"{w.wait_type}: {w.wait_time_ms}ms" 
        for w in state["current_snapshot"].top_wait_stats[:3]
    ]

    prompt = f"""
    The following ACTIVE anomalies were just detected on AdventureWorks2025:
    {json.dumps(anomalies_data, default=str, indent=2)}
    
    --- Database Context Snapshot ---
    Timestamp: {state["current_snapshot"].timestamp.isoformat()}
    Active Sessions: {state["current_snapshot"].active_sessions_count}
    Top 3 Wait Stats: {', '.join(waits_summary)}
    
    Please provide root cause analysis and recommendations respecting the strict JSON format.
    """
    state["llm_prompt"] = prompt
    return state

# Node 4: Call LLM
def call_llm_node(state: AgentState) -> AgentState:
    logger.info("Executing Graph Node: call_llm")
    response_text = groq_client.get_completion(
        system_prompt=DBA_SYSTEM_PROMPT,
        user_prompt=state["llm_prompt"],
        response_format={"type": "json_object"}
    )
    state["llm_analysis"] = response_text or "{}"
    return state

# Node 5: Store Recommendation
def store_recommendation_node(state: AgentState) -> AgentState:
    logger.info("Executing Graph Node: store_recommendation")
    try:
        raw_json = json.loads(state["llm_analysis"])
        rec = Recommendation(
            issue_summary=raw_json.get("issue_summary", "Unknown Issue"),
            technical_diagnosis=raw_json.get("technical_diagnosis", "Failed to parse diagnosis"),
            recommended_actions=[RecommendationAction(**a) for a in raw_json.get("recommended_actions", [])],
            risk_level=raw_json.get("risk_level", "HIGH"),
            confidence_score=float(raw_json.get("confidence_score", 0.0))
        )
        state["current_recommendation"] = rec
        recommendation_manager.add_recommendation(rec)
    except Exception as e:
        logger.error(f"Failed to parse LLM Response: {e}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"LLM Parse Error: {str(e)}")
        
    return state

# final No-Op node
def finalize_response_node(state: AgentState) -> AgentState:
    logger.info("Executing Graph Node: finalize_response")
    return state

def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("collect_metrics", collect_metrics_node)
    workflow.add_node("detect_anomalies", detect_anomalies_node)
    workflow.add_node("prepare_llm_prompt", prepare_llm_prompt_node)
    workflow.add_node("call_llm", call_llm_node)
    workflow.add_node("store_recommendation", store_recommendation_node)
    workflow.add_node("finalize_response", finalize_response_node)
    
    # Add edges
    workflow.set_entry_point("collect_metrics")
    workflow.add_edge("collect_metrics", "detect_anomalies")
    
    workflow.add_conditional_edges(
        "detect_anomalies",
        check_anomalies,
        {
            "prepare_llm_prompt": "prepare_llm_prompt",
            "finalize_response": "finalize_response"
        }
    )
    
    workflow.add_edge("prepare_llm_prompt", "call_llm")
    workflow.add_edge("call_llm", "store_recommendation")
    workflow.add_edge("store_recommendation", "finalize_response")
    workflow.add_edge("finalize_response", END)
    
    return workflow.compile()

dba_agent = build_graph()
