"""Configuration Audit collector: MAXDOP, memory, parallelism, trace flags."""
from models.metrics import ConfigSnapshot, ConfigSetting
from utils.db import get_db_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

CONFIG_QUERY = """
SELECT name, CAST(value_in_use AS INT) AS value_in_use
FROM sys.configurations
WHERE name IN (
    'max degree of parallelism',
    'cost threshold for parallelism',
    'max server memory (MB)',
    'min server memory (MB)',
    'max worker threads'
);
"""

TEMPDB_FILES_QUERY = """
SELECT COUNT(*) AS file_count FROM tempdb.sys.database_files WHERE type = 0;
"""

TRACE_FLAGS_QUERY = """
DBCC TRACESTATUS(-1) WITH NO_INFOMSGS;
"""

# Known best-practice recommendations
RECOMMENDATIONS = {
    "max degree of parallelism": {
        "check": lambda v, cores: "MAXDOP=0 (unlimited) can cause excessive parallelism" if v == 0 else None,
    },
    "cost threshold for parallelism": {
        "check": lambda v, cores: "Default value 5 is too low for most workloads. Consider 25-50." if v <= 5 else None,
    },
}


def collect_configuration() -> ConfigSnapshot:
    snapshot = ConfigSnapshot()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Core settings
            cursor.execute(CONFIG_QUERY)
            for row in cursor.fetchall():
                name = row.name
                val = row.value_in_use

                warning = None
                rec = RECOMMENDATIONS.get(name)
                if rec:
                    warning = rec["check"](val, 0)

                snapshot.settings.append(ConfigSetting(
                    name=name,
                    value=val,
                    warning=warning,
                ))

            # TempDB file count
            cursor.execute(TEMPDB_FILES_QUERY)
            row = cursor.fetchone()
            snapshot.tempdb_file_count = row.file_count if row else 0

            # Check if tempdb files < CPU cores
            if snapshot.tempdb_file_count < 4:
                snapshot.settings.append(ConfigSetting(
                    name="TempDB Data Files",
                    value=snapshot.tempdb_file_count,
                    recommended="4-8 files matching CPU core count",
                    warning=f"Only {snapshot.tempdb_file_count} TempDB data file(s). Consider adding more.",
                ))

            # Trace flags
            try:
                cursor.execute(TRACE_FLAGS_QUERY)
                for row in cursor.fetchall():
                    if hasattr(row, 'TraceFlag'):
                        snapshot.trace_flags.append(int(row.TraceFlag))
            except Exception:
                pass  # DBCC may not work in all permission contexts

    except Exception as e:
        logger.error(f"Configuration collector error: {e}")
    return snapshot
