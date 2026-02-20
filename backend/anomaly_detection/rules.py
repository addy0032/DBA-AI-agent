# Thresholds for Anomaly Detection
class AnomalyRules:
    BLOCKING_WAIT_TIME_MS_THRESHOLD = 5000  # 5 seconds
    COMPILING_OR_CPU_HIGH_WORKER_TIME = 1000000 # ~1 sec CPU time
    HIGH_WAIT_TIME_THRESHOLD_MS = 10000
    INDEX_FRAGMENTATION_CRITICAL_PCT = 30.0
    INDEX_FRAGMENTATION_WARNING_PCT = 15.0
    MISSING_INDEX_IMPACT_THRESHOLD = 100000.0 # user_seeks * avg_total_user_cost * avg_user_impact
