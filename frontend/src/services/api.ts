import { Incident, TriageData, Runbook, TopologyData, ChaosScenario } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

export async function fetchIncidents(params?: { status?: string; severity?: string; service?: string }): Promise<{ total: number; count: number; incidents: Incident[] }> {
  const query = new URLSearchParams();
  if (params?.status) query.append('status', params.status);
  if (params?.severity) query.append('severity', params.severity);
  if (params?.service) query.append('service_name', params.service);

  const res = await fetch(`${API_BASE}/api/incidents?${query.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch incidents: ${res.statusText}`);
  return res.json();
}

export async function fetchIncidentTriage(incidentId: string): Promise<TriageData> {
  const res = await fetch(`${API_BASE}/api/incidents/${incidentId}/triage`);
  if (!res.ok) throw new Error(`Failed to fetch triage data for ${incidentId}: ${res.statusText}`);
  return res.json();
}

export async function fetchTopology(activeService?: string): Promise<TopologyData> {
  const url = activeService 
    ? `${API_BASE}/api/services/topology?active_service=${encodeURIComponent(activeService)}`
    : `${API_BASE}/api/services/topology`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch topology: ${res.statusText}`);
  return res.json();
}

export async function fetchRunbooks(): Promise<Runbook[]> {
  const res = await fetch(`${API_BASE}/api/runbooks`);
  if (!res.ok) throw new Error(`Failed to fetch runbooks: ${res.statusText}`);
  return res.json();
}

export async function executeRunbook(runbookId: string, incidentId: string): Promise<{ status: string; incident_id: string; runbook_id: string; final_status: string }> {
  const res = await fetch(`${API_BASE}/api/runbooks/${runbookId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_id: incidentId })
  });
  if (!res.ok) throw new Error(`Failed to execute runbook: ${res.statusText}`);
  return res.json();
}

export async function fetchChaosScenarios(): Promise<ChaosScenario[]> {
  const res = await fetch(`${API_BASE}/api/chaos/scenarios`);
  if (!res.ok) throw new Error(`Failed to fetch chaos scenarios: ${res.statusText}`);
  return res.json();
}

export async function triggerChaosScenario(scenario: string): Promise<{ incident_id: string; service_name: string; deduplication_match: { has_match: boolean; similarity_percentage: string; top_match_id?: string } }> {
  const res = await fetch(`${API_BASE}/api/chaos/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario })
  });
  if (!res.ok) throw new Error(`Failed to trigger chaos: ${res.statusText}`);
  return res.json();
}

export async function fetchSystemHealth(): Promise<{ status: string; database_connected: boolean; atlas_vector_search_ready: boolean; ai_engine: string }> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Failed to fetch health status: ${res.statusText}`);
  return res.json();
}
