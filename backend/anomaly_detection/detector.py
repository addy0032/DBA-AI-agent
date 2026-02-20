import uuid
from typing import List, Dict
from models.db_models import MetricSnapshot, Anomaly, AnomalyType, SeverityLevel, BlockingSession
from anomaly_detection.rules import AnomalyRules
from config.settings import settings

class AnomalyDetector:
    def detect(self, current_snapshot: MetricSnapshot, history: List[MetricSnapshot]) -> List[Anomaly]:
        anomalies = []

        # 1. Blocking Anomalies & Head Blocker Resolution
        if current_snapshot.blocking_chains:
            # Find the head blocker (a blocking_session_id not in any session_id)
            all_sessions = {b.session_id for b in current_snapshot.blocking_chains}
            blocking_sessions = {b.blocking_session_id for b in current_snapshot.blocking_chains}
            head_blockers = blocking_sessions - all_sessions
            
            for block in current_snapshot.blocking_chains:
                is_head = block.blocking_session_id in head_blockers
                
                # Baseline: Has this identical blocking relationship persisted?
                intervals_persisted = 0
                for old_snap in reversed(history):
                    if any(b.session_id == block.session_id and b.blocking_session_id == block.blocking_session_id for b in old_snap.blocking_chains):
                        intervals_persisted += 1
                    else:
                        break

                severity = SeverityLevel.WARNING
                if block.wait_time_ms is not None and block.wait_time_ms > 30000:
                    severity = SeverityLevel.CRITICAL
                elif intervals_persisted > settings.BASELINE_WINDOW_SIZE:
                    severity = SeverityLevel.CRITICAL

                if block.wait_time_ms is not None and block.wait_time_ms > AnomalyRules.BLOCKING_WAIT_TIME_MS_THRESHOLD:
                    context = block.model_dump()
                    context["intervals_persisted"] = intervals_persisted
                    context["is_head_blocker"] = block.session_id in head_blockers
                    
                    anomalies.append(Anomaly(
                        id=str(uuid.uuid4()),
                        type=AnomalyType.BLOCKING,
                        severity=severity,
                        root_resource=f"Session {block.session_id} blocked by {block.blocking_session_id}",
                        context_data=context
                    ))

        # 2. Expensive Queries (High CPU / Regression)
        # Build history maps for query_hash
        query_history: Dict[str, List[int]] = {}
        for snap in history:
            for q in snap.expensive_queries:
                if q.query_hash not in query_history:
                    query_history[q.query_hash] = []
                query_history[q.query_hash].append(q.total_worker_time)

        for q in current_snapshot.expensive_queries:
            # Basic Threshold
            is_anomaly = False
            severity = SeverityLevel.WARNING
            reason = []

            if q.total_worker_time > AnomalyRules.COMPILING_OR_CPU_HIGH_WORKER_TIME:
                is_anomaly = True
                reason.append("Absolute CPU threshold exceeded")

            # Baseline Regression
            hist_worker_times = query_history.get(q.query_hash, [])
            if hist_worker_times:
                avg_hist_time = sum(hist_worker_times) / len(hist_worker_times)
                if avg_hist_time > 0 and (q.total_worker_time / avg_hist_time) > settings.QUERY_REGRESSION_MULTIPLIER:
                    is_anomaly = True
                    reason.append(f"Worker time Spike! {q.total_worker_time} vs baseline {avg_hist_time:.0f}")
                    if (q.total_worker_time / avg_hist_time) > (settings.QUERY_REGRESSION_MULTIPLIER * 2):
                        severity = SeverityLevel.CRITICAL

            if is_anomaly:
                context = q.model_dump()
                context["regression_reasons"] = reason
                anomalies.append(Anomaly(
                    id=str(uuid.uuid4()),
                    type=AnomalyType.HIGH_CPU,
                    severity=severity,
                    root_resource=f"Query {q.query_hash}",
                    context_data=context
                ))

        # 3. Wait Stats Spikes (Baseline Delta)
        wait_history: Dict[str, List[int]] = {}
        for snap in history:
            for w in snap.top_wait_stats:
                if w.wait_type not in wait_history:
                    wait_history[w.wait_type] = []
                wait_history[w.wait_type].append(w.wait_time_ms)

        for w in current_snapshot.top_wait_stats:
            is_anomaly = False
            severity = SeverityLevel.WARNING
            reason = []

            if w.wait_time_ms > AnomalyRules.HIGH_WAIT_TIME_THRESHOLD_MS:
                is_anomaly = True
                reason.append("Absolute threshold exceeded")

            hist_waits = wait_history.get(w.wait_type, [])
            if hist_waits:
                avg_wait = sum(hist_waits) / len(hist_waits)
                if avg_wait > 0 and (w.wait_time_ms / avg_wait) > settings.WAIT_SPIKE_MULTIPLIER:
                    is_anomaly = True
                    reason.append(f"Wait spike! {w.wait_time_ms} vs baseline {avg_wait:.0f}")

            if is_anomaly:
                context = w.model_dump()
                context["spike_reasons"] = reason
                anomalies.append(Anomaly(
                    id=str(uuid.uuid4()),
                    type=AnomalyType.HIGH_WAITS,
                    severity=severity,
                    root_resource=f"WaitType {w.wait_type}",
                    context_data=context
                ))

        # 4. Missing Indexes (Static rule is fine)
        for mi in current_snapshot.missing_indexes:
            impact_score = mi.user_seeks * mi.avg_total_user_cost * mi.avg_user_impact
            if impact_score > AnomalyRules.MISSING_INDEX_IMPACT_THRESHOLD:
                anomalies.append(Anomaly(
                    id=str(uuid.uuid4()),
                    type=AnomalyType.MISSING_INDEX,
                    severity=SeverityLevel.INFO,
                    root_resource=f"Table {mi.database_name}.{mi.schema_name}.{mi.table_name}",
                    context_data=mi.model_dump()
                ))

        # 5. Index Fragmentation (Static rule is fine)
        for ix in current_snapshot.index_health:
            if ix.avg_fragmentation_percent >= AnomalyRules.INDEX_FRAGMENTATION_CRITICAL_PCT:
                anomalies.append(Anomaly(
                    id=str(uuid.uuid4()),
                    type=AnomalyType.INDEX_FRAGMENTATION,
                    severity=SeverityLevel.WARNING,
                    root_resource=f"Index {ix.index_name} on {ix.table_name}",
                    context_data=ix.model_dump()
                ))
            elif ix.avg_fragmentation_percent >= AnomalyRules.INDEX_FRAGMENTATION_WARNING_PCT:
                anomalies.append(Anomaly(
                    id=str(uuid.uuid4()),
                    type=AnomalyType.INDEX_FRAGMENTATION,
                    severity=SeverityLevel.INFO,
                    root_resource=f"Index {ix.index_name} on {ix.table_name}",
                    context_data=ix.model_dump()
                ))

        return anomalies

detector = AnomalyDetector()
