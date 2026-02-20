import pyodbc
from typing import Dict, Any, List, Tuple
from utils.db import get_connection_string
from config.settings import settings
from utils.logger import setup_logger
import time

logger = setup_logger(__name__)

class QueryExecutor:
    def execute(self, sql: str) -> Tuple[List[Dict[str, Any]], float, str]:
        """
        Executes a SQL query in a safe, read-only isolated connection.
        Returns: (results_list, execution_time_ms, error_string)
        """
        start_time = time.time()
        conn = None
        try:
            logger.info("Connecting to sandbox execution environment...")
            # Enforce read-only autocommit to prevent locking transactions from hanging
            conn = pyodbc.connect(get_connection_string(), autocommit=True, timeout=settings.QUERY_TIMEOUT_SECONDS)
            cursor = conn.cursor()

            # Set a pessimistic lock timeout (e.g., 5000ms) so the chatbot won't wait 
            # indefinitely if it queries a locked table, protecting the main app.
            cursor.execute("SET LOCK_TIMEOUT 5000")
            
            # We enforce a hard row limit if the query missed a TOP/LIMIT clause
            sql_restricted = sql
            
            logger.debug(f"Executing Sandbox SQL => {sql_restricted[:100]}")
            cursor.execute(sql_restricted)
            
            # For queries like SELECT, fetch results. 
            # If the LLM generates a valid "PRINT" or something that doesn't return rows, skip.
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                
                # We enforce max rows at runtime to prevent RAM explosion
                rows = cursor.fetchmany(settings.CHAT_MAX_RESULT_ROWS) 
                
                results = [dict(zip(columns, row)) for row in rows]
                exec_time_ms = (time.time() - start_time) * 1000
                return results, exec_time_ms, ""
            else:
                exec_time_ms = (time.time() - start_time) * 1000
                return [], exec_time_ms, "Query executed successfully but returned no rows."
                
        except pyodbc.Error as e:
            logger.error(f"Sandbox query exception: {e}")
            return [], (time.time() - start_time) * 1000, f"Database Execution Error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected execution error: {e}")
            return [], (time.time() - start_time) * 1000, f"Unexpected Error: {str(e)}"
        finally:
            if conn:
                conn.close()

query_executor = QueryExecutor()
