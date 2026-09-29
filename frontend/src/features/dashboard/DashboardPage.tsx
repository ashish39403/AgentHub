import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, mockDb } from '../../lib/api-client';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../components/ui/Table';
import { Skeleton, TableSkeleton } from '../../components/ui/Skeleton';
import { useToast } from '../../components/ui/Toast';
import { formatRelativeTime } from '../../lib/utils';
import {
  Cpu,
  RefreshCw,
  BarChart3,
  AlertCircle,
  Clock,
  History,
  Plus,
  Search,
  SlidersHorizontal,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Link as LinkIcon,
  Touchpad,
  Calendar,
} from 'lucide-react';

export function DashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [searchFilter, setSearchFilter] = useState('');
  const [auditLogOpen, setAuditLogOpen] = useState(false);

  // Queries
  const { data: summary, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => api.getDashboardSummary(),
  });

  const { data: recentRuns, isLoading: isRunsLoading } = useQuery({
    queryKey: ['dashboard-recent-runs'],
    queryFn: () => api.getRecentRuns(),
  });

  const { data: actionItems, isLoading: isActionsLoading } = useQuery({
    queryKey: ['dashboard-action-items'],
    queryFn: () => api.getActionItems(),
  });

  // Dismiss Action item mutation
  const dismissMutation = useMutation({
    mutationFn: (id: string) => api.dismissActionItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-action-items'] });
      toast.info('Action item dismissed');
    },
  });

  // Retry Run mutation
  const retryMutation = useMutation({
    mutationFn: (routineId: string) => api.triggerRoutineRun(routineId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-recent-runs'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      toast.success('Run dispatched', 'Execution retried in background.');
    },
  });

  const filteredRuns = useMemo(() => {
    if (!recentRuns) return [];
    if (!searchFilter.trim()) return recentRuns;
    const q = searchFilter.toLowerCase();
    return recentRuns.filter(
      (run) => {
        const routine = mockDb.routines.find((r) => r.id === run.routine_id);
        const agent = mockDb.agents.find((a) => a.id === run.agent_id);
        return (
          routine?.name.toLowerCase().includes(q) ||
          agent?.name.toLowerCase().includes(q) ||
          run.status.toLowerCase().includes(q) ||
          run.tools_executed.some((t) => t.toLowerCase().includes(q))
        );
      }
    );
  }, [recentRuns, searchFilter]);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-[1440px] mx-auto w-full space-y-6 lg:space-y-8 animate-in fade-in duration-200">
      {/* Top Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-1.5 text-[#6b7280] font-mono text-[11px] tracking-wider uppercase">
            <span>Orchestration</span>
            <span>/</span>
            <span>Workspace Prod</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-semibold text-[#111827] tracking-tight">
            Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-[#4b5563]">
            Overview of autonomous agents, active routines, and system execution health
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <Button
            variant="surface"
            size="md"
            onClick={() => setAuditLogOpen(!auditLogOpen)}
            className="shadow-2xs"
          >
            <History className="w-4 h-4 text-[#6b7280]" />
            <span>View audit log</span>
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={() => navigate('/agents/new')}
            className="shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>New Agent</span>
          </Button>
        </div>
      </div>

      {/* Audit Log Drawer / Alert if open */}
      {auditLogOpen && (
        <div className="p-4 rounded-xl bg-white border border-[#e5e7eb] shadow-xs space-y-2 animate-in slide-in-from-top-2">
          <div className="flex items-center justify-between pb-2 border-b border-[#e5e7eb]">
            <span className="text-xs font-semibold text-[#111827]">
              Workspace Audit Stream
            </span>
            <span className="text-[11px] font-mono text-[#6b7280]">Last 24 hours</span>
          </div>
          <div className="space-y-1 text-xs font-mono text-[#4b5563]">
            <div className="flex items-center justify-between py-1 border-b border-[#f3f4f6]">
              <span>[09:14:02 UTC] Routine "Internship Scout Live Run" triggered by Elena Vance</span>
              <span className="text-[#16a34a]">200 OK</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-[#f3f4f6]">
              <span>[08:01:24 UTC] Routine "Morning inbox digest" completed (1m 24s)</span>
              <span className="text-[#16a34a]">200 OK</span>
            </div>
            <div className="flex items-center justify-between py-1">
              <span>[Yesterday 09:00 UTC] Routine "Weekly internship report" rate limited</span>
              <span className="text-[#dc2626]">429 TOO MANY REQUESTS</span>
            </div>
          </div>
        </div>
      )}

      {/* Stat Tiles Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Tile 1: Active Agents */}
        <div className="bg-white rounded-xl p-4 border border-[#e5e7eb] shadow-2xs flex flex-col justify-between h-[132px] hover:border-[#0f766e]/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#4b5563]">Active Agents</span>
            <Cpu className="w-4 h-4 text-[#6b7280]" />
          </div>
          <div className="flex items-baseline justify-between mt-auto">
            <div>
              <div className="text-3xl font-semibold text-[#111827] tracking-tight leading-none mb-1.5">
                {isSummaryLoading ? <Skeleton className="h-8 w-12" /> : summary?.active_agents_count ?? 2}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-[#0f766e] font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-[#16a34a]" />
                <span>{summary?.healthy_agents_count ?? 2} healthy</span>
              </div>
            </div>
            <div className="flex items-center gap-1 text-[11px] font-mono bg-[#f0fdfa] text-[#0f766e] px-1.5 py-0.5 rounded border border-[#99f6e4]">
              <span>+1 this month</span>
            </div>
          </div>
        </div>

        {/* Tile 2: Active Routines */}
        <div className="bg-white rounded-xl p-4 border border-[#e5e7eb] shadow-2xs flex flex-col justify-between h-[132px] hover:border-[#0f766e]/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#4b5563]">Active Routines</span>
            <RefreshCw className="w-4 h-4 text-[#6b7280]" />
          </div>
          <div className="flex items-baseline justify-between mt-auto">
            <div>
              <div className="text-3xl font-semibold text-[#111827] tracking-tight leading-none mb-1.5">
                {isSummaryLoading ? <Skeleton className="h-8 w-12" /> : summary?.active_routines_count ?? 4}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-[#4b5563]">
                <Clock className="w-3.5 h-3.5 text-[#6b7280]" />
                <span>
                  Next run in <span className="font-mono text-[#111827] font-medium">{summary?.next_routine_in_minutes ?? 42}m</span>
                </span>
              </div>
            </div>
            {/* Visual mini bar spark indicator */}
            <div className="w-12 h-6 flex items-end gap-1 opacity-85 pb-0.5">
              <span className="w-2 bg-[#e5e7eb] rounded-t h-2.5" />
              <span className="w-2 bg-[#e5e7eb] rounded-t h-3.5" />
              <span className="w-2 bg-[#99f6e4] rounded-t h-5" />
              <span className="w-2 bg-[#0f766e] rounded-t h-6" />
            </div>
          </div>
        </div>

        {/* Tile 3: Runs this week */}
        <div className="bg-white rounded-xl p-4 border border-[#e5e7eb] shadow-2xs flex flex-col justify-between h-[132px] hover:border-[#0f766e]/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#4b5563]">Runs this week</span>
            <BarChart3 className="w-4 h-4 text-[#6b7280]" />
          </div>
          <div className="flex items-baseline justify-between mt-auto">
            <div>
              <div className="text-3xl font-semibold text-[#111827] tracking-tight leading-none mb-1.5">
                {isSummaryLoading ? <Skeleton className="h-8 w-16" /> : summary?.runs_this_week_count ?? 148}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-[#16a34a] font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{summary?.success_rate_percentage ?? 98.6}% success rate</span>
              </div>
            </div>
            {/* Line Chart Sparkline */}
            <svg className="w-16 h-7 text-[#0f766e] overflow-visible" fill="none" viewBox="0 0 64 24">
              <path d="M1 18 L12 16 L24 20 L36 10 L48 12 L63 2" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" />
              <path d="M1 18 L12 16 L24 20 L36 10 L48 12 L63 2 V24 H1 Z" fill="currentColor" fillOpacity="0.08" />
            </svg>
          </div>
        </div>

        {/* Tile 4: Failed runs */}
        <div className="bg-white rounded-xl p-4 border border-[#e5e7eb] shadow-2xs flex flex-col justify-between h-[132px] hover:border-[#dc2626]/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#4b5563]">Failed runs</span>
            <AlertCircle className="w-4 h-4 text-[#dc2626]" />
          </div>
          <div className="flex items-baseline justify-between mt-auto">
            <div>
              <div className="text-3xl font-semibold text-[#dc2626] tracking-tight leading-none mb-1.5">
                {isSummaryLoading ? <Skeleton className="h-8 w-8" /> : summary?.failed_runs_count ?? 2}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-[#dc2626] font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-[#dc2626]" />
                <span>Needs review</span>
              </div>
            </div>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-[#fef2f2] text-[#dc2626] border border-[#fecaca]">
              Attention
            </span>
          </div>
        </div>
      </div>

      {/* System Action Items Section */}
      {actionItems && actionItems.length > 0 && (
        <div className="space-y-2.5">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase tracking-wider font-semibold text-[#6b7280]">
                System Action Items
              </span>
              <span className="px-1.5 py-0.2 rounded-full bg-[#fef2f2] text-[#dc2626] font-mono text-[10px] font-semibold">
                {actionItems.length}
              </span>
            </div>
            <button
              onClick={() => {
                actionItems.forEach((item) => dismissMutation.mutate(item.id));
              }}
              className="text-xs text-[#6b7280] hover:text-[#111827] transition-colors cursor-pointer"
            >
              Mark all acknowledged
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {actionItems.map((item) => {
              const isWarning = item.level === 'warning';

              return (
                <div
                  key={item.id}
                  className="bg-white rounded-xl p-4 border border-[#e5e7eb] shadow-2xs flex flex-col justify-between relative overflow-hidden"
                >
                  {/* Accent bar on left */}
                  <div
                    className={`absolute top-0 left-0 bottom-0 w-1 ${
                      isWarning ? 'bg-amber-500' : 'bg-[#dc2626]'
                    }`}
                  />

                  <div className="flex items-start gap-3.5 pl-1.5">
                    <div
                      className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                        isWarning
                          ? 'bg-amber-50 text-amber-600'
                          : 'bg-red-50 text-[#dc2626]'
                      }`}
                    >
                      {isWarning ? <AlertTriangle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                    </div>

                    <div className="flex flex-col min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-semibold text-[#111827] truncate">
                          {item.title}
                        </span>
                        {item.badge_text && (
                          <span
                            className={`font-mono text-[11px] px-2 py-0.5 rounded shrink-0 font-medium ${
                              isWarning
                                ? 'bg-amber-50 text-amber-700'
                                : 'bg-[#fef2f2] text-[#dc2626]'
                            }`}
                          >
                            {item.badge_text}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[#4b5563] mt-1 leading-relaxed">
                        {item.description}
                      </p>
                    </div>
                  </div>

                  {/* Card Actions */}
                  <div className="flex items-center justify-end gap-2.5 mt-4 pt-2 border-t border-[#f3f4f6] pl-1.5">
                    <button
                      onClick={() => dismissMutation.mutate(item.id)}
                      className="h-8 px-2.5 rounded-lg text-xs font-medium text-[#4b5563] hover:bg-[#f3f4f6] transition-colors"
                    >
                      {item.secondary_action_label || 'Dismiss'}
                    </button>

                    {item.target_url && (
                      <Button
                        variant="surface"
                        size="sm"
                        onClick={() => {
                          if (item.action_label === 'Retry') {
                            retryMutation.mutate('rtn_weekly_scout');
                          } else {
                            navigate(item.target_url!);
                          }
                        }}
                        className="shadow-2xs"
                      >
                        {item.action_label === 'Retry' ? (
                          <RotateCcw className="w-3.5 h-3.5" />
                        ) : (
                          <LinkIcon className="w-3.5 h-3.5" />
                        )}
                        <span>{item.action_label || 'Action'}</span>
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent Runs Table Section */}
      <div className="bg-white rounded-xl border border-[#e5e7eb] shadow-2xs overflow-hidden flex flex-col">
        {/* Table Header Filter Bar */}
        <div className="px-4 py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#e5e7eb] bg-white">
          <div className="flex items-center gap-2.5">
            <span className="text-sm font-semibold text-[#111827]">Recent Runs</span>
            <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-[#f9fafb] text-[#6b7280] border border-[#e5e7eb]">
              Live stream
            </span>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-[#6b7280] absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Filter routine..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="h-8 pl-8 pr-3 rounded-lg bg-[#f9fafb] text-xs text-[#111827] placeholder:text-[#9ca3af] border border-[#e5e7eb] focus:outline-none focus:border-[#0f766e]"
              />
            </div>

            <Button variant="outline" size="sm" className="h-8">
              <SlidersHorizontal className="w-3.5 h-3.5 text-[#6b7280]" />
              <span>View</span>
            </Button>
          </div>
        </div>

        {/* Table Body */}
        {isRunsLoading ? (
          <TableSkeleton rows={4} cols={7} />
        ) : (
          <Table>
            <TableHeader>
              <tr>
                <TableHead className="w-32">Status</TableHead>
                <TableHead>Routine / Agent</TableHead>
                <TableHead>Trigger</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Tools Executed</TableHead>
                <TableHead>Started At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </tr>
            </TableHeader>
            <TableBody>
              {filteredRuns.length === 0 ? (
                <tr>
                  <TableCell colSpan={7} className="text-center py-8 text-xs text-[#6b7280]">
                    No routine runs match your filter criteria.
                  </TableCell>
                </tr>
              ) : (
                filteredRuns.map((run) => {
                  const routine = mockDb.routines.find((r) => r.id === run.routine_id);
                  const agent = mockDb.agents.find((a) => a.id === run.agent_id);

                  return (
                    <TableRow key={run.id}>
                      {/* Status */}
                      <TableCell className="whitespace-nowrap">
                        <Badge status={run.status} />
                      </TableCell>

                      {/* Routine / Agent */}
                      <TableCell>
                        <div className="flex flex-col min-w-0">
                          <span
                            onClick={() => navigate(`/routines/${run.routine_id}/runs/${run.id}`)}
                            className="font-medium text-xs text-[#111827] hover:text-[#0f766e] transition-colors cursor-pointer truncate"
                          >
                            {routine?.name || 'Manual Run'}
                          </span>
                          <span className="text-[11px] text-[#6b7280] truncate">
                            {agent?.name || 'Autonomous Agent'}
                          </span>
                        </div>
                      </TableCell>

                      {/* Trigger */}
                      <TableCell className="whitespace-nowrap">
                        <div className="inline-flex items-center gap-1 font-mono text-[11px] text-[#4b5563] bg-[#f9fafb] px-2 py-0.5 rounded border border-[#e5e7eb]">
                          {run.trigger === 'manual' ? (
                            <>
                              <Touchpad className="w-3 h-3 text-[#6b7280]" />
                              <span>Manual</span>
                            </>
                          ) : (
                            <>
                              <Calendar className="w-3 h-3 text-[#6b7280]" />
                              <span>{routine?.schedule.includes('0 8') ? '08:00 UTC' : routine?.schedule.includes('0 9') ? 'Mon 09:00' : 'Hourly'}</span>
                            </>
                          )}
                        </div>
                      </TableCell>

                      {/* Duration */}
                      <TableCell className="whitespace-nowrap">
                        <span className={`font-mono text-xs ${run.status === 'running' ? 'text-[#0f766e] font-medium' : 'text-[#4b5563]'}`}>
                          {run.duration || '—'}
                        </span>
                      </TableCell>

                      {/* Tools Executed */}
                      <TableCell>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {run.tools_executed.map((tool, idx) => (
                            <span
                              key={idx}
                              className={`font-mono text-[10px] px-1.5 py-0.5 rounded border ${
                                run.status === 'running' && idx === 0
                                  ? 'bg-[#f0fdfa] text-[#0f766e] border-[#99f6e4] font-medium animate-pulse'
                                  : run.status === 'failed'
                                  ? 'bg-[#fef2f2] text-[#dc2626] border-[#fecaca]'
                                  : 'bg-[#f9fafb] text-[#4b5563] border-[#e5e7eb]'
                              }`}
                            >
                              {tool}
                            </span>
                          ))}
                        </div>
                      </TableCell>

                      {/* Started At */}
                      <TableCell className="whitespace-nowrap">
                        <span className="font-mono text-[11px] text-[#6b7280]">
                          {formatRelativeTime(run.started_at)}
                        </span>
                      </TableCell>

                      {/* Actions */}
                      <TableCell className="text-right whitespace-nowrap">
                        <button
                          onClick={() => navigate(`/routines/${run.routine_id}/runs/${run.id}`)}
                          className={`text-xs font-medium hover:underline transition-colors ${
                            run.status === 'failed'
                              ? 'text-[#dc2626]'
                              : 'text-[#0f766e]'
                          }`}
                        >
                          {run.status === 'running' ? 'Inspect' : run.status === 'failed' ? 'Debug' : 'View run'}
                        </button>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        )}

        {/* Table Footer Pagination Bar */}
        <div className="px-4 py-2.5 bg-[#f9fafb] border-t border-[#e5e7eb] flex items-center justify-between">
          <span className="font-mono text-[11px] text-[#6b7280]">
            Showing {filteredRuns.length} of {summary?.runs_this_week_count ?? 148} runs this week
          </span>
          <div className="flex items-center gap-1 text-xs">
            <button
              onClick={() => toast.info('Previous page')}
              className="px-2 py-1 rounded text-[#6b7280] hover:text-[#111827] transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => toast.info('Next page')}
              className="px-2 py-1 rounded text-[#111827] hover:bg-[#f3f4f6] transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
