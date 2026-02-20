import sqlparse
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SqlValidator:
    def __init__(self):
        self.allowed_operations = [op.strip().upper() for op in settings.CHAT_ALLOWED_OPERATIONS.split(',')]
        self.enable_dml = settings.CHAT_ENABLE_DML

    def validate(self, sql: str) -> tuple[bool, str]:
        if not sql or not sql.strip():
            return False, "SQL query cannot be empty."

        try:
            # Parse the SQL statement(s)
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False, "Failed to parse SQL."

            # A user might send multiple statements (e.g. SELECT 1; SELECT 2;)
            # Walk through each parsed statement
            for statement in parsed:
                # Filter out pure whitespaces/comments to find the command type
                stmt_type = statement.get_type().upper()
                
                logger.debug(f"Validating parsed SQL statement type: {stmt_type}")

                # 1. Check if statement type is explicitly allowed
                if stmt_type not in self.allowed_operations:
                    if stmt_type == "UNKNOWN":
                        # Sometimes sqlparse struggles with T-SQL CTEs (WITH clause)
                        tokens = [t for t in statement.tokens if not t.is_whitespace]
                        if tokens and tokens[0].value.upper() == 'WITH':
                            # It's a CTE which usually leads to a SELECT
                            pass
                        else:
                            return False, f"Operation type '{stmt_type}' is not recognized or permitted."
                    else:
                        return False, f"Operation '{stmt_type}' is forbidden by security policy."

                # 2. Walk AST to detect DML/DDL inside subqueries or CTEs just in case
                if not self.enable_dml:
                    for token in statement.flatten():
                        val = token.value.upper()
                        if token.ttype in sqlparse.tokens.Keyword or token.ttype in sqlparse.tokens.Keyword.DML or token.ttype in sqlparse.tokens.Keyword.DDL:
                            if val in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE', 'EXEC', 'EXECUTE', 'CREATE']:
                                return False, f"Explicit DML/DDL keyword '{val}' detected and blocked by policy."

            return True, "Valid"
            
        except Exception as e:
            logger.error(f"SQL validation crashed: {e}")
            return False, f"SQL validation engine failure: {str(e)}"

sql_validator = SqlValidator()
