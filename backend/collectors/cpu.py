"""CPU & Scheduler metrics collector."""
from models.metrics import CpuMetrics
from utils.db import get_db_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

CPU_QUERY = """
SELECT TOP 1
    record.value('(./Record/SchedulerMonitorEvent/SystemHealth/SystemIdle)[1]', 'int') AS system_idle,
    record.value('(./Record/SchedulerMonitorEvent/SystemHealth/ProcessUtilization)[1]', 'int') AS sql_cpu
FROM (
    SELECT CONVERT(XML, record) AS record
    FROM sys.dm_os_ring_buffers
    WHERE ring_buffer_type = N'RING_BUFFER_SCHEDULER_MONITOR'
      AND record LIKE '%<SystemHealth>%'
) AS x
ORDER BY record.value('(./Record/@id)[1]', 'int') DESC;
"""

SCHEDULER_QUERY = """
SELECT
    COUNT(*) AS scheduler_count,
    SUM(runnable_tasks_count) AS runnable_tasks_count,
    SUM(current_workers_count) AS current_workers_count
FROM sys.dm_os_schedulers
WHERE status = 'VISIBLE ONLINE';
"""

MAX_WORKERS_QUERY = """
SELECT max_workers_count FROM sys.dm_os_sys_info;
"""

SIGNAL_WAIT_QUERY = """
SELECT
    CAST(100.0 * SUM(signal_wait_time_ms) / NULLIF(SUM(wait_time_ms), 0) AS DECIMAL(5,2)) AS signal_wait_pct
FROM sys.dm_os_wait_stats
WHERE wait_type NOT IN (
    'SLEEP_TASK','LAZYWRITER_SLEEP','SQLTRACE_BUFFER_FLUSH',
    'WAITFOR','CLR_AUTO_EVENT','CLR_MANUAL_EVENT',
    'REQUEST_FOR_DEADLOCK_SEARCH','BROKER_TASK_STOP'
);
"""


def collect_cpu() -> CpuMetrics:
    metrics = CpuMetrics()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # CPU from ring buffer
            cursor.execute(CPU_QUERY)
            row = cursor.fetchone()
            if row:
                metrics.sql_cpu_percent = float(row.sql_cpu or 0)
                metrics.system_idle_percent = float(row.system_idle or 0)
                metrics.other_process_cpu_percent = max(0, 100.0 - metrics.sql_cpu_percent - metrics.system_idle_percent)

            # Scheduler stats
            cursor.execute(SCHEDULER_QUERY)
            row = cursor.fetchone()
            if row:
                metrics.scheduler_count = row.scheduler_count or 0
                metrics.runnable_tasks_count = row.runnable_tasks_count or 0
                metrics.current_workers_count = row.current_workers_count or 0

            # Max workers
            cursor.execute(MAX_WORKERS_QUERY)
            row = cursor.fetchone()
            if row:
                metrics.max_workers_count = row.max_workers_count or 0

            # Signal wait ratio
            cursor.execute(SIGNAL_WAIT_QUERY)
            row = cursor.fetchone()
            if row and row.signal_wait_pct is not None:
                metrics.signal_wait_pct = float(row.signal_wait_pct)

    except Exception as e:
        logger.error(f"CPU collector error: {e}")

    return metrics
