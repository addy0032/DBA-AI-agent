import time
import threading
from pyodbc import Row
from utils.logger import setup_logger
from utils.db import get_db_connection
from config.settings import settings
from data_collection.queries import (
    ACTIVE_SESSIONS_QUERY,
    ACTIVE_REQUESTS_COUNT_QUERY,
    WAIT_STATS_QUERY,
    EXPENSIVE_QUERIES_QUERY,
    MISSING_INDEXES_QUERY,
    INDEX_FRAGMENTATION_QUERY
)
from models.db_models import (
    MetricSnapshot, BlockingSession, WaitStatSummary, 
    QueryStat, MissingIndex, IndexHealth
)
from data_collection.snapshot import snapshot_manager
import re

logger = setup_logger(__name__)

class DataCollector:
    def __init__(self):
        self.is_running = False
        self._thread = None

    def _row_to_dict(self, row: Row) -> dict:
        return dict(zip([t[0] for t in row.cursor_description], row))

    def collect_now(self) -> MetricSnapshot | None:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Active Sessions Count
                cursor.execute(ACTIVE_REQUESTS_COUNT_QUERY)
                active_count = cursor.fetchone()[0]
                
                # Blocking Tree
                cursor.execute(ACTIVE_SESSIONS_QUERY)
                blocking_chains = [BlockingSession(**self._row_to_dict(row)) for row in cursor.fetchall()]

                # Wait Stats
                cursor.execute(WAIT_STATS_QUERY)
                wait_stats = [WaitStatSummary(**self._row_to_dict(row)) for row in cursor.fetchall()]

                # Expensive Queries with Plan Summarization
                cursor.execute(EXPENSIVE_QUERIES_QUERY)
                expensive_queries = []
                for row in cursor.fetchall():
                    row_dict = self._row_to_dict(row)
                    plan_xml = row_dict.get('query_plan')
                    
                    has_table_scan = False
                    estimated_cost = 0.0
                    
                    if plan_xml:
                        has_table_scan = "TableScan" in plan_xml or "LogicalOp=\"Table Scan\"" in plan_xml
                        
                        # Lightweight regex to extract StatementSubTreeCost
                        # Match: StatementSubTreeCost="45.24"
                        cost_match = re.search(r'StatementSubTreeCost="([^"]+)"', plan_xml)
                        if cost_match:
                            try:
                                estimated_cost = float(cost_match.group(1))
                            except ValueError:
                                pass
                                
                        # We clear the massive XML out before saving to save memory and token limits later
                        row_dict['query_plan'] = None 
                        
                    row_dict['has_table_scan'] = has_table_scan
                    row_dict['estimated_cost'] = estimated_cost
                    expensive_queries.append(QueryStat(**row_dict))

                # Missing Indexes
                cursor.execute(MISSING_INDEXES_QUERY)
                missing_indexes = [MissingIndex(**self._row_to_dict(row)) for row in cursor.fetchall()]

                # Index Fragmentation
                cursor.execute(INDEX_FRAGMENTATION_QUERY)
                index_health = [IndexHealth(**self._row_to_dict(row)) for row in cursor.fetchall()]

                snapshot = MetricSnapshot(
                    active_sessions_count=active_count,
                    blocking_chains=blocking_chains,
                    top_wait_stats=wait_stats,
                    expensive_queries=expensive_queries,
                    missing_indexes=missing_indexes,
                    index_health=index_health
                )
                return snapshot
        except Exception as e:
            logger.error(f"Error during data collection: {e}")
            return None

    def _poll_loop(self):
        logger.info("Started background data collection poller.")
        while self.is_running:
            snapshot = self.collect_now()
            if snapshot:
                snapshot_manager.add_snapshot(snapshot)
                logger.debug("Captured new metric snapshot.")
            time.sleep(settings.POLL_INTERVAL_SECONDS)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread:
            self._thread.join()

collector = DataCollector()
