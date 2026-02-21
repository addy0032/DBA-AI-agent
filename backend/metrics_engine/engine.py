"""Central Metrics Engine with tiered polling and rolling window storage."""
import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from collections import deque

from collectors.cpu import collect_cpu
from collectors.memory import collect_memory
from collectors.waits import collect_waits
from collectors.workload import collect_sessions, collect_blocking, collect_queries
from collectors.io_storage import collect_io
from collectors.indexes import collect_indexes
from collectors.query_store import collect_query_store
from collectors.databases import collect_databases
from collectors.configuration import collect_configuration
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Maximum history snapshots to retain per domain
MAX_HISTORY = 120  # ~10 min at 5s intervals


class MetricsEngine:
    """Coordinates all collectors with tiered polling intervals."""

    def __init__(self):
        self._lock = threading.Lock()
        self._running = False

        # Latest snapshots (current state)
        self._current: Dict[str, Any] = {}

        # Historical rolling windows per domain
        self._history: Dict[str, deque] = {
            "cpu": deque(maxlen=MAX_HISTORY),
            "memory": deque(maxlen=MAX_HISTORY),
            "waits": deque(maxlen=MAX_HISTORY),
            "sessions": deque(maxlen=MAX_HISTORY),
            "blocking": deque(maxlen=MAX_HISTORY),
            "queries": deque(maxlen=MAX_HISTORY),
            "io": deque(maxlen=60),
            "indexes": deque(maxlen=20),
            "query_store": deque(maxlen=20),
            "databases": deque(maxlen=20),
            "configuration": deque(maxlen=10),
        }

        self._threads: list[threading.Thread] = []
        self._fast_interval = getattr(settings, "FAST_POLL_SECONDS", 5)
        self._medium_interval = getattr(settings, "MEDIUM_POLL_SECONDS", 30)
        self._slow_interval = getattr(settings, "SLOW_POLL_SECONDS", 300)

    def start(self):
        if self._running:
            return
        self._running = True
        logger.info("MetricsEngine starting tiered polling...")

        # Fast tier: CPU, Sessions, Blocking, Waits, Queries
        t_fast = threading.Thread(target=self._poll_fast, daemon=True, name="poll-fast")
        # Medium tier: Memory, I/O
        t_medium = threading.Thread(target=self._poll_medium, daemon=True, name="poll-medium")
        # Slow tier: Indexes, Query Store, Databases, Configuration
        t_slow = threading.Thread(target=self._poll_slow, daemon=True, name="poll-slow")

        self._threads = [t_fast, t_medium, t_slow]
        for t in self._threads:
            t.start()

    def stop(self):
        self._running = False
        logger.info("MetricsEngine stopped.")

    # ── Fast Tier (5s) ──────────────────────────────────────────
    def _poll_fast(self):
        # Initial delay to let the DB settle
        time.sleep(1)
        while self._running:
            try:
                cpu = collect_cpu()
                sessions = collect_sessions()
                blocking = collect_blocking()
                waits = collect_waits()
                queries = collect_queries()

                with self._lock:
                    self._current["cpu"] = cpu
                    self._current["sessions"] = sessions
                    self._current["blocking"] = blocking
                    self._current["waits"] = waits
                    self._current["queries"] = queries

                    self._history["cpu"].append(cpu)
                    self._history["sessions"].append(sessions)
                    self._history["blocking"].append(blocking)
                    self._history["waits"].append(waits)
                    self._history["queries"].append(queries)

            except Exception as e:
                logger.error(f"Fast poll error: {e}")

            time.sleep(self._fast_interval)

    # ── Medium Tier (30s) ───────────────────────────────────────
    def _poll_medium(self):
        time.sleep(2)
        while self._running:
            try:
                memory = collect_memory()
                io = collect_io()

                with self._lock:
                    self._current["memory"] = memory
                    self._current["io"] = io

                    self._history["memory"].append(memory)
                    self._history["io"].append(io)

            except Exception as e:
                logger.error(f"Medium poll error: {e}")

            time.sleep(self._medium_interval)

    # ── Slow Tier (5 min) ───────────────────────────────────────
    def _poll_slow(self):
        time.sleep(3)
        while self._running:
            try:
                indexes = collect_indexes()
                qs = collect_query_store()
                dbs = collect_databases()
                config = collect_configuration()

                with self._lock:
                    self._current["indexes"] = indexes
                    self._current["query_store"] = qs
                    self._current["databases"] = dbs
                    self._current["configuration"] = config

                    self._history["indexes"].append(indexes)
                    self._history["query_store"].append(qs)
                    self._history["databases"].append(dbs)
                    self._history["configuration"].append(config)

            except Exception as e:
                logger.error(f"Slow poll error: {e}")

            time.sleep(self._slow_interval)

    # ── Public Accessors ────────────────────────────────────────
    def get_current(self, domain: str) -> Optional[Any]:
        with self._lock:
            return self._current.get(domain)

    def get_history(self, domain: str, count: int = 20) -> list:
        with self._lock:
            history = self._history.get(domain, deque())
            return list(history)[-count:]

    def get_all_current(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._current)

    def force_refresh_all(self) -> None:
        """Run ALL collectors once immediately (bypasses timer intervals)."""
        logger.info("Force refreshing all collectors...")
        try:
            cpu = collect_cpu()
            sessions = collect_sessions()
            blocking = collect_blocking()
            waits = collect_waits()
            queries = collect_queries()
            memory = collect_memory()
            io = collect_io()
            indexes = collect_indexes()
            qs = collect_query_store()
            dbs = collect_databases()
            config = collect_configuration()

            with self._lock:
                self._current["cpu"] = cpu
                self._current["sessions"] = sessions
                self._current["blocking"] = blocking
                self._current["waits"] = waits
                self._current["queries"] = queries
                self._current["memory"] = memory
                self._current["io"] = io
                self._current["indexes"] = indexes
                self._current["query_store"] = qs
                self._current["databases"] = dbs
                self._current["configuration"] = config

                self._history["cpu"].append(cpu)
                self._history["sessions"].append(sessions)
                self._history["blocking"].append(blocking)
                self._history["waits"].append(waits)
                self._history["queries"].append(queries)
                self._history["memory"].append(memory)
                self._history["io"].append(io)
                self._history["indexes"].append(indexes)
                self._history["query_store"].append(qs)
                self._history["databases"].append(dbs)
                self._history["configuration"].append(config)

            logger.info("Force refresh complete.")
        except Exception as e:
            logger.error(f"Force refresh error: {e}")

    def reset_history(self) -> None:
        """Clear all cached snapshots and history (used when switching databases)."""
        with self._lock:
            self._current.clear()
            for dq in self._history.values():
                dq.clear()
        logger.info("MetricsEngine history cleared.")


# Singleton
metrics_engine = MetricsEngine()
