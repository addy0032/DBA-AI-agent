import pyodbc
from contextlib import contextmanager
from config.settings import settings
from utils.logger import setup_logger
from typing import Generator

logger = setup_logger(__name__)

def get_connection_string() -> str:
    # Build the connection string based on auth type
    if settings.SQL_USE_WINDOWS_AUTH:
        conn_str = (
            f"DRIVER={{{settings.SQL_DRIVER}}};"
            f"SERVER={settings.SQL_SERVER};"
            f"DATABASE={settings.SQL_DATABASE};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes;"
        )
    else:
        conn_str = (
            f"DRIVER={{{settings.SQL_DRIVER}}};"
            f"SERVER={settings.SQL_SERVER};"
            f"DATABASE={settings.SQL_DATABASE};"
            f"UID={settings.SQL_USER};"
            f"PWD={settings.SQL_PASSWORD};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes;"
        )
    return conn_str

@contextmanager
def get_db_connection() -> Generator[pyodbc.Connection, None, None]:
    """
    Context manager for database connections.
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    conn_str = get_connection_string()
    conn = None
    try:
        # autocommit=True is often better for read-only DMV queries to avoid implicit transactions
        conn = pyodbc.connect(conn_str, autocommit=True)
        yield conn
    except pyodbc.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
