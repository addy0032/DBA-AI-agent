"""Query Store collector: Regressed queries, forced plans (graceful if disabled)."""
from models.metrics import QueryStoreSnapshot, RegressedQuery
from utils.db import get_db_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Check if Query Store is enabled on the current database
QS_ENABLED_CHECK = """
SELECT
    CASE WHEN actual_state_desc IS NOT NULL AND actual_state_desc <> 'OFF'
         THEN 1 ELSE 0 END AS is_enabled
FROM sys.database_query_store_options;
"""

REGRESSED_QUERIES = """
SELECT TOP 10
    q.query_id,
    SUBSTRING(qt.query_sql_text, 1, 500) AS query_text,
    rs_recent.avg_duration AS recent_avg_duration_us,
    rs_hist.avg_duration AS historical_avg_duration_us,
    CASE WHEN rs_hist.avg_duration > 0
         THEN ((rs_recent.avg_duration - rs_hist.avg_duration) / rs_hist.avg_duration) * 100
         ELSE 0 END AS regression_pct,
    rs_recent.count_executions AS execution_count,
    (SELECT COUNT(DISTINCT plan_id) FROM sys.query_store_plan WHERE query_id = q.query_id) AS plan_count
FROM sys.query_store_query q
JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
CROSS APPLY (
    SELECT TOP 1 avg_duration, count_executions
    FROM sys.query_store_runtime_stats rs
    JOIN sys.query_store_plan p ON rs.plan_id = p.plan_id
    WHERE p.query_id = q.query_id
    ORDER BY rs.last_execution_time DESC
) rs_recent
CROSS APPLY (
    SELECT AVG(avg_duration) AS avg_duration
    FROM sys.query_store_runtime_stats rs
    JOIN sys.query_store_plan p ON rs.plan_id = p.plan_id
    WHERE p.query_id = q.query_id
) rs_hist
WHERE rs_recent.avg_duration > rs_hist.avg_duration * 1.5
ORDER BY regression_pct DESC;
"""

FORCED_PLAN_COUNT = """
SELECT COUNT(*) AS cnt FROM sys.query_store_plan WHERE is_forced_plan = 1;
"""

TOTAL_PLANS = """
SELECT COUNT(*) AS cnt FROM sys.query_store_plan;
"""


def collect_query_store() -> QueryStoreSnapshot:
    snapshot = QueryStoreSnapshot()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Graceful check — if QS is off, return empty
            try:
                cursor.execute(QS_ENABLED_CHECK)
                row = cursor.fetchone()
                if not row or row.is_enabled == 0:
                    snapshot.is_enabled = False
                    return snapshot
                snapshot.is_enabled = True
            except Exception:
                snapshot.is_enabled = False
                return snapshot

            # Regressed queries
            try:
                cursor.execute(REGRESSED_QUERIES)
                for row in cursor.fetchall():
                    snapshot.regressed_queries.append(RegressedQuery(
                        query_id=row.query_id or 0,
                        query_text=(row.query_text or "")[:500],
                        recent_avg_duration_us=float(row.recent_avg_duration_us or 0),
                        historical_avg_duration_us=float(row.historical_avg_duration_us or 0),
                        regression_pct=float(row.regression_pct or 0),
                        execution_count=row.execution_count or 0,
                        plan_count=row.plan_count or 0,
                    ))
            except Exception as e:
                logger.warning(f"Query store regression query failed: {e}")

            # Forced plans
            try:
                cursor.execute(FORCED_PLAN_COUNT)
                row = cursor.fetchone()
                snapshot.forced_plan_count = row.cnt if row else 0
            except Exception:
                pass

            # Total plans
            try:
                cursor.execute(TOTAL_PLANS)
                row = cursor.fetchone()
                snapshot.total_plans_tracked = row.cnt if row else 0
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Query Store collector error: {e}")
    return snapshot
