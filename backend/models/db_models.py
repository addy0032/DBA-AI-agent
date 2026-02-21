from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum

class SeverityLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AnomalyType(str, Enum):
    BLOCKING = "BLOCKING"
    HIGH_CPU = "HIGH_CPU"
    HIGH_MEMORY = "HIGH_MEMORY"
    MISSING_INDEX = "MISSING_INDEX"
    LONG_RUNNING_QUERY = "LONG_RUNNING_QUERY"
    HIGH_WAITS = "HIGH_WAITS"
    INDEX_FRAGMENTATION = "INDEX_FRAGMENTATION"
    PARAMETER_SNIFFING = "PARAMETER_SNIFFING"
    PREDICTED_REGRESSION = "PREDICTED_REGRESSION"

class Anomaly(BaseModel):
    id: str
    type: AnomalyType
    severity: SeverityLevel
    root_resource: str
    context_data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BlockingSession(BaseModel):
    session_id: int
    blocking_session_id: int
    wait_type: Optional[str] = None
    wait_time_ms: int = 0
    status: str
    command: str
    sql_text: Optional[str] = None
    database_name: Optional[str] = None
    host_name: Optional[str] = None
    program_name: Optional[str] = None

class WaitStatSummary(BaseModel):
    wait_type: str
    waiting_tasks_count: int
    wait_time_ms: int
    max_wait_time_ms: int
    signal_wait_time_ms: int

class QueryStat(BaseModel):
    query_hash: str
    execution_count: int
    total_worker_time: int
    total_logical_reads: int
    total_elapsed_time: int
    sql_text: str
    database_name: Optional[str] = None
    query_plan: Optional[str] = None
    has_table_scan: bool = False
    estimated_cost: float = 0.0

class IndexHealth(BaseModel):
    database_name: Optional[str] = None
    schema_name: Optional[str] = None
    table_name: Optional[str] = None
    index_name: Optional[str] = None
    avg_fragmentation_percent: float
    page_count: int

class MissingIndex(BaseModel):
    database_name: Optional[str] = None
    schema_name: Optional[str] = None
    table_name: Optional[str] = None
    equality_columns: Optional[str] = None
    inequality_columns: Optional[str] = None
    included_columns: Optional[str] = None
    user_seeks: int
    user_scans: int
    avg_total_user_cost: float
    avg_user_impact: float

class MetricSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active_sessions_count: int
    blocking_chains: List[BlockingSession] = []
    top_wait_stats: List[WaitStatSummary] = []
    expensive_queries: List[QueryStat] = []
    index_health: List[IndexHealth] = []
    missing_indexes: List[MissingIndex] = []
