"""Memory & Buffer Pool metrics collector."""
from models.metrics import MemoryMetrics
from utils.db import get_db_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

PERF_COUNTERS_QUERY = """
SELECT
    RTRIM(counter_name) AS counter_name,
    cntr_value
FROM sys.dm_os_performance_counters
WHERE (object_name LIKE '%:Memory Manager%'
       AND counter_name IN (
           'Total Server Memory (KB)',
           'Target Server Memory (KB)',
           'Memory Grants Pending',
           'Memory Grants Outstanding',
           'Stolen Server Memory (KB)',
           'Free Memory (KB)'
       ))
   OR (object_name LIKE '%:Buffer Manager%'
       AND counter_name IN ('Page life expectancy', 'Buffer cache hit ratio'));
"""

SYS_MEMORY_QUERY = """
SELECT
    total_physical_memory_kb / 1024.0 AS total_physical_memory_mb,
    available_physical_memory_kb / 1024.0 AS available_physical_memory_mb
FROM sys.dm_os_sys_memory;
"""


def collect_memory() -> MemoryMetrics:
    metrics = MemoryMetrics()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(PERF_COUNTERS_QUERY)
            for row in cursor.fetchall():
                name = row.counter_name.strip()
                val = row.cntr_value or 0

                if name == "Total Server Memory (KB)":
                    metrics.total_server_memory_mb = val / 1024.0
                elif name == "Target Server Memory (KB)":
                    metrics.target_server_memory_mb = val / 1024.0
                elif name == "Page life expectancy":
                    metrics.page_life_expectancy = val
                elif name == "Buffer cache hit ratio":
                    metrics.buffer_cache_hit_ratio = float(val)
                elif name == "Memory Grants Pending":
                    metrics.memory_grants_pending = val
                elif name == "Memory Grants Outstanding":
                    metrics.memory_grants_outstanding = val
                elif name == "Stolen Server Memory (KB)":
                    metrics.stolen_server_memory_kb = val
                elif name == "Free Memory (KB)":
                    metrics.free_memory_kb = val

            cursor.execute(SYS_MEMORY_QUERY)
            row = cursor.fetchone()
            if row:
                metrics.total_physical_memory_mb = float(row.total_physical_memory_mb or 0)
                metrics.available_physical_memory_mb = float(row.available_physical_memory_mb or 0)

    except Exception as e:
        logger.error(f"Memory collector error: {e}")

    return metrics
