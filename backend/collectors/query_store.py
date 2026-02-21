"""Query Store collector: Regressed queries, forced plans, parameter sniffing (graceful if disabled)."""
import math
from collections import defaultdict
from models.metrics import (
    QueryStoreSnapshot, RegressedQuery,
    ParameterSniffingCandidate, PlanPerformance
)
from config.settings import settings
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

# Per-plan performance for parameter sniffing detection.
# Only queries with 2+ distinct plans and meaningful execution counts.
PLAN_VARIANCE_QUERY = """
SELECT
    q.query_id,
    SUBSTRING(qt.query_sql_text, 1, 500) AS query_text,
    p.plan_id,
    AVG(rs.avg_duration) AS avg_duration_us,
    AVG(rs.avg_cpu_time) AS avg_cpu_time_us,
    SUM(rs.count_executions) AS execution_count
FROM sys.query_store_query q
JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
JOIN sys.query_store_plan p ON q.query_id = p.query_id
JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
WHERE rs.count_executions > 0
GROUP BY q.query_id, qt.query_sql_text, p.plan_id
HAVING SUM(rs.count_executions) >= 2;
"""


def _analyze_parameter_sniffing(cursor) -> list[ParameterSniffingCandidate]:
    """Group per-plan stats by query and compute variance metrics."""
    candidates = []

    try:
        cursor.execute(PLAN_VARIANCE_QUERY)
        rows = cursor.fetchall()
    except Exception as e:
        logger.warning(f"Parameter sniffing query failed: {e}")
        return candidates

    # SQL patterns from our own collectors — exclude from sniffing analysis
    _SELF_QUERY_PATTERNS = (
        "sys.dm_db_index_physical_stats",
        "sys.dm_os_schedulers",
        "sys.dm_os_wait_stats",
        "sys.dm_exec_requests",
        "sys.dm_io_virtual_file_stats",
        "sys.query_store",
        "sys.dm_os_performance_counters",
        "blocking_session_id",
        "BlockingTree",
    )

    query_plans: dict[int, dict] = defaultdict(lambda: {"text": "", "plans": []})
    for row in rows:
        qid = row.query_id
        sql_text = (row.query_text or "")[:500]

        # Skip our own monitoring queries
        if any(pat in sql_text for pat in _SELF_QUERY_PATTERNS):
            continue

        query_plans[qid]["text"] = sql_text
        query_plans[qid]["plans"].append(PlanPerformance(
            plan_id=row.plan_id,
            avg_duration_us=float(row.avg_duration_us or 0),
            avg_cpu_time_us=float(row.avg_cpu_time_us or 0),
            execution_count=int(row.execution_count or 0),
        ))

    variance_threshold = settings.PARAM_SNIFFING_VARIANCE_RATIO
    stddev_threshold = settings.PARAM_SNIFFING_MIN_STDDEV

    for qid, data in query_plans.items():
        plans = data["plans"]
        if len(plans) < 2:
            continue

        durations = [p.avg_duration_us for p in plans]
        mean_dur = sum(durations) / len(durations)
        max_dur = max(durations)
        min_dur = min(durations)

        # Variance ratio: how different is the worst plan vs the best?
        variance_ratio = max_dur / min_dur if min_dur > 0 else 0.0

        # Standard deviation of per-plan average durations
        if len(durations) > 1:
            variance = sum((d - mean_dur) ** 2 for d in durations) / len(durations)
            stddev = math.sqrt(variance)
        else:
            stddev = 0.0

        suspected = (
            len(plans) >= 2
            and variance_ratio > variance_threshold
            and stddev > stddev_threshold
        )

        candidates.append(ParameterSniffingCandidate(
            query_id=qid,
            query_text=data["text"],
            plan_count=len(plans),
            plans=plans,
            duration_mean_us=mean_dur,
            duration_stddev_us=stddev,
            max_avg_duration_us=max_dur,
            min_avg_duration_us=min_dur,
            variance_ratio=round(variance_ratio, 2),
            suspected=suspected,
        ))

    # Sort by variance ratio descending, limit to top 15
    candidates.sort(key=lambda c: c.variance_ratio, reverse=True)
    return candidates[:15]


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

            # Parameter Sniffing Detection
            snapshot.parameter_sniffing_candidates = _analyze_parameter_sniffing(cursor)

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
