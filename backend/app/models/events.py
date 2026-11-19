from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class SeverityLevel(str, Enum):
    P1 = "P1-Critical"
    P2 = "P2-High"
    P3 = "P3-Medium"
    P4 = "P4-Low"

class IncidentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TRIAGED = "TRIAGED"
    REMEDIATING = "REMEDIATING"
    RESOLVED = "RESOLVED"

class GitMetadata(BaseModel):
    commit_hash: Optional[str] = None
    branch: Optional[str] = "main"
    author: Optional[str] = None
    commit_message: Optional[str] = None
    diff_summary: Optional[str] = None
    changed_files: Optional[List[str]] = Field(default_factory=list)

class RawMetricEvent(BaseModel):
    service_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metric_type: str = Field(description="heartbeat, cpu_percent, memory_mb, latency_ms, error_rate")
    value: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)

class PolymorphicPayload(BaseModel):
    """Flexible schema for ingesting any telemetry/error payload."""
    source: Optional[str] = "generic-service"
    service_name: str = "checkout-api"
    environment: str = "production"
    timestamp: Optional[datetime] = None
    level: str = "ERROR"
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    git_metadata: Optional[GitMetadata] = None
    metrics: Optional[Dict[str, float]] = None
    context: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    model_config = ConfigDict(extra="allow")

class IncidentMatch(BaseModel):
    incident_id: str
    title: str
    similarity_score: float
    service_name: str
    resolution_summary: Optional[str] = None
    created_at: datetime
    runbook_id: Optional[str] = None

class Incident(BaseModel):
    incident_id: str
    title: str
    service_name: str
    environment: str = "production"
    severity: SeverityLevel = SeverityLevel.P1
    status: IncidentStatus = IncidentStatus.ACTIVE
    error_message: str
    normalized_stack_trace: str
    raw_stack_trace: Optional[str] = None
    source: str = "webhook"
    git_metadata: Optional[GitMetadata] = None
    embedding: List[float] = Field(default_factory=list)
    upstream_services: List[str] = Field(default_factory=list)
    downstream_services: List[str] = Field(default_factory=list)
    blast_radius_score: float = 0.0
    suggested_runbook_id: Optional[str] = None
    top_matches: List[IncidentMatch] = Field(default_factory=list)
    root_cause_summary: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(from_attributes=True)

class Runbook(BaseModel):
    runbook_id: str
    title: str
    error_signature: str
    service_name: str
    category: str
    remediation_steps: List[str]
    remediation_commands: List[str]
    rollback_script: Optional[str] = None
    post_mortem_notes: str
    verification_check: str
    success_rate: float = 0.95
    average_recovery_time_sec: int = 120
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(from_attributes=True)

class MetricPoint(BaseModel):
    timestamp: datetime
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    latency_ms: float = 0.0
    error_rate: float = 0.0
    active_connections: int = 0
    is_deployment_marker: bool = False
    deployment_info: Optional[str] = None

class TriageResponse(BaseModel):
    incident: Incident
    similar_past_outages: List[IncidentMatch]
    matched_runbook: Optional[Runbook] = None
    causal_timeline: List[MetricPoint]
    affected_topology: Dict[str, Any]
    ai_root_cause_analysis: str
    suggested_action: str
