import React, { useState } from 'react';
import { Incident, IncidentMatch, Runbook } from '../types';
import {
  FileCode2,
  GitCommit,
  Sparkles,
  Terminal,
  Copy,
  Check,
  Play,
  History,
  ShieldCheck,
  Cpu
} from 'lucide-react';

interface RootCauseDiffViewProps {
  incident: Incident;
  topMatch: IncidentMatch | null;
  matchedRunbook: Runbook | null;
  aiAnalysis: string;
  onExecuteRunbook: (runbookId: string) => void;
  isExecutingRunbook: boolean;
}

export const RootCauseDiffView: React.FC<RootCauseDiffViewProps> = ({
  incident,
  topMatch,
  matchedRunbook,
  aiAnalysis,
  onExecuteRunbook,
  isExecutingRunbook
}) => {
  const [activeTab, setActiveTab] = useState<'stack_trace' | 'git_diff'>('stack_trace');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopyCommand = (cmd: string, idx: number) => {
    navigator.clipboard.writeText(cmd);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const similarityScore = topMatch ? Math.round(topMatch.similarity_score * 100) : null;

  return (
    <div className="flex flex-col bg-[#0b101d] border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="p-3.5 border-b border-slate-800/80 bg-slate-900/60 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">
            Root-Cause Analysis & Semantic Deduplication
          </h2>
        </div>

        {topMatch && similarityScore && (
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/40 text-xs font-mono text-cyan-300">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>
              {similarityScore}% Match to Historical Incident{' '}
              <strong className="text-white">#{topMatch.incident_id}</strong>
            </span>
          </div>
        )}
      </div>

      {/* AI Synthesis Executive Summary Card */}
      <div className="p-4 bg-gradient-to-r from-purple-950/30 via-slate-900/40 to-slate-900/30 border-b border-slate-800/80">
        <div className="flex items-center gap-2 mb-2 text-xs font-mono font-bold text-purple-300">
          <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />
          <span>Autonomous AI Root-Cause Synthesis (Gemini 2.5 Flash)</span>
        </div>
        <p className="text-xs text-slate-200 leading-relaxed font-sans bg-slate-950/50 p-3 rounded-lg border border-purple-500/20 shadow-inner">
          {aiAnalysis || incident.root_cause_summary || 'Analyzing causal graph and stack trace patterns...'}
        </p>
      </div>

      {/* Tab Switcher: Stack Trace vs Git Diff */}
      <div className="px-4 pt-3 flex items-center justify-between border-b border-slate-800/80 bg-slate-950/40">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('stack_trace')}
            className={`flex items-center gap-1.5 pb-2.5 text-xs font-mono transition-colors border-b-2 ${
              activeTab === 'stack_trace'
                ? 'border-cyan-400 text-cyan-300 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileCode2 className="w-3.5 h-3.5" />
            Stack Trace Deduplication
          </button>
          <button
            onClick={() => setActiveTab('git_diff')}
            className={`flex items-center gap-1.5 pb-2.5 text-xs font-mono transition-colors border-b-2 ${
              activeTab === 'git_diff'
                ? 'border-cyan-400 text-cyan-300 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <GitCommit className="w-3.5 h-3.5" />
            Git Commit Diff ({incident.git_metadata?.commit_hash?.slice(0, 7) || 'N/A'})
          </button>
        </div>

        {incident.git_metadata?.author && (
          <span className="text-[11px] font-mono text-slate-400 pb-2">
            Author: <strong className="text-slate-300">{incident.git_metadata.author}</strong>
          </span>
        )}
      </div>

      {/* Code / Trace Viewer Panel */}
      <div className="p-4 bg-slate-950 font-mono text-xs overflow-x-auto max-h-72 border-b border-slate-800/80">
        {activeTab === 'stack_trace' ? (
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                <span>Active Crash Normalized Stack Trace</span>
                <span className="text-[10px] text-rose-400 font-semibold">Active Outage</span>
              </div>
              <pre className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-rose-200/90 overflow-x-auto text-[11px] leading-snug">
                {incident.raw_stack_trace || incident.normalized_stack_trace || incident.error_message}
              </pre>
            </div>

            {topMatch && (
              <div>
                <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                  <span className="flex items-center gap-1">
                    <History className="w-3 h-3 text-cyan-400" />
                    Closest Historical Match: #{topMatch.incident_id} ({similarityScore}% Vector Similarity)
                  </span>
                  <span className="text-[10px] text-emerald-400 font-semibold">Past Outage Resolved</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/60 border border-cyan-500/20 text-slate-300 text-[11px]">
                  <p className="font-semibold text-cyan-300 mb-1">{topMatch.title}</p>
                  <p className="text-slate-400">{topMatch.service_name} · Runbook #{topMatch.runbook_id || 'N/A'}</p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2">
              <span className="font-semibold text-slate-200">
                Commit: {incident.git_metadata?.commit_message || 'Recent commit deployment'}
              </span>
              <span className="text-slate-400 font-mono">
                Branch: {incident.git_metadata?.branch || 'main'}
              </span>
            </div>

            {incident.git_metadata?.diff_summary ? (
              <pre className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-[11px] leading-relaxed">
                {incident.git_metadata.diff_summary.split('\n').map((line, idx) => {
                  const isAdd = line.startsWith('+');
                  const isSub = line.startsWith('-');
                  const isHunk = line.startsWith('@@');
                  const color = isAdd ? 'text-emerald-400 bg-emerald-950/20' : isSub ? 'text-rose-400 bg-rose-950/20' : isHunk ? 'text-cyan-400' : 'text-slate-400';
                  return (
                    <div key={idx} className={`${color} px-1.5 py-0.5 rounded-sm`}>
                      {line}
                    </div>
                  );
                })}
              </pre>
            ) : (
              <div className="p-4 text-center text-slate-400 text-xs">
                No git diff attached to this incident.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Matched Verified Runbook Card */}
      {matchedRunbook ? (
        <div className="p-4 bg-slate-900/70">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <div className="p-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-xs font-bold text-slate-100 font-mono">
                    {matchedRunbook.title}
                  </h3>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
                    {matchedRunbook.runbook_id}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[10px] font-mono text-slate-400 mt-0.5">
                  <span className="text-emerald-400 font-semibold">
                    Success Rate: {Math.round(matchedRunbook.success_rate * 100)}%
                  </span>
                  <span>·</span>
                  <span>Avg MTTR: {matchedRunbook.average_recovery_time_sec}s</span>
                </div>
              </div>
            </div>

            {/* Execute Runbook Action Button */}
            <button
              disabled={isExecutingRunbook || incident.status === 'RESOLVED'}
              onClick={() => onExecuteRunbook(matchedRunbook.runbook_id)}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all shadow-md ${
                incident.status === 'RESOLVED'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 cursor-default'
                  : 'bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white border border-emerald-400/40 hover:scale-[1.02] active:scale-[0.98]'
              }`}
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>
                {incident.status === 'RESOLVED'
                  ? 'Mitigation Verified'
                  : isExecutingRunbook
                  ? 'Self-Healing in Progress...'
                  : 'Execute Autonomous Self-Healing'}
              </span>
            </button>
          </div>

          {/* Remediation Commands */}
          <div className="space-y-2">
            <div className="text-[10px] font-mono uppercase text-slate-400 font-semibold">
              Verified Remediation Commands:
            </div>
            {matchedRunbook.remediation_commands.map((cmd, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between gap-2 p-2 rounded-lg bg-slate-950/80 border border-slate-800 font-mono text-xs text-cyan-300 group hover:border-slate-700"
              >
                <div className="flex items-center gap-2 overflow-x-auto">
                  <Terminal className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                  <code className="text-[11px] whitespace-nowrap text-slate-200">{cmd}</code>
                </div>

                <button
                  onClick={() => handleCopyCommand(cmd, idx)}
                  className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex-shrink-0"
                >
                  {copiedIndex === idx ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="p-6 text-center text-slate-400 text-xs font-mono">
          No automated runbook mapped yet. AI suggests standard container restart or roll-forward.
        </div>
      )}
    </div>
  );
};
