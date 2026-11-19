import React, { useState } from 'react';
import { Incident, SeverityLevel } from '../types';
import { AlertCircle, CheckCircle2, Clock, GitCommit, Layers, Search, ShieldAlert, Sparkles, Flame } from 'lucide-react';

interface IncidentFeedProps {
  incidents: Incident[];
  selectedIncidentId: string | null;
  onSelectIncident: (id: string) => void;
  isLoading: boolean;
}

export const IncidentFeed: React.FC<IncidentFeedProps> = ({
  incidents,
  selectedIncidentId,
  onSelectIncident,
  isLoading
}) => {
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredIncidents = incidents.filter((inc) => {
    if (severityFilter !== 'ALL' && inc.severity !== severityFilter) return false;
    if (statusFilter !== 'ALL' && inc.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchText = `${inc.incident_id} ${inc.service_name} ${inc.title} ${inc.error_message}`.toLowerCase();
      if (!matchText.includes(q)) return false;
    }
    return true;
  });

  const getSeverityBadge = (severity: SeverityLevel) => {
    switch (severity) {
      case 'P1-Critical':
        return (
          <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 font-bold">
            <Flame className="w-3 h-3 text-rose-500 animate-pulse" />
            P1 Critical
          </span>
        );
      case 'P2-High':
        return (
          <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-medium">
            <ShieldAlert className="w-3 h-3 text-amber-400" />
            P2 High
          </span>
        );
      case 'P3-Medium':
        return (
          <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-medium">
            <AlertCircle className="w-3 h-3 text-cyan-400" />
            P3 Medium
          </span>
        );
      default:
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
            {severity}
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-bold text-rose-400 uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping" />
            Active Outage
          </span>
        );
      case 'REMEDIATING':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-bold text-cyan-400 uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-spin" />
            Self-Healing Active
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 font-medium">
            <CheckCircle2 className="w-3 h-3" />
            Mitigated
          </span>
        );
      default:
        return <span className="text-[10px] font-mono text-slate-400">{status}</span>;
    }
  };

  const formatRelativeTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffSec = Math.floor(diffMs / 1000);
      if (diffSec < 60) return `${diffSec}s ago`;
      const diffMin = Math.floor(diffSec / 60);
      if (diffMin < 60) return `${diffMin}m ago`;
      const diffHr = Math.floor(diffMin / 60);
      if (diffHr < 24) return `${diffHr}h ago`;
      return `${Math.floor(diffHr / 24)}d ago`;
    } catch {
      return 'recent';
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0b101d] border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Header and Filter Controls */}
      <div className="p-3.5 border-b border-slate-800/80 bg-slate-900/60">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white tracking-wide">
              Live Incident Feed
            </h2>
            <span className="px-2 py-0.5 text-[11px] font-mono font-semibold rounded-full bg-slate-800 text-slate-300">
              {filteredIncidents.length}
            </span>
          </div>

          <div className="flex items-center gap-1 text-xs">
            {['ALL', 'ACTIVE', 'RESOLVED'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
                  statusFilter === st
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {/* Search Input */}
        <div className="relative mb-2.5">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search service, error signature, or commit..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 font-mono transition-colors"
          />
        </div>

        {/* Severity Filters */}
        <div className="flex items-center gap-1.5">
          {['ALL', 'P1-Critical', 'P2-High', 'P3-Medium'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-colors ${
                severityFilter === sev
                  ? 'bg-slate-700 text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200 bg-slate-800/40'
              }`}
            >
              {sev.replace('P1-', '').replace('P2-', '').replace('P3-', '')}
            </button>
          ))}
        </div>
      </div>

      {/* Incident List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60 p-2 space-y-2">
        {isLoading && incidents.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center text-slate-400 text-xs">
            <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mb-2" />
            <span>Connecting to Atlas Telemetry Stream...</span>
          </div>
        ) : filteredIncidents.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs font-mono">
            No incidents matching current filters.
          </div>
        ) : (
          filteredIncidents.map((incident) => {
            const isSelected = incident.incident_id === selectedIncidentId;
            const topMatch = incident.top_matches && incident.top_matches.length > 0 ? incident.top_matches[0] : null;
            const matchPercentage = topMatch ? Math.round(topMatch.similarity_score * 100) : null;

            return (
              <div
                key={incident.incident_id}
                onClick={() => onSelectIncident(incident.incident_id)}
                className={`p-3 rounded-xl cursor-pointer transition-all duration-200 border ${
                  isSelected
                    ? 'bg-slate-800/90 border-cyan-500/70 shadow-lg shadow-cyan-950/40 translate-x-1'
                    : 'bg-slate-900/50 border-slate-800/80 hover:bg-slate-850 hover:border-slate-700'
                }`}
              >
                {/* Top Row: Service, Severity, Status */}
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-slate-100 tracking-tight">
                      {incident.service_name}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      #{incident.incident_id}
                    </span>
                  </div>
                  {getSeverityBadge(incident.severity)}
                </div>

                {/* Title & Error message */}
                <p className="text-xs text-slate-300 font-medium line-clamp-2 mb-2">
                  {incident.title}
                </p>

                {/* Semantic Deduplication Badge (Vector Search Result) */}
                {topMatch && matchPercentage && matchPercentage > 50 && (
                  <div className="mb-2 p-1.5 rounded-lg bg-cyan-950/40 border border-cyan-500/30 flex items-center justify-between text-[11px] font-mono">
                    <div className="flex items-center gap-1.5 text-cyan-300">
                      <Sparkles className="w-3 h-3 text-cyan-400" />
                      <span>{matchPercentage}% vector match to</span>
                      <span className="font-bold underline decoration-cyan-500/50">
                        #{topMatch.incident_id}
                      </span>
                    </div>
                    <span className="text-[10px] text-cyan-400/80 font-semibold">
                      Deduplicated
                    </span>
                  </div>
                )}

                {/* Footer Metadata */}
                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono pt-1 border-t border-slate-800/40">
                  <div className="flex items-center gap-3">
                    {getStatusBadge(incident.status)}
                    {incident.git_metadata?.commit_hash && (
                      <span className="flex items-center gap-1 text-slate-400">
                        <GitCommit className="w-3 h-3 text-slate-400" />
                        {incident.git_metadata.commit_hash.slice(0, 7)}
                      </span>
                    )}
                  </div>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatRelativeTime(incident.created_at)}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
