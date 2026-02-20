"""Delta computation utilities for cumulative SQL Server metrics."""
from typing import Dict, Optional
from datetime import datetime, timezone


class DeltaTracker:
    """Tracks previous cumulative values and computes deltas between polls."""

    def __init__(self):
        self._previous: Dict[str, Dict[str, float]] = {}
        self._previous_timestamp: Optional[datetime] = None

    def compute_delta(
        self,
        domain: str,
        key: str,
        current_value: float,
        current_timestamp: datetime
    ) -> float:
        """Return the delta between current and previous value for a given key."""
        compound_key = f"{domain}:{key}"

        if compound_key not in self._previous:
            self._previous[compound_key] = {}

        prev = self._previous[compound_key].get("value")
        self._previous[compound_key]["value"] = current_value

        if prev is None:
            return 0.0

        delta = current_value - prev
        # Cumulative counters can reset on server restart
        return max(0.0, delta)

    def get_elapsed_seconds(self, current_timestamp: datetime) -> float:
        """Seconds elapsed since the last poll."""
        if self._previous_timestamp is None:
            self._previous_timestamp = current_timestamp
            return 0.0

        elapsed = (current_timestamp - self._previous_timestamp).total_seconds()
        self._previous_timestamp = current_timestamp
        return max(elapsed, 0.001)  # avoid division by zero

    def reset(self):
        self._previous.clear()
        self._previous_timestamp = None


# Singleton used across collectors
delta_tracker = DeltaTracker()
