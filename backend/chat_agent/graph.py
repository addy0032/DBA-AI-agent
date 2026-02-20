from typing import Dict, List
import json
from langgraph.graph import StateGraph, END
from models.chat_models import ChatAgentState
from chat_agent.schema import schema_introspector
from chat_agent.sql_generator import sql_generator
from chat_agent.validator import sql_validator
from chat_agent.executor import query_executor
from chat_agent.synthesizer import result_synthesizer
from utils.logger import setup_logger

logger = setup_logger(__name__)

def introspect_schema_node(state: ChatAgentState) -> ChatAgentState:
    logger.info("ChatNode: introspect_schema")
    # Fetch compressed schema for the LLM context prompt
    state["db_schema_context"] = schema_introspector.get_schema_summary()
    return state

def generate_sql_node(state: ChatAgentState) -> ChatAgentState:
    logger.info("ChatNode: generate_sql")
    state["generated_sql"] = sql_generator.generate(state)
    return state

def validate_sql_node(state: ChatAgentState) -> ChatAgentState:
    logger.info("ChatNode: validate_sql")
    sql = state.get("generated_sql", "")
    
    # Empty SQL usually implies the LLM decided the prompt wasn't DB related
    if not sql:
        state["is_valid_sql"] = False
        state["validation_error"] = "Agent could not map the request to valid SQL."
        return state
        
    is_valid, error_msg = sql_validator.validate(sql)
    state["is_valid_sql"] = is_valid
    state["validation_error"] = error_msg
    return state

def check_sql_validity(state: ChatAgentState) -> str:
    """Conditional Edge preventing Sandbox Execution if SQL AST parsed illegal DML"""
    if state.get("is_valid_sql", False):
        return "execute_sql"
    return "synthesize_results"

def execute_sql_node(state: ChatAgentState) -> ChatAgentState:
    logger.info("ChatNode: execute_sql")
    sql = state.get("generated_sql", "")
    
    # Fire it to the explicit read-only pyodbc connection
    results, exec_time, error = query_executor.execute(sql)
    
    state["query_results_preview"] = results
    state["execution_time_ms"] = exec_time
    state["execution_error"] = error
    return state

def synthesize_results_node(state: ChatAgentState) -> ChatAgentState:
    logger.info("ChatNode: synthesize_results")
    
    # Convert output grid back into an english explanation and chart mapping
    summary_pack = result_synthesizer.synthesize(state)
    
    state["explanation"] = summary_pack.get("explanation", "")
    state["suggested_chart_type"] = summary_pack.get("suggested_chart_type", "none")
    state["confidence"] = summary_pack.get("confidence", 0.0)
    return state

def build_chat_graph() -> StateGraph:
    workflow = StateGraph(ChatAgentState)
    
    # 1. Add all functional nodes
    workflow.add_node("introspect_schema", introspect_schema_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("synthesize_results", synthesize_results_node)
    
    # 2. Add linear Edges
    workflow.set_entry_point("introspect_schema")
    workflow.add_edge("introspect_schema", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")
    
    # 3. Add conditional edge (Don't execute Dropping a table, route straight to LLM error apology)
    workflow.add_conditional_edges(
        "validate_sql",
        check_sql_validity,
        {
            "execute_sql": "execute_sql",
            "synthesize_results": "synthesize_results"
        }
    )
    
    # 4. Tie off execution results into Synthesizer
    workflow.add_edge("execute_sql", "synthesize_results")
    workflow.add_edge("synthesize_results", END)
    
    return workflow.compile()

chat_agent_graph = build_chat_graph()
