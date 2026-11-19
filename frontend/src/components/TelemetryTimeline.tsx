import React, { useState } from 'react';
import { MetricPoint } from '../types';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts';
import { TrendingUp, Cpu, Clock, AlertTriangle, GitCommit } from 'lucide-react';

interface TelemetryTimelineProps {
  timeline: MetricPoint[];
  serviceName: string;
}

export const TelemetryTimeline: React.FC<TelemetryTimelineProps> = ({
  timeline,
  serviceName
}) => {
  const [metricTab, setMetricTab] = useState<'latency_error' | 'cpu_memory'>('latency_error');

  if (!timeline || timeline.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 p-6 bg-[#0b101d] border border-slate-800 rounded-xl text-slate-500 font-mono text-xs">
        <Clock className="w-6 h-6 mb-2 animate-spin" />
        <span>Aggregating TimeSeries Telemetry Metrics...</span>
      </div>
    );
  }

  // Find deployment marker point
  const deployPoint = timeline.find((p) => p.is_deployment_marker);

  // Calculate peaks
  const peakLatency = Math.max(...timeline.map((p) => p.latency_ms || 0));
  const peakCpu = Math.max(...timeline.map((p) => p.cpu_percent || 0));
  const peakErrorRate = Math.max(...timeline.map((p) => p.error_rate || 0));

  const formatTimeLabel = (timestamp: string) => {
    try {
      const d = new Date(timestamp);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return timestamp;
    }
  };

  const chartData = timeline.map((p) => ({
    ...p,
    formattedTime: formatTimeLabel(p.timestamp)
  }));

  return (
    <div className="flex flex-col bg-[#0b101d] border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Header & Metric View Switcher */}
      <div className="p-3.5 border-b border-slate-800/80 bg-slate-900/60 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">
            Pre-Crash Telemetry Timeline
          </h2>
          <span className="text-xs font-mono text-slate-400">
            ({serviceName} · 15m Window)
          </span>
        </div>

        <div className="flex items-center gap-1 bg-slate-950/80 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setMetricTab('latency_error')}
            className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
              metricTab === 'latency_error'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Latency & Error Rate
          </button>
          <button
            onClick={() => setMetricTab('cpu_memory')}
            className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
              metricTab === 'cpu_memory'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            CPU & Memory
          </button>
        </div>
      </div>

      {/* KPI Stats Bar */}
      <div className="grid grid-cols-3 gap-2 p-3 bg-slate-950/40 border-b border-slate-800/60 text-xs font-mono">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
          <Clock className="w-3.5 h-3.5 text-rose-400" />
          <div>
            <div className="text-[10px] text-slate-400">Peak Latency</div>
            <div className="text-sm font-bold text-rose-400">{peakLatency} ms</div>
          </div>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
          <Cpu className="w-3.5 h-3.5 text-amber-400" />
          <div>
            <div className="text-[10px] text-slate-400">Peak CPU</div>
            <div className="text-sm font-bold text-amber-400">{peakCpu}%</div>
          </div>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          <div>
            <div className="text-[10px] text-slate-400">Peak Error Rate</div>
            <div className="text-sm font-bold text-rose-400">{peakErrorRate}%</div>
          </div>
        </div>
      </div>

      {/* Deployment Banner if present */}
      {deployPoint && deployPoint.deployment_info && (
        <div className="mx-3 mt-3 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-between text-xs font-mono text-amber-300">
          <div className="flex items-center gap-2">
            <GitCommit className="w-3.5 h-3.5 text-amber-400" />
            <span>Deployment Trigger: {deployPoint.deployment_info}</span>
          </div>
          <span className="text-[10px] text-amber-400/80 font-bold uppercase">
            Causal Anomaly Onset
          </span>
        </div>
      )}

      {/* Chart Canvas */}
      <div className="p-4 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {metricTab === 'latency_error' ? (
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="latencyGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="errorGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="formattedTime" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  fontSize: '11px',
                  fontFamily: 'monospace'
                }}
              />
              {deployPoint && (
                <ReferenceLine
                  x={formatTimeLabel(deployPoint.timestamp)}
                  stroke="#f59e0b"
                  strokeDasharray="4 4"
                  label={{ value: 'Bad Commit Deploy', fill: '#f59e0b', fontSize: 10, position: 'top' }}
                />
              )}
              <Area
                type="monotone"
                dataKey="latency_ms"
                name="Latency (ms)"
                stroke="#f43f5e"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#latencyGrad)"
              />
              <Area
                type="monotone"
                dataKey="error_rate"
                name="Error Rate (%)"
                stroke="#06b6d4"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#errorGrad)"
              />
            </AreaChart>
          ) : (
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="memGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a855f7" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#a855f7" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="formattedTime" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  fontSize: '11px',
                  fontFamily: 'monospace'
                }}
              />
              {deployPoint && (
                <ReferenceLine
                  x={formatTimeLabel(deployPoint.timestamp)}
                  stroke="#f59e0b"
                  strokeDasharray="4 4"
                  label={{ value: 'Deployment', fill: '#f59e0b', fontSize: 10, position: 'top' }}
                />
              )}
              <Area
                type="monotone"
                dataKey="cpu_percent"
                name="CPU Usage (%)"
                stroke="#f59e0b"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#cpuGrad)"
              />
              <Area
                type="monotone"
                dataKey="memory_mb"
                name="Memory (MB)"
                stroke="#a855f7"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#memGrad)"
              />
            </AreaChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};
