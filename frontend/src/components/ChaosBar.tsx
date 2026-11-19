import React, { useState } from 'react';
import { Zap, AlertTriangle, ShieldAlert, Cpu, Database, RefreshCw } from 'lucide-react';
import { ChaosScenario } from '../types';

interface ChaosBarProps {
  scenarios: ChaosScenario[];
  onTrigger: (scenarioId: string) => Promise<void>;
}

export const ChaosBar: React.FC<ChaosBarProps> = ({ scenarios, onTrigger }) => {
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);

  const handleTrigger = async (id: string) => {
    try {
      setLoadingScenario(id);
      await onTrigger(id);
    } finally {
      setLoadingScenario(null);
    }
  };

  const getScenarioIcon = (id: string) => {
    switch (id) {
      case 'db_pool_exhaustion':
        return <Database className="w-4 h-4 text-rose-400" />;
      case 'bad_ci_dependency':
        return <ShieldAlert className="w-4 h-4 text-amber-400" />;
      case 'memory_leak_oom':
        return <Cpu className="w-4 h-4 text-purple-400" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-cyan-400" />;
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-xl backdrop-blur-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30">
            <Zap className="w-4 h-4 text-rose-400 animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Chaos Engineering Simulator
              <span className="text-[10px] font-mono text-slate-400 font-normal">
                (Simulate Cascading Outages On Demand)
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Injects realistic metric ramps into TimeSeries, triggers vector deduplication, and reconstructs blast radius.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {scenarios.map((s) => {
          const isLoading = loadingScenario === s.id;
          return (
            <button
              key={s.id}
              disabled={isLoading}
              onClick={() => handleTrigger(s.id)}
              className="group relative flex flex-col items-start p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/90 text-left transition-all duration-200 hover:shadow-lg disabled:opacity-60"
            >
              <div className="flex items-center justify-between w-full mb-1.5">
                <div className="flex items-center gap-2">
                  {getScenarioIcon(s.id)}
                  <span className="text-xs font-mono font-bold text-slate-200 group-hover:text-cyan-300">
                    {s.service_name}
                  </span>
                </div>
                <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${
                  s.level === 'CRITICAL' || s.level === 'FATAL'
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                    : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                }`}>
                  {s.level}
                </span>
              </div>

              <p className="text-xs text-slate-400 line-clamp-2 mb-2 group-hover:text-slate-300">
                {s.title}
              </p>

              <div className="mt-auto w-full pt-1.5 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-cyan-400 font-mono">
                <span>{isLoading ? 'Injecting Outage...' : 'Simulate Outage'}</span>
                {isLoading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <span className="opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
