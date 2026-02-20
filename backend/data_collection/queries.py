# SQL DMV Queries

# 1. Active sessions & Blocking
ACTIVE_SESSIONS_QUERY = """
WITH BlockingTree AS (
    SELECT 
        w.session_id,
        w.blocking_session_id,
        w.wait_type,
        w.wait_duration_ms as wait_time_ms,
        r.status,
        r.command,
        t.text AS sql_text,
        DB_NAME(r.database_id) AS database_name,
        s.host_name,
        s.program_name
    FROM sys.dm_os_waiting_tasks w
    JOIN sys.dm_exec_requests r ON w.session_id = r.session_id
    JOIN sys.dm_exec_sessions s ON r.session_id = s.session_id
    OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) t
    WHERE w.blocking_session_id <> 0 
       OR w.session_id IN (SELECT blocking_session_id FROM sys.dm_os_waiting_tasks WHERE blocking_session_id <> 0)
)
SELECT * FROM BlockingTree;
"""

ACTIVE_REQUESTS_COUNT_QUERY = """
SELECT COUNT(*) as active_sessions 
FROM sys.dm_exec_requests 
WHERE session_id > 50 AND status = 'running';
"""

# 2. Wait Stats
WAIT_STATS_QUERY = """
SELECT TOP 10
    wait_type,
    waiting_tasks_count,
    wait_time_ms,
    max_wait_time_ms,
    signal_wait_time_ms
FROM sys.dm_os_wait_stats
WHERE wait_type NOT IN (
    'DIRTY_PAGE_POLL', 'HADR_FILESTREAM_IOMGR_IOCOMPLETION', 
    'LAZYWRITER_SLEEP', 'LOGMGR_QUEUE', 'REQUEST_FOR_DEADLOCK_SEARCH',
    'SLEEP_TASK', 'SQLTRACE_BUFFER_FLUSH', 'WAITFOR',
    'BROKER_TASK_STOP', 'CLR_MANUAL_EVENT', 'CLR_AUTO_EVENT', 'DISPATCHER_QUEUE_SEMAPHORE',
    'FT_IFTS_SCHEDULER_IDLE_WAIT', 'XE_DISPATCHER_WAIT', 'XE_TIMER_EVENT'
)
ORDER BY wait_time_ms DESC;
"""

# 3. Expensive Queries (High CPU/Reads)
EXPENSIVE_QUERIES_QUERY = """
SELECT TOP 10
    CONVERT(VARCHAR(64), qs.query_hash, 1) as query_hash,
    qs.execution_count,
    qs.total_worker_time,
    qs.total_logical_reads,
    qs.total_elapsed_time,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1, 
        ((CASE qs.statement_end_offset 
          WHEN -1 THEN DATALENGTH(st.text) 
         ELSE qs.statement_end_offset 
         END - qs.statement_start_offset)/2) + 1) AS sql_text,
    DB_NAME(st.dbid) AS database_name,
    CAST(qp.query_plan AS NVARCHAR(MAX)) AS query_plan
FROM sys.dm_exec_query_stats AS qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) AS st
OUTER APPLY sys.dm_exec_query_plan(qs.plan_handle) AS qp
ORDER BY qs.total_worker_time DESC;
"""

# 4. Missing Indexes
MISSING_INDEXES_QUERY = """
SELECT TOP 10
    DB_NAME(mid.database_id) AS database_name,
    OBJECT_SCHEMA_NAME(mid.object_id, mid.database_id) AS schema_name,
    OBJECT_NAME(mid.object_id, mid.database_id) AS table_name,
    mid.equality_columns,
    mid.inequality_columns,
    mid.included_columns,
    migs.user_seeks,
    migs.user_scans,
    migs.avg_total_user_cost,
    migs.avg_user_impact
FROM sys.dm_db_missing_index_group_stats AS migs
INNER JOIN sys.dm_db_missing_index_groups AS mig ON migs.group_handle = mig.index_group_handle
INNER JOIN sys.dm_db_missing_index_details AS mid ON mig.index_handle = mid.index_handle
ORDER BY migs.avg_total_user_cost * migs.avg_user_impact * (migs.user_seeks + migs.user_scans) DESC;
"""

# 5. Index Fragmentation (Limited to recent table updates to avoid heavy scanning)
INDEX_FRAGMENTATION_QUERY = """
SELECT TOP 20
    DB_NAME(ips.database_id) AS database_name,
    OBJECT_SCHEMA_NAME(ips.object_id, ips.database_id) AS schema_name,
    OBJECT_NAME(ips.object_id, ips.database_id) AS table_name,
    i.name AS index_name,
    ips.avg_fragmentation_in_percent AS avg_fragmentation_percent,
    ips.page_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') AS ips
JOIN sys.indexes AS i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.avg_fragmentation_in_percent > 10.0
  AND ips.index_id > 0
ORDER BY ips.avg_fragmentation_in_percent DESC;
"""
