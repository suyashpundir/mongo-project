export type SeverityLevel = 'P1-Critical' | 'P2-High' | 'P3-Medium' | 'P4-Low';
export type IncidentStatus = 'ACTIVE' | 'TRIAGED' | 'REMEDIATING' | 'RESOLVED';

export interface GitMetadata {
  commit_hash?: string;
  branch?: string;
  author?: string;
  commit_message?: string;
  diff_summary?: string;
  changed_files?: string[];
}

export interface IncidentMatch {
  incident_id: string;
  title: string;
  similarity_score: number;
  service_name: string;
  created_at: string;
  runbook_id?: string;
}

export interface Incident {
  incident_id: string;
  title: string;
  service_name: string;
  environment: string;
  severity: SeverityLevel;
  status: IncidentStatus;
  error_message: string;
  normalized_stack_trace: string;
  raw_stack_trace?: string;
  source: string;
  git_metadata?: GitMetadata;
  suggested_runbook_id?: string;
  top_matches?: IncidentMatch[];
  root_cause_summary?: string;
  created_at: string;
  updated_at: string;
}

export interface Runbook {
  runbook_id: string;
  title: string;
  error_signature: string;
  service_name: string;
  category: string;
  remediation_steps: string[];
  remediation_commands: string[];
  rollback_script?: string;
  post_mortem_notes: string;
  verification_check: string;
  success_rate: number;
  average_recovery_time_sec: number;
  created_at?: string;
}

export interface MetricPoint {
  timestamp: string;
  cpu_percent: number;
  memory_mb: number;
  latency_ms: number;
  error_rate: number;
  active_connections?: number;
  is_deployment_marker?: boolean;
  deployment_info?: string | null;
}

export interface TopologyNode {
  id: string;
  label: string;
  status: 'HEALTHY' | 'DEGRADED' | 'CRITICAL';
  health_score: number;
  active_incident_id?: string | null;
  type: 'microservice' | 'database' | 'ci';
}

export interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  is_impacted: boolean;
  latency_ms: number;
}

export interface TopologyData {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  root_failure_node?: string | null;
  blast_radius_count: number;
}

export interface TriageData {
  incident: Incident;
  similar_past_outages: IncidentMatch[];
  matched_runbook: Runbook | null;
  causal_timeline: MetricPoint[];
  affected_topology: TopologyData;
  ai_root_cause_analysis: string;
  suggested_action: string;
}

export interface ChaosScenario {
  id: string;
  title: string;
  service_name: string;
  level: string;
  error_message: string;
}

export interface RemediationLogStep {
  step_index: number;
  total_steps: number;
  step_description: string;
  command: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED';
  output?: string;
  timestamp: string;
}
