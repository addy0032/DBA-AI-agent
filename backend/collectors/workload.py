"""Workload collector: Sessions, Blocking, and Expensive Queries."""
from models.metrics import (
    SessionSummary, BlockingSnapshot, BlockingNode,
    QuerySnapshot, TopQuery
)
from utils.db import get_db_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

SESSION_SUMMARY_QUERY = """
SELECT
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN status = 'running' AND session_id > 50 THEN 1 ELSE 0 END) AS active_sessions,
    SUM(CASE WHEN status = 'sleeping' AND session_id > 50 THEN 1 ELSE 0 END) AS sleeping_sessions,
    (SELECT COUNT(*) FROM sys.dm_exec_requests WHERE blocking_session_id <> 0) AS blocked_sessions
FROM sys.dm_exec_sessions
WHERE session_id > 50;
"""

BLOCKING_TREE_QUERY = """
SELECT
    w.session_id,
    w.blocking_session_id,
    w.wait_type,
    w.wait_duration_ms AS wait_time_ms,
    r.status,
    r.command,
    SUBSTRING(st.text, 1, 500) AS sql_text,
    DB_NAME(r.database_id) AS database_name,
    s.host_name,
    s.program_name
FROM sys.dm_os_waiting_tasks w
JOIN sys.dm_exec_requests r ON w.session_id = r.session_id
JOIN sys.dm_exec_sessions s ON r.session_id = s.session_id
OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) st
WHERE w.blocking_session_id <> 0
   OR w.session_id IN (SELECT blocking_session_id FROM sys.dm_os_waiting_tasks WHERE blocking_session_id <> 0);
"""

TOP_QUERIES_BY_CPU = """
SELECT TOP 10
    CONVERT(VARCHAR(64), qs.query_hash, 1) AS query_hash,
    qs.execution_count,
    qs.total_worker_time,
    qs.total_logical_reads,
    qs.total_elapsed_time,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1,
        ((CASE qs.statement_end_offset WHEN -1 THEN DATALENGTH(st.text)
          ELSE qs.statement_end_offset END - qs.statement_start_offset)/2) + 1) AS sql_text,
    DB_NAME(st.dbid) AS database_name
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
ORDER BY qs.total_worker_time DESC;
"""

TOP_QUERIES_BY_READS = """
SELECT TOP 10
    CONVERT(VARCHAR(64), qs.query_hash, 1) AS query_hash,
    qs.execution_count,
    qs.total_worker_time,
    qs.total_logical_reads,
    qs.total_elapsed_time,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1,
        ((CASE qs.statement_end_offset WHEN -1 THEN DATALENGTH(st.text)
          ELSE qs.statement_end_offset END - qs.statement_start_offset)/2) + 1) AS sql_text,
    DB_NAME(st.dbid) AS database_name
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
ORDER BY qs.total_logical_reads DESC;
"""

TOP_QUERIES_BY_DURATION = """
SELECT TOP 10
    CONVERT(VARCHAR(64), qs.query_hash, 1) AS query_hash,
    qs.execution_count,
    qs.total_worker_time,
    qs.total_logical_reads,
    qs.total_elapsed_time,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1,
        ((CASE qs.statement_end_offset WHEN -1 THEN DATALENGTH(st.text)
          ELSE qs.statement_end_offset END - qs.statement_start_offset)/2) + 1) AS sql_text,
    DB_NAME(st.dbid) AS database_name
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
ORDER BY qs.total_elapsed_time DESC;
"""


def collect_sessions() -> SessionSummary:
    summary = SessionSummary()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(SESSION_SUMMARY_QUERY)
            row = cursor.fetchone()
            if row:
                summary.total_sessions = row.total_sessions or 0
                summary.active_sessions = row.active_sessions or 0
                summary.sleeping_sessions = row.sleeping_sessions or 0
                summary.blocked_sessions = row.blocked_sessions or 0
    except Exception as e:
        logger.error(f"Session collector error: {e}")
    return summary


def collect_blocking() -> BlockingSnapshot:
    snapshot = BlockingSnapshot()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(BLOCKING_TREE_QUERY)

            all_sessions = set()
            blocking_ids = set()
            nodes = []

            for row in cursor.fetchall():
                all_sessions.add(row.session_id)
                blocking_ids.add(row.blocking_session_id)
                nodes.append(BlockingNode(
                    session_id=row.session_id,
                    blocking_session_id=row.blocking_session_id,
                    wait_type=row.wait_type,
                    wait_time_ms=row.wait_time_ms or 0,
                    status=row.status or "",
                    command=row.command or "",
                    sql_text=row.sql_text,
                    database_name=row.database_name,
                    host_name=row.host_name,
                    program_name=row.program_name,
                ))

            head_blockers = blocking_ids - all_sessions
            for n in nodes:
                n.is_head_blocker = n.blocking_session_id in head_blockers

            snapshot.chains = nodes
            snapshot.head_blocker_count = len(head_blockers)

    except Exception as e:
        logger.error(f"Blocking collector error: {e}")
    return snapshot


def _parse_query_rows(cursor) -> list[TopQuery]:
    results = []
    for row in cursor.fetchall():
        results.append(TopQuery(
            query_hash=row.query_hash or "",
            execution_count=row.execution_count or 0,
            total_worker_time=row.total_worker_time or 0,
            total_logical_reads=row.total_logical_reads or 0,
            total_elapsed_time=row.total_elapsed_time or 0,
            sql_text=(row.sql_text or "")[:500],
            database_name=row.database_name,
        ))
    return results


def collect_queries() -> QuerySnapshot:
    snapshot = QuerySnapshot()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(TOP_QUERIES_BY_CPU)
            snapshot.top_by_cpu = _parse_query_rows(cursor)

            cursor.execute(TOP_QUERIES_BY_READS)
            snapshot.top_by_reads = _parse_query_rows(cursor)

            cursor.execute(TOP_QUERIES_BY_DURATION)
            snapshot.top_by_duration = _parse_query_rows(cursor)

    except Exception as e:
        logger.error(f"Query collector error: {e}")
    return snapshot
