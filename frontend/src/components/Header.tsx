import React from 'react';
import { Activity, ShieldCheck, Zap, Database, Cpu, Radio } from 'lucide-react';

interface HeaderProps {
  wsConnected: boolean;
  dbConnected: boolean;
  atlasReady: boolean;
  aiEngine: string;
  activeCount: number;
  onOpenChaosModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  wsConnected,
  dbConnected,
  atlasReady,
  aiEngine,
  activeCount,
  onOpenChaosModal
}) => {
  return (
    <header className="sticky top-0 z-30 bg-[#090d16]/90 backdrop-blur-md border-b border-slate-800 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 via-blue-500/20 to-purple-500/20 border border-cyan-500/40 shadow-lg shadow-cyan-500/10">
          <Activity className="w-5 h-5 text-cyan-400 animate-pulse" />
          <div className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-white font-sans">
              Net<span className="text-cyan-400">Pulse</span>
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              v1.0 RCA
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">
            Autonomous Incident Triage & Self-Healing Platform
          </p>
        </div>
      </div>

      {/* Real-time System Status Pills */}
      <div className="flex items-center flex-wrap gap-2 text-xs">
        {/* WebSocket Live Stream */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${
          wsConnected 
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
            : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
        }`}>
          <Radio className="w-3.5 h-3.5 animate-pulse" />
          <span className="font-mono font-medium">{wsConnected ? 'LIVE STREAM' : 'DISCONNECTED'}</span>
        </div>

        {/* Database Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-slate-300">
          <Database className={`w-3.5 h-3.5 ${dbConnected ? 'text-emerald-400' : 'text-rose-400'}`} />
          <span>MongoDB TimeSeries</span>
        </div>

        {/* Vector Search Engine */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-slate-300">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>{atlasReady ? 'Atlas $vectorSearch' : 'Vector Cosine Deduplication'}</span>
        </div>

        {/* AI Engine */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-purple-400" />
          <span>{aiEngine || 'Gemini 2.5 Flash'}</span>
        </div>
      </div>

      {/* Action CTA */}
      <div className="flex items-center gap-3">
        {activeCount > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-mono font-bold animate-pulse">
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            {activeCount} ACTIVE CRITICAL
          </div>
        )}

        <button
          onClick={onOpenChaosModal}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white text-xs font-semibold shadow-md shadow-rose-900/20 border border-rose-400/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          <Zap className="w-3.5 h-3.5" />
          <span>Trigger Chaos Outage</span>
        </button>
      </div>
    </header>
  );
};
