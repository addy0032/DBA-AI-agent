from fastapi import APIRouter, HTTPException
from models.api_models import ChatRequest, ChatResponse
from models.chat_models import ChatAgentState
from chat_agent.graph import chat_agent_graph
from chat_agent.memory import chat_memory
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    try:
        # Load conversation memory
        history = chat_memory.get_history(request.session_id)
        
        # Initialize graph state
        initial_state: ChatAgentState = {
            "session_id": request.session_id,
            "user_message": request.user_message,
            "chat_history": history,
            "db_schema_context": "",
            "generated_sql": "",
            "is_valid_sql": False,
            "validation_error": "",
            "query_results_preview": [],
            "execution_time_ms": 0.0,
            "execution_error": "",
            "explanation": "",
            "confidence": 0.0,
            "suggested_chart_type": "none"
        }
        
        # Synchronously invoke graph
        final_state = chat_agent_graph.invoke(initial_state)
        
        # Save Q&A to Memory
        chat_memory.add_message(request.session_id, "user", request.user_message)
        chat_memory.add_message(request.session_id, "assistant", final_state.get("explanation", ""))
        
        # Formulate Response
        return ChatResponse(
            generated_sql=final_state.get("generated_sql"),
            explanation=final_state.get("explanation"),
            confidence=final_state.get("confidence", 0.0),
            execution_time_ms=final_state.get("execution_time_ms", 0.0),
            query_results_preview=final_state.get("query_results_preview", []),
            error_message=final_state.get("validation_error") or final_state.get("execution_error"),
            suggested_chart_type=final_state.get("suggested_chart_type", "none")
        )
        
    except Exception as e:
        logger.error(f"Chat Graph failed: {e}")
        return ChatResponse(
            explanation="The SQL Chat Agent encountered an unexpected error.",
            error_message=str(e),
            confidence=0.0
        )

@router.get("/history")
async def get_chat_history(session_id: str = "default_session"):
    return chat_memory.get_history(session_id)

@router.delete("/history")
async def clear_chat_history(session_id: str = "default_session"):
    chat_memory.clear_session(session_id)
    return {"status": "cleared"}
