"""Index Health collector: Fragmentation, Missing indexes, Usage stats."""
from models.metrics import IndexSnapshot, FragmentedIndex, MissingIndexDetail
from utils.db import get_db_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

# LIMITED mode — lightweight, safe for frequent polling
FRAGMENTATION_QUERY = """
SELECT TOP 30
    DB_NAME(ips.database_id) AS database_name,
    OBJECT_SCHEMA_NAME(ips.object_id, ips.database_id) AS schema_name,
    OBJECT_NAME(ips.object_id, ips.database_id) AS table_name,
    i.name AS index_name,
    ips.avg_fragmentation_in_percent AS avg_fragmentation_percent,
    ips.page_count,
    ISNULL(ius.user_seeks, 0) AS user_seeks,
    ISNULL(ius.user_scans, 0) AS user_scans,
    ISNULL(ius.user_lookups, 0) AS user_lookups,
    ISNULL(ius.user_updates, 0) AS user_updates
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
LEFT JOIN sys.dm_db_index_usage_stats ius
    ON ips.object_id = ius.object_id AND ips.index_id = ius.index_id AND ips.database_id = ius.database_id
WHERE ips.avg_fragmentation_in_percent > 5.0
  AND ips.index_id > 0
  AND ips.page_count > 100
ORDER BY ips.avg_fragmentation_in_percent DESC;
"""

MISSING_INDEXES_QUERY = """
SELECT TOP 20
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
FROM sys.dm_db_missing_index_group_stats migs
INNER JOIN sys.dm_db_missing_index_groups mig ON migs.group_handle = mig.index_group_handle
INNER JOIN sys.dm_db_missing_index_details mid ON mig.index_handle = mid.index_handle
ORDER BY migs.avg_total_user_cost * migs.avg_user_impact * (migs.user_seeks + migs.user_scans) DESC;
"""


def collect_indexes() -> IndexSnapshot:
    snapshot = IndexSnapshot()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(FRAGMENTATION_QUERY)
            for row in cursor.fetchall():
                snapshot.fragmented.append(FragmentedIndex(
                    database_name=row.database_name,
                    schema_name=row.schema_name,
                    table_name=row.table_name,
                    index_name=row.index_name,
                    avg_fragmentation_percent=float(row.avg_fragmentation_percent or 0),
                    page_count=row.page_count or 0,
                    user_seeks=row.user_seeks or 0,
                    user_scans=row.user_scans or 0,
                    user_lookups=row.user_lookups or 0,
                    user_updates=row.user_updates or 0,
                ))

            cursor.execute(MISSING_INDEXES_QUERY)
            for row in cursor.fetchall():
                seeks = row.user_seeks or 0
                scans = row.user_scans or 0
                cost = row.avg_total_user_cost or 0
                impact = row.avg_user_impact or 0
                snapshot.missing.append(MissingIndexDetail(
                    database_name=row.database_name,
                    schema_name=row.schema_name,
                    table_name=row.table_name,
                    equality_columns=row.equality_columns,
                    inequality_columns=row.inequality_columns,
                    included_columns=row.included_columns,
                    user_seeks=seeks,
                    user_scans=scans,
                    avg_total_user_cost=float(cost),
                    avg_user_impact=float(impact),
                    impact_score=float(seeks * cost * impact),
                ))

    except Exception as e:
        logger.error(f"Index collector error: {e}")
    return snapshot
