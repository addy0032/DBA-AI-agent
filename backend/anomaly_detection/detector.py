import uuid
from typing import List, Dict
import math
from models.db_models import MetricSnapshot, Anomaly, AnomalyType, SeverityLevel, BlockingSession
from anomaly_detection.rules import AnomalyRules
from config.settings import settings

class AnomalyDetector:
    def _calculate_severity(self, weights: int) -> SeverityLevel:
        if weights >= 8:
            return SeverityLevel.CRITICAL
        elif weights >= 4:
            return SeverityLevel.WARNING
        return SeverityLevel.INFO

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

                severity_weight = 5
                if block.wait_time_ms is not None and block.wait_time_ms > 30000:
                    severity_weight += 3
                if intervals_persisted >= settings.BASELINE_WINDOW_SIZE:
                    severity_weight += 5

                if block.wait_time_ms is not None and block.wait_time_ms > AnomalyRules.BLOCKING_WAIT_TIME_MS_THRESHOLD:
                    context = block.model_dump()
                    context["intervals_persisted"] = intervals_persisted
                    context["is_head_blocker"] = is_head
                    context["anomaly_score"] = severity_weight
                    
                    anomalies.append(Anomaly(
                        id=str(uuid.uuid4()),
                        type=AnomalyType.BLOCKING,
                        severity=self._calculate_severity(severity_weight),
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
            severity_weight = 0
            is_anomaly = False
            reason = []

            if q.total_worker_time > AnomalyRules.COMPILING_OR_CPU_HIGH_WORKER_TIME:
                is_anomaly = True
                severity_weight += 2
                reason.append("Absolute CPU threshold exceeded")

            # Z-Score Regression Math
            hist_worker_times = query_history.get(q.query_hash, [])
            if len(hist_worker_times) > 1:
                n = len(hist_worker_times)
                mean = sum(hist_worker_times) / n
                variance = sum((x - mean) ** 2 for x in hist_worker_times) / (n - 1)
                std_dev = math.sqrt(variance)

                # Avoid division by zero
                std_dev = max(std_dev, 1.0)
                mean = max(mean, 1.0)

                z_score = (q.total_worker_time - mean) / std_dev
                regression_multiplier = q.total_worker_time / mean
                
                if z_score > settings.CPU_ZSCORE_THRESHOLD and regression_multiplier > settings.QUERY_REGRESSION_STD_MULTIPLIER:
                    is_anomaly = True
                    severity_weight += 4
                    reason.append(f"Z-Score {z_score:.2f} (Spike x{regression_multiplier:.1f} vs baseline {mean:.0f})")

            if is_anomaly:
                context = q.model_dump()
                context["regression_reasons"] = reason
                context["anomaly_score"] = severity_weight
                anomalies.append(Anomaly(
                    id=str(uuid.uuid4()),
                    type=AnomalyType.HIGH_CPU,
                    severity=self._calculate_severity(severity_weight),
                    root_resource=f"Query {q.query_hash}",
                    context_data=context
                ))

        # 3. Wait Stats Spikes (Delta-based Modeling)
        # We need the direct previous snapshot for cumulative delta
        if history:
            prev_snapshot = history[-1]
            prev_wait_map = {w.wait_type: w.wait_time_ms for w in prev_snapshot.top_wait_stats}
            
            # Calculate total delta across all waits to find dominance
            total_delta_ms = 0
            delta_map = {}
            for w in current_snapshot.top_wait_stats:
                prev_val = prev_wait_map.get(w.wait_type, w.wait_time_ms)
                # Ensure no negative deltas if server restarted
                delta = max(0, w.wait_time_ms - prev_val)
                delta_map[w.wait_type] = delta
                total_delta_ms += delta
                
            elapsed_seconds = max((current_snapshot.timestamp - prev_snapshot.timestamp).total_seconds(), 1.0)
                
            for w in current_snapshot.top_wait_stats:
                is_anomaly = False
                severity_weight = 0
                reason = []
                
                delta_ms = delta_map.get(w.wait_type, 0)
                wait_rate_per_sec = delta_ms / elapsed_seconds
                dominance_pct = (delta_ms / total_delta_ms * 100) if total_delta_ms > 0 else 0
                
                if wait_rate_per_sec > settings.WAIT_RATE_THRESHOLD_PER_SEC and dominance_pct > settings.WAIT_DOMINANCE_PERCENT_THRESHOLD:
                    is_anomaly = True
                    severity_weight += 4
                    reason.append(f"Wait Rate {wait_rate_per_sec:.0f} ms/sec ({dominance_pct:.1f}% dominance)")

                if is_anomaly:
                    context = w.model_dump()
                    context["spike_reasons"] = reason
                    context["delta_ms"] = delta_ms
                    context["rate_ms_per_sec"] = wait_rate_per_sec
                    context["dominance_pct"] = dominance_pct
                    context["anomaly_score"] = severity_weight
                    
                    anomalies.append(Anomaly(
                        id=str(uuid.uuid4()),
                        type=AnomalyType.HIGH_WAITS,
                        severity=self._calculate_severity(severity_weight),
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

        # 6. Parameter Sniffing Detection (from MetricsEngine QS snapshot)
        try:
            from metrics_engine.engine import metrics_engine
            qs_snapshot = metrics_engine.get_current("query_store")
            if qs_snapshot and hasattr(qs_snapshot, "parameter_sniffing_candidates"):
                for candidate in qs_snapshot.parameter_sniffing_candidates:
                    if candidate.suspected:
                        # Severity scales with variance ratio
                        if candidate.variance_ratio > 10:
                            severity_weight = 9  # CRITICAL
                        elif candidate.variance_ratio > 5:
                            severity_weight = 5  # WARNING
                        else:
                            severity_weight = 3  # INFO

                        context = candidate.model_dump()
                        context["anomaly_score"] = severity_weight
                        context["detection_method"] = "plan_variance_analysis"

                        anomalies.append(Anomaly(
                            id=str(uuid.uuid4()),
                            type=AnomalyType.PARAMETER_SNIFFING,
                            severity=self._calculate_severity(severity_weight),
                            root_resource=f"Query {candidate.query_id} ({candidate.plan_count} plans, {candidate.variance_ratio:.1f}x variance)",
                            context_data=context
                        ))
        except Exception as e:
            pass  # MetricsEngine may not be initialized yet

        # 7. Predictive Query Degradation (trend slope on historical duration)
        try:
            from metrics_engine.prediction import compute_trend_slope, compute_ewma

            for q in current_snapshot.expensive_queries:
                hist_durations: list[float] = []
                for snap in history:
                    for old_q in snap.expensive_queries:
                        if old_q.query_hash == q.query_hash:
                            hist_durations.append(float(old_q.total_elapsed_time))

                if len(hist_durations) >= settings.PREDICTION_MIN_HISTORY_POINTS:
                    # Smooth with EWMA first to reduce noise
                    smoothed = compute_ewma(hist_durations, alpha=0.3)
                    slope = compute_trend_slope(smoothed)

                    if slope > settings.PREDICTION_SLOPE_THRESHOLD:
                        # Accelerating = slope of the second half > first half
                        mid = len(smoothed) // 2
                        slope_first = compute_trend_slope(smoothed[:mid]) if mid >= 3 else 0
                        slope_second = compute_trend_slope(smoothed[mid:]) if len(smoothed) - mid >= 3 else slope
                        is_accelerating = slope_second > slope_first * 1.2

                        severity_weight = 6 if is_accelerating else 4

                        anomalies.append(Anomaly(
                            id=str(uuid.uuid4()),
                            type=AnomalyType.PREDICTED_REGRESSION,
                            severity=self._calculate_severity(severity_weight),
                            root_resource=f"Query {q.query_hash}",
                            context_data={
                                "slope": round(slope, 2),
                                "slope_first_half": round(slope_first, 2),
                                "slope_second_half": round(slope_second, 2),
                                "is_accelerating": is_accelerating,
                                "history_points": len(hist_durations),
                                "current_elapsed_time": q.total_elapsed_time,
                                "sql_text": q.sql_text[:300],
                                "anomaly_score": severity_weight,
                            }
                        ))
        except Exception as e:
            pass  # prediction module may not be available

        return anomalies

detector = AnomalyDetector()
