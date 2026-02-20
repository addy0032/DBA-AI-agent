from collections import deque
from typing import List, Optional
from models.db_models import MetricSnapshot
from config.settings import settings
import threading

class SnapshotManager:
    def __init__(self, max_len: int = settings.MAX_HISTORY_SNAPSHOTS):
        self._snapshots = deque(maxlen=max_len)
        self._lock = threading.Lock()

    def add_snapshot(self, snapshot: MetricSnapshot):
        with self._lock:
            self._snapshots.append(snapshot)

    def get_latest(self) -> Optional[MetricSnapshot]:
        with self._lock:
            if not self._snapshots:
                return None
            return self._snapshots[-1]

    def get_history(self, count: int = 10) -> List[MetricSnapshot]:
        with self._lock:
            return list(self._snapshots)[-count:]

snapshot_manager = SnapshotManager()
