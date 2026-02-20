"""Database Health collector: Recovery model, size, backups, log reuse."""
from models.metrics import DatabasesSnapshot, DatabaseInfo
from utils.db import get_db_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

DATABASES_QUERY = """
SELECT
    d.name AS db_name,
    d.state_desc,
    d.recovery_model_desc AS recovery_model,
    d.compatibility_level,
    d.log_reuse_wait_desc,
    (SELECT SUM(size) * 8.0 / 1024 FROM sys.master_files mf WHERE mf.database_id = d.database_id) AS size_mb,
    (SELECT SUM(size - FILEPROPERTY(name, 'SpaceUsed')) * 8.0 / 1024
     FROM sys.master_files mf WHERE mf.database_id = d.database_id AND mf.type = 0) AS free_space_mb,
    (SELECT MAX(bs.backup_finish_date)
     FROM msdb.dbo.backupset bs WHERE bs.database_name = d.name AND bs.type = 'D') AS last_full_backup,
    (SELECT MAX(bs.backup_finish_date)
     FROM msdb.dbo.backupset bs WHERE bs.database_name = d.name AND bs.type = 'L') AS last_log_backup
FROM sys.databases d
WHERE d.database_id > 4
ORDER BY d.name;
"""


def collect_databases() -> DatabasesSnapshot:
    snapshot = DatabasesSnapshot()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(DATABASES_QUERY)
            for row in cursor.fetchall():
                snapshot.databases.append(DatabaseInfo(
                    db_name=row.db_name or "",
                    state_desc=row.state_desc or "ONLINE",
                    recovery_model=row.recovery_model or "",
                    compatibility_level=row.compatibility_level or 0,
                    size_mb=float(row.size_mb or 0),
                    free_space_mb=float(row.free_space_mb or 0),
                    last_full_backup=row.last_full_backup,
                    last_log_backup=row.last_log_backup,
                    log_reuse_wait_desc=row.log_reuse_wait_desc or "",
                ))
    except Exception as e:
        logger.error(f"Database collector error: {e}")
    return snapshot
