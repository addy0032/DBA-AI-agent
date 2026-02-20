from typing import Dict, Any, List
import pyodbc
from utils.db import get_db_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SchemaIntrospector:
    def __init__(self):
        self._schema_cache = None

    def get_schema_summary(self) -> str:
        if self._schema_cache:
            return self._schema_cache

        logger.info("Introspecting SQL Server Schema for AI Chat Context...")
        schema_text = []
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Fetch Tables and Columns
                cursor.execute("""
                    SELECT 
                        s.name AS schema_name,
                        t.name AS table_name,
                        c.name AS column_name,
                        tp.name AS data_type,
                        c.max_length,
                        c.is_nullable
                    FROM sys.tables t
                    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                    INNER JOIN sys.columns c ON t.object_id = c.object_id
                    INNER JOIN sys.types tp ON c.user_type_id = tp.user_type_id
                    WHERE s.name != 'sys' AND s.name != 'INFORMATION_SCHEMA'
                    ORDER BY s.name, t.name, c.column_id;
                """)
                
                current_table = None
                for row in cursor.fetchall():
                    table_full_name = f"{row.schema_name}.{row.table_name}"
                    if table_full_name != current_table:
                        if current_table is not None:
                            schema_text.append(")")
                        schema_text.append(f"Table {table_full_name} (")
                        current_table = table_full_name
                    
                    null_str = "NULL" if row.is_nullable else "NOT NULL"
                    schema_text.append(f"  {row.column_name} {row.data_type} {null_str},")
                
                if current_table is not None:
                    schema_text.append(")")
                
                # Fetch Primary and Foreign Keys
                cursor.execute("""
                    SELECT 
                        fk.name AS fk_name,
                        s1.name AS schema_name,
                        t1.name AS table_name,
                        c1.name AS column_name,
                        s2.name AS ref_schema_name,
                        t2.name AS ref_table_name,
                        c2.name AS ref_column_name
                    FROM sys.foreign_keys fk
                    INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
                    INNER JOIN sys.tables t1 ON fkc.parent_object_id = t1.object_id
                    INNER JOIN sys.schemas s1 ON t1.schema_id = s1.schema_id
                    INNER JOIN sys.columns c1 ON fkc.parent_object_id = c1.object_id AND fkc.parent_column_id = c1.column_id
                    INNER JOIN sys.tables t2 ON fkc.referenced_object_id = t2.object_id
                    INNER JOIN sys.schemas s2 ON t2.schema_id = s2.schema_id
                    INNER JOIN sys.columns c2 ON fkc.referenced_object_id = c2.object_id AND fkc.referenced_column_id = c2.column_id;
                """)
                
                schema_text.append("\nForeign Keys:")
                for fk in cursor.fetchall():
                    schema_text.append(f"  {fk.schema_name}.{fk.table_name}({fk.column_name}) REFERENCES {fk.ref_schema_name}.{fk.ref_table_name}({fk.ref_column_name})")

        except Exception as e:
            logger.error(f"Failed to introspect schema: {e}")
            return "Error introspecting schema."
            
        self._schema_cache = "\n".join(schema_text)
        return self._schema_cache

    def refresh_cache(self):
        self._schema_cache = None

schema_introspector = SchemaIntrospector()
