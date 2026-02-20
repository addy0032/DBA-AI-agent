export type SeverityLevel = "INFO" | "WARNING" | "CRITICAL";

export type AnomalyType =
    | "BLOCKING"
    | "HIGH_CPU"
    | "HIGH_MEMORY"
    | "MISSING_INDEX"
    | "LONG_RUNNING_QUERY"
    | "HIGH_WAITS"
    | "INDEX_FRAGMENTATION";

export interface BlockingSession {
    session_id: number;
    blocking_session_id: number;
    wait_type?: string;
    wait_time_ms: number;
    status: string;
    command: string;
    sql_text?: string;
    database_name?: string;
    host_name?: string;
    program_name?: string;
}

export interface WaitStatSummary {
    wait_type: string;
    waiting_tasks_count: number;
    wait_time_ms: number;
    max_wait_time_ms: number;
    signal_wait_time_ms: number;
}

export interface QueryStat {
    query_hash: string;
    execution_count: number;
    total_worker_time: number;
    total_logical_reads: number;
    total_elapsed_time: number;
    sql_text: string;
    database_name?: string;
    query_plan?: string;
    has_table_scan: boolean;
    estimated_cost: number;
}

export interface IndexHealth {
    database_name?: string;
    schema_name?: string;
    table_name?: string;
    index_name?: string;
    avg_fragmentation_percent: number;
    page_count: number;
}

export interface MissingIndex {
    database_name?: string;
    schema_name?: string;
    table_name?: string;
    equality_columns?: string;
    inequality_columns?: string;
    included_columns?: string;
    user_seeks: number;
    user_scans: number;
    avg_total_user_cost: number;
    avg_user_impact: number;
}

export interface MetricSnapshot {
    timestamp: string;
    active_sessions_count: number;
    blocking_chains: BlockingSession[];
    top_wait_stats: WaitStatSummary[];
    expensive_queries: QueryStat[];
    index_health: IndexHealth[];
    missing_indexes: MissingIndex[];
}

export interface Anomaly {
    id: string;
    type: AnomalyType;
    severity: SeverityLevel;
    root_resource: string;
    context_data: Record<string, any>;
    timestamp: string;
}

export interface RecommendationAction {
    action_type: string;
    description: string;
    sql_statement?: string;
}

export interface Recommendation {
    issue_summary: string;
    technical_diagnosis: string;
    recommended_actions: RecommendationAction[];
    risk_level: string;
    confidence_score: number;
    timestamp: string;
}

export interface TriggerAnalysisResponse {
    status: string;
    message: string;
    anomalies_detected: number;
    recommendations?: Recommendation;
}

export interface HealthCheck {
    status: string;
    poller_running: boolean;
}
