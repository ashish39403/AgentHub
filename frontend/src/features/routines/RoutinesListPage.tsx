import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../lib/api-client';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Switch } from '../../components/ui/Switch';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../components/ui/Table';
import { TableSkeleton } from '../../components/ui/Skeleton';
import { useToast } from '../../components/ui/Toast';
import { describeCronExpression, formatRelativeTime } from '../../lib/utils';
import {
  Clock,
  Plus,
  Play,
  Edit2,
  Trash2,
  Cpu,
  Search,
} from 'lucide-react';

export function RoutinesListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [searchQuery, setSearchQuery] = useState('');

  const { data: routines, isLoading } = useQuery({
    queryKey: ['routines-list'],
    queryFn: () => api.getRoutines(),
  });

  const { data: agents = [] } = useQuery({
    queryKey: ['agents-list'],
    queryFn: () => api.getAgents(),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      api.updateRoutine(id, { is_active }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['routines-list'] });
      toast.success(
        updated.is_active ? 'Routine activated' : 'Routine paused',
        `Schedule for "${updated.name}" updated.`
      );
    },
  });

  const triggerRunMutation = useMutation({
    mutationFn: (id: string) => api.triggerRoutineRun(id),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: ['routines-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-recent-runs'] });
      toast.success('Run triggered', 'Routine execution queued.');
      navigate(`/routines/${run.routine_id}/runs/${run.id}`);
    },
    onError: () => toast.error('Error', 'Failed to trigger run.'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteRoutine(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['routines-list'] });
      toast.success('Routine removed');
    },
  });

  const filteredRoutines = (routines || []).filter((r) => {
    const agent = agents.find((a) => a.id === r.agent_id);
    return (
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.prompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent?.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-[1440px] mx-auto w-full space-y-6 lg:space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-[#6b7280] font-mono text-[11px] uppercase tracking-wider">
            <span>Automations</span>
            <span>/</span>
            <span>Cron Orchestrator</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-semibold text-[#111827] tracking-tight">
            Routines
          </h1>
          <p className="text-xs sm:text-sm text-[#4b5563]">
            Schedule automated background jobs, recurring workflows, and multi-tool pipelines across your agents.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#6b7280] absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search routines..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 pl-8 pr-3 bg-white text-xs text-[#111827] placeholder:text-[#9ca3af] rounded-lg border border-[#e5e7eb] shadow-2xs focus:outline-none focus:border-[#0f766e]"
            />
          </div>

          <Button
            variant="primary"
            size="md"
            onClick={() => navigate('/routines/new')}
            className="shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>New Routine</span>
          </Button>
        </div>
      </div>

      {/* Routines Table */}
      <div className="bg-white rounded-xl border border-[#e5e7eb] shadow-2xs overflow-hidden">
        {isLoading ? (
          <TableSkeleton rows={4} cols={6} />
        ) : (
          <Table>
            <TableHeader>
              <tr>
                <TableHead className="w-16">Active</TableHead>
                <TableHead>Routine & Mission</TableHead>
                <TableHead>Assigned Agent</TableHead>
                <TableHead>Schedule & Cadence</TableHead>
                <TableHead>Last Execution</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </tr>
            </TableHeader>
            <TableBody>
              {filteredRoutines.length === 0 ? (
                <tr>
                  <TableCell colSpan={6} className="text-center py-10 text-xs text-[#6b7280]">
                    No routines created yet. Click "+ New Routine" to schedule your first job.
                  </TableCell>
                </tr>
              ) : (
                filteredRoutines.map((routine) => {
                  const agent = agents.find((a) => a.id === routine.agent_id);

                  return (
                    <TableRow key={routine.id}>
                      {/* Active Toggle */}
                      <TableCell>
                        <Switch
                          checked={routine.is_active}
                          onCheckedChange={(checked) =>
                            toggleActiveMutation.mutate({ id: routine.id, is_active: checked })
                          }
                        />
                      </TableCell>

                      {/* Routine & Mission */}
                      <TableCell>
                        <div className="flex flex-col min-w-0 max-w-md">
                          <span
                            onClick={() => navigate(`/routines/${routine.id}/edit`)}
                            className="font-semibold text-xs text-[#111827] hover:text-[#0f766e] transition-colors cursor-pointer truncate"
                          >
                            {routine.name}
                          </span>
                          <span className="text-xs text-[#4b5563] line-clamp-1 mt-0.5">
                            {routine.prompt}
                          </span>
                        </div>
                      </TableCell>

                      {/* Assigned Agent */}
                      <TableCell>
                        <div
                          onClick={() => agent && navigate(`/agents/${agent.id}/chat`)}
                          className="flex items-center gap-1.5 text-xs text-[#111827] hover:text-[#0f766e] cursor-pointer"
                        >
                          <Cpu className="w-3.5 h-3.5 text-[#6b7280]" />
                          <span>{agent?.name || 'Unassigned'}</span>
                        </div>
                      </TableCell>

                      {/* Schedule */}
                      <TableCell>
                        <div className="flex flex-col gap-0.5">
                          <div className="inline-flex items-center gap-1 font-mono text-[11px] text-[#0f766e] bg-[#f0fdfa] px-2 py-0.5 rounded border border-[#99f6e4] w-fit">
                            <Clock className="w-3.5 h-3.5 text-[#0f766e]" />
                            <span>{routine.schedule}</span>
                          </div>
                          <span className="text-[11px] text-[#6b7280]">
                            {describeCronExpression(routine.schedule)}
                          </span>
                        </div>
                      </TableCell>

                      {/* Last Execution */}
                      <TableCell>
                        <div className="flex flex-col gap-1">
                          {routine.last_run_status ? (
                            <Badge status={routine.last_run_status} />
                          ) : (
                            <span className="text-[11px] text-[#6b7280]">Never run</span>
                          )}
                          {routine.last_run_at && (
                            <span className="font-mono text-[10px] text-[#6b7280]">
                              {formatRelativeTime(routine.last_run_at)}
                            </span>
                          )}
                        </div>
                      </TableCell>

                      {/* Actions */}
                      <TableCell className="text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            variant="surface"
                            size="sm"
                            onClick={() => triggerRunMutation.mutate(routine.id)}
                            isLoading={triggerRunMutation.isPending}
                            title="Trigger immediate execution"
                            className="h-8 shadow-2xs"
                          >
                            <Play className="w-3.5 h-3.5 fill-current" />
                            <span>Run</span>
                          </Button>

                          <Button
                            variant="surface"
                            size="sm"
                            onClick={() => navigate(`/routines/${routine.id}/edit`)}
                            className="h-8 shadow-2xs"
                          >
                            <Edit2 className="w-3.5 h-3.5 text-[#6b7280]" />
                          </Button>

                          <button
                            onClick={() => {
                              if (confirm(`Delete routine "${routine.name}"?`)) {
                                deleteMutation.mutate(routine.id);
                              }
                            }}
                            className="p-1.5 rounded text-[#6b7280] hover:text-[#dc2626] transition-colors cursor-pointer"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
