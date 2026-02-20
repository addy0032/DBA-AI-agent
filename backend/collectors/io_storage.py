"""I/O & Storage collector: File latency, IOPS, TempDB usage."""
from models.metrics import IOSnapshot, FileIOMetric
from utils.db import get_db_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

FILE_IO_QUERY = """
SELECT
    DB_NAME(vfs.database_id) AS database_name,
    mf.name AS file_name,
    mf.type_desc AS file_type,
    CASE WHEN vfs.num_of_reads = 0 THEN 0
         ELSE vfs.io_stall_read_ms / vfs.num_of_reads END AS read_latency_ms,
    CASE WHEN vfs.num_of_writes = 0 THEN 0
         ELSE vfs.io_stall_write_ms / vfs.num_of_writes END AS write_latency_ms,
    vfs.num_of_reads AS read_iops,
    vfs.num_of_writes AS write_iops,
    CAST(vfs.size_on_disk_bytes / 1048576.0 AS DECIMAL(18,2)) AS size_mb
FROM sys.dm_io_virtual_file_stats(NULL, NULL) vfs
JOIN sys.master_files mf ON vfs.database_id = mf.database_id AND vfs.file_id = mf.file_id
ORDER BY (vfs.io_stall_read_ms + vfs.io_stall_write_ms) DESC;
"""

TEMPDB_QUERY = """
SELECT
    SUM(size) * 8.0 / 1024 AS total_mb,
    SUM(FILEPROPERTY(name, 'SpaceUsed')) * 8.0 / 1024 AS used_mb
FROM sys.master_files
WHERE database_id = DB_ID('tempdb') AND type = 0;
"""


def collect_io() -> IOSnapshot:
    snapshot = IOSnapshot()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(FILE_IO_QUERY)
            for row in cursor.fetchall():
                snapshot.files.append(FileIOMetric(
                    database_name=row.database_name or "",
                    file_name=row.file_name or "",
                    file_type=row.file_type or "",
                    read_latency_ms=float(row.read_latency_ms or 0),
                    write_latency_ms=float(row.write_latency_ms or 0),
                    read_iops=float(row.read_iops or 0),
                    write_iops=float(row.write_iops or 0),
                    size_mb=float(row.size_mb or 0),
                ))

            cursor.execute(TEMPDB_QUERY)
            row = cursor.fetchone()
            if row:
                total = float(row.total_mb or 0)
                used = float(row.used_mb or 0)
                snapshot.tempdb_used_mb = used
                snapshot.tempdb_free_mb = max(0, total - used)

    except Exception as e:
        logger.error(f"I/O collector error: {e}")
    return snapshot
