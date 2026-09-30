import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../lib/api-client';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { useToast } from '../../components/ui/Toast';
import { formatDateTime, formatRelativeTime } from '../../lib/utils';
import {
  ArrowLeft,
  RotateCcw,
  Terminal,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

export function RoutineRunDetailsPage() {
  const { routineId, runId } = useParams<{ routineId: string; runId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: run, isLoading: isRunLoading } = useQuery({
    queryKey: ['routine-run-detail', routineId, runId],
    queryFn: () => (routineId && runId ? api.getRoutineRun(routineId, runId) : null),
    enabled: !!routineId && !!runId,
  });

  const { data: routine } = useQuery({
    queryKey: ['routine-detail', routineId],
    queryFn: () => (routineId ? api.getRoutine(routineId) : null),
    enabled: !!routineId,
  });

  const { data: agent } = useQuery({
    queryKey: ['agent-detail', run?.agent_id],
    queryFn: () => (run?.agent_id ? api.getAgent(run.agent_id) : null),
    enabled: !!run?.agent_id,
  });

  const { data: toolLogs } = useQuery({
    queryKey: ['run-tool-logs', routineId, runId],
    queryFn: () => (routineId && runId ? api.getToolLogsForRun(routineId, runId) : []),
    enabled: !!routineId && !!runId,
  });

  const retryMutation = useMutation({
    mutationFn: (rId: string) => api.triggerRoutineRun(rId),
    onSuccess: (newRun) => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-recent-runs'] });
      toast.success('Run dispatched', 'Execution retried in background.');
      navigate(`/routines/${newRun.routine_id}/runs/${newRun.id}`);
    },
  });

  if (isRunLoading) {
    return <div className="p-8 text-center text-xs text-[#6b7280]">Loading run details...</div>;
  }

  if (!run) {
    return (
      <div className="p-8 text-center text-xs text-[#6b7280]">
        Run not found.{' '}
        <button onClick={() => navigate('/routines')} className="text-[#0f766e] underline cursor-pointer">
          Back to routines
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto w-full space-y-6 animate-in fade-in duration-200">
      {/* Top Breadcrumb */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-1.5 text-xs text-[#6b7280] hover:text-[#111827] transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        <Button
          variant="primary"
          size="sm"
          onClick={() => routine && retryMutation.mutate(routine.id)}
          isLoading={retryMutation.isPending}
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Re-run Execution</span>
        </Button>
      </div>

      {/* Header Summary Card */}
      <div className="p-5 sm:p-6 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#f3f4f6]">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-[#f0fdfa] border border-[#99f6e4] text-[#0f766e] flex items-center justify-center shrink-0">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-semibold text-[#111827] tracking-tight">
                  {routine?.name || 'Execution Run'}
                </h1>
                <Badge status={run.status} />
              </div>
              <p className="text-xs text-[#4b5563] mt-0.5 font-mono">
                Run ID: {run.id} • Trigger: {run.trigger}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="surface"
              size="sm"
              onClick={() => agent && navigate(`/agents/${agent.id}/chat`)}
            >
              <span>Open Agent Chat</span>
            </Button>
          </div>
        </div>

        {/* 4 Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-1">
          <div>
            <span className="text-[11px] uppercase tracking-wider font-semibold text-[#6b7280] block">
              Agent
            </span>
            <span className="text-xs font-semibold text-[#111827] mt-0.5 block">
              {agent?.name || 'Autonomous Agent'}
            </span>
          </div>

          <div>
            <span className="text-[11px] uppercase tracking-wider font-semibold text-[#6b7280] block">
              Duration
            </span>
            <span className="font-mono text-xs font-semibold text-[#111827] mt-0.5 block">
              {run.duration || '—'}
            </span>
          </div>

          <div>
            <span className="text-[11px] uppercase tracking-wider font-semibold text-[#6b7280] block">
              Started At
            </span>
            <span className="font-mono text-xs text-[#4b5563] mt-0.5 block">
              {formatDateTime(run.started_at)}
            </span>
          </div>

          <div>
            <span className="text-[11px] uppercase tracking-wider font-semibold text-[#6b7280] block">
              Finished At
            </span>
            <span className="font-mono text-xs text-[#4b5563] mt-0.5 block">
              {run.finished_at ? formatDateTime(run.finished_at) : 'In progress'}
            </span>
          </div>
        </div>
      </div>

      {/* Error Output Card if Failed */}
      {run.error && (
        <div className="p-4 rounded-xl bg-[#fef2f2] border border-[#fecaca] text-[#dc2626] space-y-2">
          <div className="flex items-center gap-2 font-semibold text-xs">
            <AlertCircle className="w-4 h-4" />
            <span>Execution Error Trace</span>
          </div>
          <p className="font-mono text-xs leading-relaxed bg-white/70 p-3 rounded-lg border border-[#fecaca]">
            {run.error}
          </p>
        </div>
      )}

      {/* Output Artifact / Result Canvas */}
      {run.output && (
        <div className="p-5 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#f3f4f6]">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#16a34a]" />
              <h2 className="text-xs font-semibold text-[#111827] uppercase tracking-wider">
                Run Output Artifact
              </h2>
            </div>
            <span className="font-mono text-[10px] text-[#6b7280]">Markdown synthesis</span>
          </div>

          <div className="p-4 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] text-xs sm:text-sm text-[#111827] leading-relaxed whitespace-pre-wrap font-sans">
            {run.output}
          </div>
        </div>
      )}

      {/* Tool Action Log Timeline */}
      <div className="p-5 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-[#f3f4f6]">
          <div>
            <h2 className="text-sm font-semibold text-[#111827]">
              Tool Action Execution Timeline
            </h2>
            <p className="text-xs text-[#4b5563]">
              Chronological log of system integrations and remote API calls executed during this run.
            </p>
          </div>
          <span className="font-mono text-xs text-[#0f766e] font-medium">
            {toolLogs?.length ?? 0} actions recorded
          </span>
        </div>

        <div className="space-y-3">
          {(toolLogs || []).map((log, index) => (
            <div
              key={log.id}
              className="p-3.5 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-semibold text-[#0f766e]">
                    #{index + 1} {log.tool_name}
                  </span>
                  <span
                    className={`font-mono text-[10px] px-1.5 py-0.2 rounded border ${
                      log.status === 'succeeded'
                        ? 'bg-[#f0fdf4] text-[#15803d] border-[#bbf7d0]'
                        : 'bg-[#fef2f2] text-[#dc2626] border-[#fecaca]'
                    }`}
                  >
                    {log.status.toUpperCase()}
                  </span>
                </div>
                <span className="font-mono text-[10px] text-[#6b7280]">
                  {formatRelativeTime(log.created_at)}
                </span>
              </div>

              {/* Input / Output payload preview */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-white border border-[#e5e7eb]">
                  <span className="text-[10px] uppercase text-[#6b7280] block mb-1">Input Arguments</span>
                  <div className="text-[#4b5563] truncate">
                    {JSON.stringify(log.input)}
                  </div>
                </div>

                <div className="p-2 rounded bg-white border border-[#e5e7eb]">
                  <span className="text-[10px] uppercase text-[#6b7280] block mb-1">Response Data</span>
                  <div className="text-[#4b5563] truncate">
                    {typeof log.output === 'object' ? JSON.stringify(log.output) : log.output || '—'}
                  </div>
                </div>
              </div>

              {log.error && (
                <div className="text-xs font-mono text-[#dc2626] bg-[#fef2f2] p-2 rounded border border-[#fecaca]">
                  Error: {log.error}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
