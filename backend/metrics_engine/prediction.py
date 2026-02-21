"""Lightweight prediction utilities — pure Python, no numpy required."""
import math
from typing import List


def compute_trend_slope(values: List[float]) -> float:
    """Compute linear regression slope via least-squares formula.
    
    Returns the slope (change per sample). A positive slope means
    the metric is increasing over time.
    
    Uses the formula: slope = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
    """
    n = len(values)
    if n < 3:
        return 0.0

    sum_x = 0.0
    sum_y = 0.0
    sum_xy = 0.0
    sum_x2 = 0.0

    for i, y in enumerate(values):
        x = float(i)
        sum_x += x
        sum_y += y
        sum_xy += x * y
        sum_x2 += x * x

    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        return 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    return slope


def compute_ewma(values: List[float], alpha: float = 0.3) -> List[float]:
    """Exponentially weighted moving average for noise smoothing.
    
    Args:
        values: Raw time series
        alpha: Smoothing factor (0-1). Higher = more weight on recent.
    """
    if not values:
        return []

    result = [values[0]]
    for v in values[1:]:
        smoothed = alpha * v + (1 - alpha) * result[-1]
        result.append(smoothed)
    return result


def compute_stddev(values: List[float]) -> float:
    """Population standard deviation."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return math.sqrt(variance)
