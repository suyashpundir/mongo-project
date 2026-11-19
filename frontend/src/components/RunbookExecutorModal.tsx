import React from 'react';
import { RemediationLogStep } from '../types';
import { Terminal, CheckCircle2, Clock, X, ShieldCheck } from 'lucide-react';

interface RunbookExecutorModalProps {
  isOpen: boolean;
  onClose: () => void;
  runbookTitle: string;
  runbookId: string;
  logs: RemediationLogStep[];
  isComplete: boolean;
}

export const RunbookExecutorModal: React.FC<RunbookExecutorModalProps> = ({
  isOpen,
  onClose,
  runbookTitle,
  runbookId,
  logs,
  isComplete
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-2xl bg-[#0b101d] border border-cyan-500/40 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
              <Terminal className="w-4 h-4 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                Autonomous Self-Healing Execution
                <span className="text-[10px] text-cyan-400 font-semibold px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/30">
                  {runbookId}
                </span>
              </h3>
              <p className="text-xs text-slate-400 font-sans">{runbookTitle}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Console / Terminal Body */}
        <div className="p-4 bg-slate-950 font-mono text-xs space-y-3 max-h-96 overflow-y-auto">
          {logs.map((log, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-300 space-y-1.5"
            >
              <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-2">
                  <span className="text-cyan-400 font-bold">
                    [Step {log.step_index}/{log.total_steps}]
                  </span>
                  <span className="text-slate-200">{log.step_description}</span>
                </div>
                {log.status === 'SUCCESS' ? (
                  <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-bold uppercase">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Passed
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[10px] text-cyan-400 font-bold uppercase animate-pulse">
                    <Clock className="w-3.5 h-3.5 animate-spin" />
                    Executing...
                  </span>
                )}
              </div>

              <div className="p-2 rounded bg-black/60 border border-slate-800/80 text-[11px] text-slate-400">
                <span className="text-emerald-400">$</span> {log.command}
              </div>

              {log.output && (
                <div className="text-[10px] text-slate-400 pl-1 font-mono">
                  {log.output}
                </div>
              )}
            </div>
          ))}

          {isComplete && (
            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <div>
                  <div className="font-bold text-xs">Self-Healing Verification Complete</div>
                  <div className="text-[10px] text-emerald-400/80">
                    Health probes returned 200 OK. Incident transitioned to RESOLVED.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-3.5 border-t border-slate-800 bg-slate-900/60 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors"
          >
            {isComplete ? 'Close & Review' : 'Dismiss'}
          </button>
        </div>
      </div>
    </div>
  );
};
