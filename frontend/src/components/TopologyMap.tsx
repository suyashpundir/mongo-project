import React from 'react';
import { TopologyData, TopologyNode } from '../types';
import { Network, Server, Database, ArrowRight, Activity } from 'lucide-react';

interface TopologyMapProps {
  data: TopologyData | null;
  selectedService: string | null;
  onSelectService: (serviceName: string) => void;
}

export const TopologyMap: React.FC<TopologyMapProps> = ({
  data,
  selectedService,
  onSelectService
}) => {
  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-slate-500 font-mono text-xs">
        <Network className="w-8 h-8 text-slate-600 mb-2 animate-pulse" />
        <span>Loading service dependency mesh...</span>
      </div>
    );
  }

  // Group nodes by tier for structured topology layout
  const tiers = {
    ingress: data.nodes.filter((n) => n.id === 'api-gateway'),
    core: data.nodes.filter((n) => ['auth-service', 'checkout-api', 'inventory-service', 'ci-cd-builder'].includes(n.id)),
    downstream: data.nodes.filter((n) => ['payment-gateway', 'postgres-orders', 'postgres-auth', 'redis-cache', 'redis-sessions'].includes(n.id))
  };

  const getNodeIcon = (node: TopologyNode) => {
    if (node.type === 'database') {
      return <Database className="w-4 h-4" />;
    }
    return <Server className="w-4 h-4" />;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'CRITICAL':
        return {
          bg: 'bg-rose-950/80',
          border: 'border-rose-500',
          text: 'text-rose-400',
          badge: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
          pulse: 'shadow-lg shadow-rose-900/50 animate-pulse'
        };
      case 'DEGRADED':
        return {
          bg: 'bg-amber-950/70',
          border: 'border-amber-500/80',
          text: 'text-amber-400',
          badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
          pulse: 'shadow-md shadow-amber-900/30'
        };
      default:
        return {
          bg: 'bg-slate-900/80',
          border: 'border-emerald-500/40',
          text: 'text-emerald-400',
          badge: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
          pulse: ''
        };
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0b101d] border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Topology Header */}
      <div className="p-3.5 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">
            Causal Blast-Radius Topology
          </h2>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="flex items-center gap-1 text-rose-400 font-bold bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping" />
            Blast Radius: {data.blast_radius_count} Services Impacted
          </span>
        </div>
      </div>

      {/* Visual Graph View */}
      <div className="flex-1 p-5 overflow-auto flex flex-col justify-around gap-6 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px]">
        {/* Tier 1: Ingress Gateway */}
        <div className="flex flex-col items-center">
          <div className="text-[10px] font-mono uppercase text-slate-400 mb-2 font-semibold tracking-wider">
            Tier 1: Edge & Ingress Gateway
          </div>
          <div className="flex justify-center gap-4">
            {tiers.ingress.map((node) => renderNode(node))}
          </div>
        </div>

        {/* Directed Edge Divider */}
        <div className="flex items-center justify-center text-slate-600 gap-1">
          <div className="h-[1px] w-24 bg-gradient-to-r from-transparent via-slate-700 to-transparent" />
          <ArrowRight className="w-3.5 h-3.5 rotate-90 text-cyan-400 animate-bounce" />
          <div className="h-[1px] w-24 bg-gradient-to-r from-transparent via-slate-700 to-transparent" />
        </div>

        {/* Tier 2: Core Microservices */}
        <div className="flex flex-col items-center">
          <div className="text-[10px] font-mono uppercase text-slate-400 mb-2 font-semibold tracking-wider">
            Tier 2: Core Domain Services & CI/CD
          </div>
          <div className="flex flex-wrap justify-center gap-4">
            {tiers.core.map((node) => renderNode(node))}
          </div>
        </div>

        {/* Directed Edge Divider */}
        <div className="flex items-center justify-center text-slate-600 gap-1">
          <div className="h-[1px] w-24 bg-gradient-to-r from-transparent via-slate-700 to-transparent" />
          <ArrowRight className="w-3.5 h-3.5 rotate-90 text-cyan-400 animate-bounce" />
          <div className="h-[1px] w-24 bg-gradient-to-r from-transparent via-slate-700 to-transparent" />
        </div>

        {/* Tier 3: Downstream Persistence & Adapters */}
        <div className="flex flex-col items-center">
          <div className="text-[10px] font-mono uppercase text-slate-400 mb-2 font-semibold tracking-wider">
            Tier 3: Persistence, Caching & Downstream Gateways
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            {tiers.downstream.map((node) => renderNode(node))}
          </div>
        </div>
      </div>

      {/* Legend & Latency Indicator */}
      <div className="p-2.5 border-t border-slate-800/80 bg-slate-900/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
            Crash Origin
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
            Cascading Degradation
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            Healthy Normal
          </span>
        </div>
        <div className="text-cyan-400 flex items-center gap-1">
          <Activity className="w-3 h-3" />
          <span>Real-time Mesh Telemetry</span>
        </div>
      </div>
    </div>
  );

  function renderNode(node: TopologyNode) {
    const isSelected = selectedService === node.id;
    const style = getStatusColor(node.status);
    const isRoot = data?.root_failure_node === node.id;

    return (
      <button
        key={node.id}
        onClick={() => onSelectService(node.id)}
        className={`relative flex flex-col items-start p-3 rounded-xl border backdrop-blur-md transition-all duration-200 text-left min-w-[150px] ${style.bg} ${style.border} ${style.pulse} ${
          isSelected ? 'ring-2 ring-cyan-400 scale-105' : 'hover:scale-102 hover:border-slate-600'
        }`}
      >
        {isRoot && (
          <span className="absolute -top-2 -right-2 px-1.5 py-0.5 rounded-full bg-rose-600 text-[9px] font-mono font-bold text-white shadow-lg animate-bounce">
            ROOT CAUSE
          </span>
        )}

        <div className="flex items-center justify-between w-full mb-1">
          <div className={`p-1.5 rounded-lg bg-slate-950/50 ${style.text}`}>
            {getNodeIcon(node)}
          </div>
          <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border ${style.badge}`}>
            {node.status}
          </span>
        </div>

        <span className="text-xs font-mono font-bold text-slate-100 truncate w-full">
          {node.label}
        </span>

        <div className="flex items-center justify-between w-full mt-2 pt-1 border-t border-slate-800/40 text-[10px] font-mono">
          <span className="text-slate-400">Health:</span>
          <span className={`font-bold ${style.text}`}>
            {node.health_score}%
          </span>
        </div>
      </button>
    );
  }
};
