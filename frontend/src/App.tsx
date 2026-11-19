import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { IncidentFeed } from './components/IncidentFeed';
import { TopologyMap } from './components/TopologyMap';
import { TelemetryTimeline } from './components/TelemetryTimeline';
import { RootCauseDiffView } from './components/RootCauseDiffView';
import { ChaosBar } from './components/ChaosBar';
import { RunbookExecutorModal } from './components/RunbookExecutorModal';
import {
  Incident,
  TriageData,
  ChaosScenario,
  RemediationLogStep
} from './types';
import {
  fetchIncidents,
  fetchIncidentTriage,
  fetchSystemHealth,
  fetchChaosScenarios,
  triggerChaosScenario,
  executeRunbook
} from './services/api';
import { wsClient } from './services/websocket';

export const App: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [triageData, setTriageData] = useState<TriageData | null>(null);
  const [chaosScenarios, setChaosScenarios] = useState<ChaosScenario[]>([]);
  const [isChaosBarOpen, setIsChaosBarOpen] = useState<boolean>(true);
  const [isLoadingIncidents, setIsLoadingIncidents] = useState<boolean>(true);

  // System status
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [dbConnected, setDbConnected] = useState<boolean>(true);
  const [atlasReady, setAtlasReady] = useState<boolean>(false);
  const [aiEngine, setAiEngine] = useState<string>('Gemini 2.5 Flash');

  // Remediation Execution Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [remediationLogs, setRemediationLogs] = useState<RemediationLogStep[]>([]);
  const [isExecutingRunbook, setIsExecutingRunbook] = useState<boolean>(false);
  const [isRemediationComplete, setIsRemediationComplete] = useState<boolean>(false);

  // 1. Initial Data Fetch
  const loadInitialData = useCallback(async () => {
    try {
      setIsLoadingIncidents(true);
      const [incRes, healthRes, chaosRes] = await Promise.allSettled([
        fetchIncidents(),
        fetchSystemHealth(),
        fetchChaosScenarios()
      ]);

      if (incRes.status === 'fulfilled') {
        setIncidents(incRes.value.incidents);
        if (incRes.value.incidents.length > 0 && !selectedIncidentId) {
          setSelectedIncidentId(incRes.value.incidents[0].incident_id);
        }
      }

      if (healthRes.status === 'fulfilled') {
        setDbConnected(healthRes.value.database_connected);
        setAtlasReady(healthRes.value.atlas_vector_search_ready);
        setAiEngine(healthRes.value.ai_engine);
      }

      if (chaosRes.status === 'fulfilled') {
        setChaosScenarios(chaosRes.value);
      }
    } finally {
      setIsLoadingIncidents(false);
    }
  }, [selectedIncidentId]);

  // 2. Fetch Triage Details when selected incident changes
  useEffect(() => {
    if (!selectedIncidentId) return;

    let isMounted = true;
    const loadTriage = async () => {
      try {
        const triage = await fetchIncidentTriage(selectedIncidentId);
        if (isMounted) {
          setTriageData(triage);
        }
      } catch (err) {
        console.error('Failed to load incident triage:', err);
      }
    };

    loadTriage();
    return () => {
      isMounted = false;
    };
  }, [selectedIncidentId]);

  // 3. Setup WebSocket and Listeners
  useEffect(() => {
    wsClient.connect();

    const unsubStatus = wsClient.on('connection_status', (data: unknown) => {
      const payload = data as { connected: boolean };
      setWsConnected(payload.connected);
    });

    const unsubNewIncident = wsClient.on('new_incident', (data: unknown) => {
      const newInc = data as Incident;
      setIncidents((prev) => [newInc, ...prev.filter((i) => i.incident_id !== newInc.incident_id)]);
      setSelectedIncidentId(newInc.incident_id);
    });

    const unsubChaos = wsClient.on('chaos_triggered', (data: unknown) => {
      const payload = data as { incident?: Incident };
      if (payload?.incident) {
        const inc = payload.incident;
        setIncidents((prev) => [inc, ...prev.filter((i) => i.incident_id !== inc.incident_id)]);
        setSelectedIncidentId(inc.incident_id);
      }
    });

    const unsubIncidentStatus = wsClient.on('incident_status_change', (data: unknown) => {
      const payload = data as { incident_id: string; status: Incident['status'] };
      setIncidents((prev) =>
        prev.map((i) =>
          i.incident_id === payload.incident_id ? { ...i, status: payload.status } : i
        )
      );
      if (triageData && triageData.incident.incident_id === payload.incident_id) {
        setTriageData((prev) => (prev ? { ...prev, incident: { ...prev.incident, status: payload.status } } : null));
      }
    });

    const unsubRemediationStep = wsClient.on('remediation_step', (data: unknown) => {
      const payload = data as { log: RemediationLogStep };
      setRemediationLogs((prev) => [...prev, payload.log]);
    });

    loadInitialData();

    return () => {
      unsubStatus();
      unsubNewIncident();
      unsubChaos();
      unsubIncidentStatus();
      unsubRemediationStep();
    };
  }, [loadInitialData]);

  // 4. Handle Trigger Chaos Outage
  const handleTriggerChaos = async (scenarioId: string) => {
    try {
      const res = await triggerChaosScenario(scenarioId);
      if (res && res.incident_id) {
        setSelectedIncidentId(res.incident_id);
      }
    } catch (err) {
      console.error('Failed to trigger chaos outage:', err);
    }
  };

  // 5. Handle Execute Runbook
  const handleExecuteRunbook = async (runbookId: string) => {
    if (!selectedIncidentId || !triageData) return;
    try {
      setIsExecutingRunbook(true);
      setIsRemediationComplete(false);
      setRemediationLogs([]);
      setIsModalOpen(true);

      const res = await executeRunbook(runbookId, selectedIncidentId);
      if (res.status === 'success') {
        setIsRemediationComplete(true);
        // Refresh incident triage
        const updatedTriage = await fetchIncidentTriage(selectedIncidentId);
        setTriageData(updatedTriage);
      }
    } catch (err) {
      console.error('Failed to execute runbook:', err);
    } finally {
      setIsExecutingRunbook(false);
    }
  };

  const activeIncidentsCount = incidents.filter((i) => i.status === 'ACTIVE').length;

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30">
      {/* Top Navigation Bar */}
      <Header
        wsConnected={wsConnected}
        dbConnected={dbConnected}
        atlasReady={atlasReady}
        aiEngine={aiEngine}
        activeCount={activeIncidentsCount}
        onOpenChaosModal={() => setIsChaosBarOpen((prev) => !prev)}
      />

      {/* Main Workspace Container */}
      <main className="flex-1 p-4 lg:p-6 space-y-5 max-w-[1720px] mx-auto w-full">
        {/* Chaos Engineering Simulator Demo Control Bar */}
        {isChaosBarOpen && (
          <ChaosBar
            scenarios={chaosScenarios}
            onTrigger={handleTriggerChaos}
          />
        )}

        {/* Command Center Grid: 3-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          {/* Column 1: Live Incident Feed (3.5 cols on desktop) */}
          <div className="lg:col-span-4 xl:col-span-3 h-[780px]">
            <IncidentFeed
              incidents={incidents}
              selectedIncidentId={selectedIncidentId}
              onSelectIncident={(id) => setSelectedIncidentId(id)}
              isLoading={isLoadingIncidents}
            />
          </div>

          {/* Column 2 & 3: Causal Timeline, Topology & Root Cause Diff View (8.5 cols) */}
          <div className="lg:col-span-8 xl:col-span-9 space-y-5">
            {triageData ? (
              <>
                {/* Upper Row: Pre-Crash Telemetry Timeline & Service Topology side-by-side */}
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                  <TelemetryTimeline
                    timeline={triageData.causal_timeline}
                    serviceName={triageData.incident.service_name}
                  />

                  <TopologyMap
                    data={triageData.affected_topology}
                    selectedService={triageData.incident.service_name}
                    onSelectService={(svc) => {
                      const match = incidents.find((i) => i.service_name === svc);
                      if (match) setSelectedIncidentId(match.incident_id);
                    }}
                  />
                </div>

                {/* Lower Row: Root Cause Analysis, Stack Trace Deduplication & Runbook Remediation */}
                <RootCauseDiffView
                  incident={triageData.incident}
                  topMatch={triageData.similar_past_outages.length > 0 ? triageData.similar_past_outages[0] : null}
                  matchedRunbook={triageData.matched_runbook}
                  aiAnalysis={triageData.ai_root_cause_analysis}
                  onExecuteRunbook={handleExecuteRunbook}
                  isExecutingRunbook={isExecutingRunbook}
                />
              </>
            ) : (
              <div className="h-96 flex flex-col items-center justify-center p-8 bg-[#0b101d] border border-slate-800 rounded-xl text-slate-400 font-mono text-xs">
                <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mb-3" />
                <span>Select an incident from the feed to view causal triage & blast radius.</span>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Autonomous Runbook Self-Healing Progress Modal */}
      <RunbookExecutorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        runbookTitle={triageData?.matched_runbook?.title || 'Automated Remediation'}
        runbookId={triageData?.matched_runbook?.runbook_id || 'RB-AUTO'}
        logs={remediationLogs}
        isComplete={isRemediationComplete}
      />
    </div>
  );
};

export default App;
