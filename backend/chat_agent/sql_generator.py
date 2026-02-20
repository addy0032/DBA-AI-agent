import json
from models.chat_models import ChatAgentState
from llm.groq_client import groq_client
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# The System Prompt guiding the SQL Generation phase
SQL_GENERATOR_PROMPT = """
You are an expert SQL Server DBA and Data Analyst AI.
Your goal is to parse the user's natural language request and output a strictly valid T-SQL query that answers the question.

DATABASE SCHEMA:
{schema_text}

SECURITY POLICIES:
- You may ONLY perform {allowed_ops} operations.
- Do NOT issue DELETE, DROP, UPDATE, INSERT, ALTER, EXEC, or TRUNCATE.
- Limit large queries with `TOP(1000)` unless aggregation is strictly requested.
- Use explicit JOIN syntax.

Return ONLY a JSON object containing the raw query:
{{
  "generated_sql": "SELECT ... "
}}
"""

class SqlGenerator:
    def generate(self, state: ChatAgentState) -> str:
        logger.info("Generating SQL from User Intent...")
        
        system_prompt = SQL_GENERATOR_PROMPT.format(
            schema_text=state["db_schema_context"],
            allowed_ops=settings.CHAT_ALLOWED_OPERATIONS
        )
        
        # Build context from previous conversation optionally
        history_context = ""
        if state.get("chat_history"):
            history_context = "--- PREVIOUS MESSAGES ---\n"
            for msg in state["chat_history"][-3:]:
                history_context += f"{msg['role'].upper()}: {msg['content']}\n"
            history_context += "\n"

        user_prompt = f"{history_context}USER REQUEST: {state['user_message']}"
        
        try:
            response_text = groq_client.get_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format={"type": "json_object"}
            )
            raw_json = json.loads(response_text)
            sql = raw_json.get("generated_sql", "").strip()
            
            # Remove Markdown codeblocks if the LLM leaked them into the JSON value
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.endswith("```"):
                sql = sql[:-3]
                
            return sql.strip()
        except Exception as e:
            logger.error(f"Failed to generate SQL: {e}")
            return ""

sql_generator = SqlGenerator()
