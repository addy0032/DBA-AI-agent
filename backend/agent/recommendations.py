from collections import deque
from typing import List, Optional
import threading
from models.api_models import Recommendation
from config.settings import settings

class RecommendationManager:
    def __init__(self, max_len: int = settings.RECOMMENDATION_HISTORY_LIMIT):
        self._recommendations = deque(maxlen=max_len)
        self._lock = threading.Lock()

    def add_recommendation(self, recommendation: Recommendation):
        with self._lock:
            self._recommendations.append(recommendation)

    def get_latest(self) -> Optional[Recommendation]:
        with self._lock:
            if not self._recommendations:
                return None
            return self._recommendations[-1]

    def get_history(self, limit: int = 10) -> List[Recommendation]:
        with self._lock:
            # Return last N elements reversed (newest first is usually helpful)
            return list(self._recommendations)[-limit:][::-1]

    def clear(self):
        with self._lock:
            self._recommendations.clear()

recommendation_manager = RecommendationManager()
