"""Wait Statistics collector with delta computation."""
from datetime import datetime, timezone
from models.metrics import WaitStatsSnapshot, WaitStatDelta
from metrics_engine.delta import delta_tracker
from utils.db import get_db_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Filter out benign/idle waits that create noise
WAIT_STATS_QUERY = """
SELECT
    wait_type,
    waiting_tasks_count,
    wait_time_ms,
    signal_wait_time_ms
FROM sys.dm_os_wait_stats
WHERE wait_type NOT IN (
    'DIRTY_PAGE_POLL','HADR_FILESTREAM_IOMGR_IOCOMPLETION',
    'LAZYWRITER_SLEEP','LOGMGR_QUEUE','REQUEST_FOR_DEADLOCK_SEARCH',
    'SLEEP_TASK','SQLTRACE_BUFFER_FLUSH','WAITFOR',
    'BROKER_TASK_STOP','CLR_MANUAL_EVENT','CLR_AUTO_EVENT',
    'DISPATCHER_QUEUE_SEMAPHORE','FT_IFTS_SCHEDULER_IDLE_WAIT',
    'XE_DISPATCHER_WAIT','XE_TIMER_EVENT','BROKER_EVENTHANDLER',
    'CHECKPOINT_QUEUE','CHKPT','HADR_WORK_QUEUE',
    'KSOURCE_WAKEUP','ONDEMAND_TASK_QUEUE','SLEEP_BPOOL_FLUSH',
    'SLEEP_DBSTARTUP','SLEEP_DCOMSTARTUP','SLEEP_MASTERDBREADY',
    'SLEEP_MASTERMDREADY','SLEEP_MASTERUPGRADED','SLEEP_MSDBSTARTUP',
    'SLEEP_SYSTEMTASK','SLEEP_TEMPDBSTARTUP','SNI_HTTP_ACCEPT',
    'SP_SERVER_DIAGNOSTICS_SLEEP','SQLTRACE_INCREMENTAL_FLUSH_SLEEP',
    'SQLTRACE_WAIT_ENTRIES','WAIT_FOR_RESULTS','WAIT_XTP_CKPT_CLOSE',
    'WAIT_XTP_HOST_WAIT','WAIT_XTP_OFFLINE_CKPT_NEW_LOG',
    'WAIT_XTP_RECOVERY','PREEMPTIVE_OS_AUTHENTICATIONOPS',
    'PREEMPTIVE_OS_GETPROCADDRESS','BROKER_RECEIVE_WAITFOR'
)
  AND wait_time_ms > 0
ORDER BY wait_time_ms DESC;
"""


def collect_waits() -> WaitStatsSnapshot:
    now = datetime.now(timezone.utc)
    elapsed = delta_tracker.get_elapsed_seconds(now)
    snapshot = WaitStatsSnapshot(timestamp=now, elapsed_seconds=elapsed)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(WAIT_STATS_QUERY)

            raw_deltas = []
            for row in cursor.fetchall():
                wt = row.wait_type
                cum_wait = row.wait_time_ms or 0
                cum_tasks = row.waiting_tasks_count or 0
                cum_signal = row.signal_wait_time_ms or 0

                wait_delta = delta_tracker.compute_delta("waits_time", wt, cum_wait, now)
                tasks_delta = delta_tracker.compute_delta("waits_tasks", wt, cum_tasks, now)
                signal_delta = delta_tracker.compute_delta("waits_signal", wt, cum_signal, now)

                raw_deltas.append(WaitStatDelta(
                    wait_type=wt,
                    wait_time_delta_ms=wait_delta,
                    waiting_tasks_delta=int(tasks_delta),
                    signal_wait_delta_ms=signal_delta,
                    wait_rate_ms_per_sec=wait_delta / elapsed if elapsed > 0 else 0,
                    dominance_pct=0,  # computed below
                    cumulative_wait_time_ms=cum_wait,
                    cumulative_waiting_tasks=cum_tasks,
                    cumulative_signal_wait_ms=cum_signal,
                ))

            # Compute dominance %
            total_delta = sum(d.wait_time_delta_ms for d in raw_deltas)
            snapshot.total_delta_ms = total_delta
            for d in raw_deltas:
                d.dominance_pct = (d.wait_time_delta_ms / total_delta * 100) if total_delta > 0 else 0

            # Keep top 20 by delta, filter out zero-deltas
            snapshot.waits = sorted(
                [d for d in raw_deltas if d.wait_time_delta_ms > 0],
                key=lambda d: d.wait_time_delta_ms,
                reverse=True
            )[:20]

    except Exception as e:
        logger.error(f"Wait stats collector error: {e}")

    return snapshot
