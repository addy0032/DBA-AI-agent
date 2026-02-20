from datetime import datetime, timedelta
from typing import Dict
import threading

class AnomalyMemory:
    def __init__(self):
        # Maps anomaly root_resource string to the timestamp it was last alerted
        self._history: Dict[str, datetime] = {}
        self._lock = threading.Lock()
        self.cooldown_minutes = 15

    def should_alert(self, root_resource: str) -> bool:
        with self._lock:
            now = datetime.utcnow()
            if root_resource in self._history:
                last_alert_time = self._history[root_resource]
                if now - last_alert_time < timedelta(minutes=self.cooldown_minutes):
                    return False
            
            self._history[root_resource] = now
            return True

    def clear(self):
        with self._lock:
            self._history.clear()

anomaly_memory = AnomalyMemory()
