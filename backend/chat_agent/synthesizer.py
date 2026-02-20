import json
from models.chat_models import ChatAgentState
from llm.groq_client import groq_client
from utils.logger import setup_logger

logger = setup_logger(__name__)

SYNTHESIZER_PROMPT = """
You are an expert SQL Server Data Analyst responding to an executive or engineer.
You just executed a SQL query on their behalf. The results are provided below.

Your goal is to explain WHAT these results mean contextually in concise, natural language.

--- CONTEXT ---
Original User Request: {user_message}
SQL Executed: {sql_text}

--- RESULTS ROW PREVIEW ({row_count} rows total) ---
{results_json}

INSTRUCTIONS:
1. Provide a clear, natural language explanation of the answer. 
2. Recommend follow-up questions if appropriate.
3. Suggest an ECharts visual type ("bar", "line", "pie", or "none") if the data is aggregative or categorical.
4. Output strict JSON.

{{
  "explanation": "...",
  "suggested_chart_type": "none",
  "confidence": 0.95
}}
"""

class ResultSynthesizer:
    def synthesize(self, state: ChatAgentState) -> dict:
        logger.info("Synthesizing Query Results into Natural Language...")
        
        results = state.get("query_results_preview", [])
        
        # If execution failed, summarize the error
        if state.get("execution_error") or not state.get("is_valid_sql"):
            error_msg = state.get("execution_error") or state.get("validation_error")
            return {
                "explanation": f"I couldn't complete that request. Error: {error_msg}",
                "suggested_chart_type": "none",
                "confidence": 0.0
            }
            
        # Avoid overflowing LLM if row size is massive, just sample first 50
        sample_results = results[:50]
        results_json = json.dumps(sample_results, default=str)
        
        prompt = SYNTHESIZER_PROMPT.format(
            user_message=state["user_message"],
            sql_text=state["generated_sql"],
            row_count=len(results),
            results_json=results_json
        )
        
        try:
            response_text = groq_client.get_completion(
                system_prompt="You are a data interpretation module. Output strict JSON only.",
                user_prompt=prompt,
                response_format={"type": "json_object"}
            )
            parsed = json.loads(response_text)
            
            return {
                "explanation": parsed.get("explanation", "Data retrieval successful."),
                "suggested_chart_type": parsed.get("suggested_chart_type", "none"),
                "confidence": float(parsed.get("confidence", 0.8))
            }
        except Exception as e:
            logger.error(f"Synthesizer LLM failed: {e}")
            return {
                "explanation": f"Retrieved {len(results)} rows. (Failed to generate AI summary)",
                "suggested_chart_type": "none",
                "confidence": 0.0
            }

result_synthesizer = ResultSynthesizer()
