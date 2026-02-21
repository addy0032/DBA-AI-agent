import pyodbc
from contextlib import contextmanager
from config.settings import settings
from utils.logger import setup_logger
from typing import Generator, List
import threading

logger = setup_logger(__name__)

# Runtime-mutable active database name
_active_db_lock = threading.Lock()
_active_database: str = settings.SQL_DATABASE


def get_active_database() -> str:
    """Return the currently active database name."""
    with _active_db_lock:
        return _active_database


def set_active_database(db_name: str) -> None:
    """Switch the active database at runtime (no restart required)."""
    global _active_database
    with _active_db_lock:
        _active_database = db_name
    logger.info(f"Active database switched to: {db_name}")


def get_connection_string(database: str | None = None) -> str:
    """Build ODBC connection string. Uses active database if none specified."""
    db = database or get_active_database()

    if settings.SQL_USE_WINDOWS_AUTH:
        conn_str = (
            f"DRIVER={{{settings.SQL_DRIVER}}};"
            f"SERVER={settings.SQL_SERVER};"
            f"DATABASE={db};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes;"
        )
    else:
        conn_str = (
            f"DRIVER={{{settings.SQL_DRIVER}}};"
            f"SERVER={settings.SQL_SERVER};"
            f"DATABASE={db};"
            f"UID={settings.SQL_USER};"
            f"PWD={settings.SQL_PASSWORD};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes;"
        )
    return conn_str


@contextmanager
def get_db_connection(database: str | None = None) -> Generator[pyodbc.Connection, None, None]:
    """
    Context manager for database connections.
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    conn_str = get_connection_string(database)
    conn = None
    try:
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


def list_all_databases() -> List[str]:
    """List all user databases on the SQL Server instance (connects to master)."""
    dbs = []
    try:
        with get_db_connection(database="master") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sys.databases "
                "WHERE database_id > 4 AND state_desc = 'ONLINE' "
                "ORDER BY name"
            )
            dbs = [row.name for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
    return dbs
