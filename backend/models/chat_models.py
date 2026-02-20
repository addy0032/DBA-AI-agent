from typing import TypedDict, List, Dict, Any

class ChatAgentState(TypedDict):
    session_id: str
    user_message: str
    
    # Introspection Pipeline
    db_schema_context: str
    
    # LLM Code Gen Pipeline
    generated_sql: str
    
    # Validation
    is_valid_sql: bool
    validation_error: str
    
    # Execution
    query_results_preview: List[Dict[str, Any]]
    execution_time_ms: float
    execution_error: str
    
    # Synthesizer
    explanation: str
    confidence: float
    suggested_chart_type: str
    
    # Conversation Context
    chat_history: List[Dict[str, str]]
