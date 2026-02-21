from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone


# ── Section 1: CPU & Scheduler ──────────────────────────────────
class CpuMetrics(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sql_cpu_percent: float = 0.0
    system_idle_percent: float = 0.0
    other_process_cpu_percent: float = 0.0
    scheduler_count: int = 0
    runnable_tasks_count: int = 0
    current_workers_count: int = 0
    max_workers_count: int = 0
    signal_wait_pct: float = 0.0


# ── Section 2: Memory ───────────────────────────────────────────
class MemoryMetrics(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_server_memory_mb: float = 0.0
    target_server_memory_mb: float = 0.0
    page_life_expectancy: int = 0
    buffer_cache_hit_ratio: float = 0.0
    memory_grants_pending: int = 0
    memory_grants_outstanding: int = 0
    stolen_server_memory_kb: int = 0
    free_memory_kb: int = 0
    total_physical_memory_mb: float = 0.0
    available_physical_memory_mb: float = 0.0


# ── Section 3: Wait Stats (Delta) ───────────────────────────────
class WaitStatDelta(BaseModel):
    wait_type: str
    wait_time_delta_ms: float = 0.0
    waiting_tasks_delta: int = 0
    signal_wait_delta_ms: float = 0.0
    wait_rate_ms_per_sec: float = 0.0
    dominance_pct: float = 0.0
    # Raw cumulative for history
    cumulative_wait_time_ms: int = 0
    cumulative_waiting_tasks: int = 0
    cumulative_signal_wait_ms: int = 0

class WaitStatsSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    elapsed_seconds: float = 0.0
    total_delta_ms: float = 0.0
    waits: List[WaitStatDelta] = []


# ── Section 4: Workload ─────────────────────────────────────────
class SessionSummary(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_sessions: int = 0
    active_sessions: int = 0
    sleeping_sessions: int = 0
    blocked_sessions: int = 0

class BlockingNode(BaseModel):
    session_id: int
    blocking_session_id: int
    wait_type: Optional[str] = None
    wait_time_ms: int = 0
    status: str = ""
    command: str = ""
    sql_text: Optional[str] = None
    database_name: Optional[str] = None
    host_name: Optional[str] = None
    program_name: Optional[str] = None
    is_head_blocker: bool = False

class BlockingSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    chains: List[BlockingNode] = []
    head_blocker_count: int = 0

class TopQuery(BaseModel):
    query_hash: str
    execution_count: int = 0
    total_worker_time: int = 0
    total_logical_reads: int = 0
    total_elapsed_time: int = 0
    sql_text: str = ""
    database_name: Optional[str] = None

class QuerySnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    top_by_cpu: List[TopQuery] = []
    top_by_reads: List[TopQuery] = []
    top_by_duration: List[TopQuery] = []


# ── Section 5: I/O & Storage ────────────────────────────────────
class FileIOMetric(BaseModel):
    database_name: str
    file_name: str
    file_type: str  # "ROWS" or "LOG"
    read_latency_ms: float = 0.0
    write_latency_ms: float = 0.0
    read_iops: float = 0.0
    write_iops: float = 0.0
    size_mb: float = 0.0

class IOSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    files: List[FileIOMetric] = []
    tempdb_used_mb: float = 0.0
    tempdb_free_mb: float = 0.0


# ── Section 6: Index Health ─────────────────────────────────────
class FragmentedIndex(BaseModel):
    database_name: Optional[str] = None
    schema_name: Optional[str] = None
    table_name: Optional[str] = None
    index_name: Optional[str] = None
    avg_fragmentation_percent: float = 0.0
    page_count: int = 0
    user_seeks: int = 0
    user_scans: int = 0
    user_lookups: int = 0
    user_updates: int = 0

class MissingIndexDetail(BaseModel):
    database_name: Optional[str] = None
    schema_name: Optional[str] = None
    table_name: Optional[str] = None
    equality_columns: Optional[str] = None
    inequality_columns: Optional[str] = None
    included_columns: Optional[str] = None
    user_seeks: int = 0
    user_scans: int = 0
    avg_total_user_cost: float = 0.0
    avg_user_impact: float = 0.0
    impact_score: float = 0.0

class IndexSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fragmented: List[FragmentedIndex] = []
    missing: List[MissingIndexDetail] = []


# ── Section 7: Query Store ──────────────────────────────────────
class RegressedQuery(BaseModel):
    query_id: int = 0
    query_text: str = ""
    recent_avg_duration_us: float = 0.0
    historical_avg_duration_us: float = 0.0
    regression_pct: float = 0.0
    execution_count: int = 0
    plan_count: int = 0

class PlanPerformance(BaseModel):
    plan_id: int
    avg_duration_us: float = 0.0
    avg_cpu_time_us: float = 0.0
    execution_count: int = 0

class ParameterSniffingCandidate(BaseModel):
    query_id: int
    query_text: str = ""
    plan_count: int = 0
    plans: List[PlanPerformance] = []
    duration_mean_us: float = 0.0
    duration_stddev_us: float = 0.0
    max_avg_duration_us: float = 0.0
    min_avg_duration_us: float = 0.0
    variance_ratio: float = 0.0
    suspected: bool = False

class QueryStoreSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_enabled: bool = False
    regressed_queries: List[RegressedQuery] = []
    parameter_sniffing_candidates: List[ParameterSniffingCandidate] = []
    forced_plan_count: int = 0
    total_plans_tracked: int = 0


# ── Section 8: Database Health ──────────────────────────────────
class DatabaseInfo(BaseModel):
    db_name: str
    state_desc: str = "ONLINE"
    recovery_model: str = ""
    compatibility_level: int = 0
    size_mb: float = 0.0
    free_space_mb: float = 0.0
    log_space_used_pct: float = 0.0
    last_full_backup: Optional[datetime] = None
    last_log_backup: Optional[datetime] = None
    log_reuse_wait_desc: str = ""

class DatabasesSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    databases: List[DatabaseInfo] = []


# ── Section 9: Configuration ────────────────────────────────────
class ConfigSetting(BaseModel):
    name: str
    value: Any
    recommended: Optional[str] = None
    warning: Optional[str] = None

class ConfigSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    settings: List[ConfigSetting] = []
    trace_flags: List[int] = []
    tempdb_file_count: int = 0
