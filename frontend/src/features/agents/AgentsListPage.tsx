import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../lib/api-client';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { useToast } from '../../components/ui/Toast';
import {
  Cpu,
  Search,
  Plus,
  MessageSquare,
  Edit2,
  MoreVertical,
  Sliders,
  Clock,
  CheckCircle2,
  Link2Off,
  Lightbulb,
  ArrowRight,
  ArrowUpRight,
  ShieldCheck,
  GitFork,
  PauseCircle,
  PlayCircle,
  Trash2,
} from 'lucide-react';

export function AgentsListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);

  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents-list'],
    queryFn: () => api.getAgents(),
  });

  const { data: routines = [] } = useQuery({
    queryKey: ['routines-list'],
    queryFn: () => api.getRoutines(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteAgent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents-list'] });
      toast.success('Agent removed', 'Agent was successfully deleted.');
      setActiveMenuId(null);
    },
  });

  const toggleStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'active' | 'paused' | 'draft' }) =>
      api.updateAgent(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents-list'] });
      toast.success('Agent status updated');
      setActiveMenuId(null);
    },
  });

  const filteredAgents = useMemo(() => {
    if (!agents) return [];
    return agents.filter((agent) => {
      const matchesQuery =
        !searchQuery.trim() ||
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.objective.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.tools.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesStatus = statusFilter === 'all' || agent.status === statusFilter;
      return matchesQuery && matchesStatus;
    });
  }, [agents, searchQuery, statusFilter]);

  const activeCount = agents?.filter((a) => a.status === 'active').length ?? 0;
  const pausedCount = agents?.filter((a) => a.status === 'paused').length ?? 0;

  const templates = [
    {
      category: 'MARKET INTEL',
      title: 'Competitive Intel Agent',
      description: 'Parses public release notes, SEC filings, and pricing changes into structured JSON updates.',
      toolsCount: 3,
      tools: ['web_search', 'parse_job_requirements', 'save_report'],
      prompt: 'Track quarterly updates and new pricing tiers across competitive developer platforms.',
    },
    {
      category: 'USER RESEARCH',
      title: 'Customer Feedback Synthesizer',
      description: 'Clusters Intercom, Discord, and Zendesk tickets to generate recurring friction matrices.',
      toolsCount: 4,
      tools: ['slack_notify', 'gmail_read', 'save_report', 'date_time'],
      prompt: 'Synthesize unread bug reports and feature requests from support channels into a weekly priority matrix.',
    },
    {
      category: 'OPERATIONS',
      title: 'Meeting Action Extractor',
      description: 'Transforms call transcripts into Linear tickets and Slack alerts with clear deliverables.',
      toolsCount: 2,
      tools: ['draft_message', 'slack_notify'],
      prompt: 'Extract action items, assignees, and deadlines from meeting notes and format for delivery.',
    },
  ];

  const handleApplyTemplate = (tmpl: typeof templates[0]) => {
    navigate('/agents/new', {
      state: {
        template: {
          name: tmpl.title,
          objective: tmpl.description,
          instructions: `You are an automated worker specialized in: ${tmpl.prompt}. Coordinate tool outputs, validate schemas, and write synthesis summaries.`,
          tools: tmpl.tools,
          model: 'google/gemini-2.5-flash',
        },
      },
    });
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-[1440px] mx-auto w-full space-y-6 lg:space-y-8 animate-in fade-in duration-200">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4 mb-2">
        <div className="flex flex-col gap-1 max-w-2xl">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[11px] text-[#0f766e] bg-[#f0fdfa] border border-[#99f6e4] px-2 py-0.5 rounded-full font-medium tracking-tight">
              ORCHESTRATION
            </span>
            <span className="font-mono text-[11px] text-[#6b7280]">•</span>
            <span className="font-mono text-[11px] text-[#6b7280]">WORKSPACE ID: prod_us_east</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-semibold text-[#111827] tracking-tight">
            Agents
          </h1>
          <p className="text-xs sm:text-sm text-[#4b5563]">
            Configure autonomous AI workers, define tool execution boundaries, and monitor task status across distributed runtime nodes.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <div className="relative flex items-center">
            <Search className="w-4 h-4 text-[#6b7280] absolute left-2.5" />
            <input
              type="text"
              placeholder="Filter agents by name or tool..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 pl-8 pr-3 w-60 sm:w-64 bg-white rounded-lg text-xs text-[#111827] placeholder:text-[#9ca3af] border border-[#e5e7eb] shadow-2xs focus:outline-none focus:border-[#0f766e]"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 px-3 bg-white text-xs font-medium text-[#4b5563] rounded-lg border border-[#e5e7eb] shadow-2xs cursor-pointer focus:outline-none focus:border-[#0f766e]"
          >
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="draft">Draft</option>
          </select>

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

      {/* 4 Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <div className="p-4 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider font-semibold text-[#6b7280]">
              Active State
            </span>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#16a34a] opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#16a34a]" />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-semibold text-[#111827]">
              {activeCount}
            </span>
            <span className="font-mono text-[11px] text-[#16a34a] font-medium">
              RUNNING
            </span>
          </div>
          <span className="text-xs text-[#6b7280] mt-1">Ready for triggers</span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider font-semibold text-[#6b7280]">
              Halted / Paused
            </span>
            <span className="h-2 w-2 rounded-full bg-[#9ca3af]" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-semibold text-[#111827]">
              {pausedCount}
            </span>
            <span className="font-mono text-[11px] text-[#6b7280]">STANDBY</span>
          </div>
          <span className="text-xs text-[#6b7280] mt-1">Zero throttled runtimes</span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider font-semibold text-[#6b7280]">
              Connected Workflows
            </span>
            <GitFork className="w-3.5 h-3.5 text-[#0f766e]" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-semibold text-[#111827]">
              {routines.length}
            </span>
            <span className="font-mono text-[11px] text-[#0f766e] font-medium">
              ROUTINES
            </span>
          </div>
          <span className="text-xs text-[#6b7280] mt-1">Synced across 2 cron-jobs</span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider font-semibold text-[#6b7280]">
              Access Scope
            </span>
            <ShieldCheck className="w-3.5 h-3.5 text-[#16a34a]" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-semibold text-[#111827]">
              100%
            </span>
            <span className="font-mono text-[11px] text-[#16a34a] font-medium">
              SECURE
            </span>
          </div>
          <span className="text-xs text-[#6b7280] mt-1">Tool permissions validated</span>
        </div>
      </div>

      {/* Configured Agents Container */}
      <div className="bg-white rounded-xl border border-[#e5e7eb] shadow-2xs overflow-hidden">
        <div className="px-5 py-3.5 bg-[#f9fafb] border-b border-[#e5e7eb] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[#111827]">
              Configured Agents
            </span>
            <span className="px-2 py-0.5 rounded-full bg-white text-[#4b5563] font-mono text-[10px] font-medium border border-[#e5e7eb]">
              {agents?.length ?? 0} total
            </span>
          </div>
          <div className="flex items-center gap-2 text-[#6b7280] text-xs font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-[#16a34a]" />
            <span>Live Telemetry</span>
          </div>
        </div>

        {/* Rows */}
        {isLoading ? (
          <div className="p-6 space-y-4 bg-white">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : filteredAgents.length === 0 ? (
          <div className="p-12 text-center text-xs text-[#6b7280] bg-white">
            No agents found matching your filter.
          </div>
        ) : (
          <div className="divide-y divide-[#e5e7eb] bg-white">
            {filteredAgents.map((agent) => {
              const linkedRoutine = routines.find((r) => r.agent_id === agent.id);

              return (
                <div
                  key={agent.id}
                  className="p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4 hover:bg-[#f9fafb] transition-colors bg-white"
                >
                  {/* Left Side: Avatar + Details + Tools */}
                  <div className="flex items-start gap-4 min-w-0 flex-1">
                    <div className="w-11 h-11 rounded-lg bg-[#f0fdfa] border border-[#99f6e4] flex items-center justify-center shrink-0 text-[#0f766e]">
                      <Cpu className="w-5 h-5" />
                    </div>

                    <div className="flex flex-col min-w-0 pr-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          onClick={() => navigate(`/agents/${agent.id}/chat`)}
                          className="text-sm font-semibold text-[#111827] tracking-tight hover:text-[#0f766e] cursor-pointer"
                        >
                          {agent.name}
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-[#f3f4f6] border border-[#e5e7eb] font-mono text-[10px] text-[#4b5563]">
                          {agent.version || 'v1.0'}
                        </span>
                        {agent.status === 'active' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#f0fdfa] text-[#0f766e] border border-[#99f6e4] text-[11px] font-medium">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#0f766e]" />
                            Autonomous
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#f9fafb] text-[#6b7280] border border-[#e5e7eb] text-[11px] font-medium">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#6b7280]" />
                            {agent.status === 'draft' ? 'Unpublished' : 'Paused'}
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-[#4b5563] mt-1 line-clamp-2 max-w-xl leading-relaxed">
                        {agent.objective}
                      </p>

                      {/* Tools row */}
                      <div className="flex flex-wrap items-center gap-1.5 mt-2.5">
                        <span className="font-mono text-[10px] text-[#6b7280] mr-1 uppercase">TOOLS:</span>
                        {agent.tools.map((tool) => (
                          <span
                            key={tool}
                            className="px-2 py-0.5 rounded bg-[#f9fafb] border border-[#e5e7eb] font-mono text-[10px] text-[#0f766e] font-medium"
                          >
                            {tool}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Right Side: Linked Routine + Last Activity + Action Buttons */}
                  <div className="flex flex-col sm:flex-row sm:items-center gap-4 lg:gap-6 shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-[#f3f4f6]">
                    {/* Linked Routine */}
                    <div className="flex flex-col gap-0.5 min-w-[150px]">
                      <span className="text-[10px] uppercase font-semibold text-[#6b7280]">
                        Linked Routine
                      </span>
                      {linkedRoutine ? (
                        <div className="flex items-center gap-1.5 text-xs text-[#111827]">
                          <Clock className="w-3.5 h-3.5 text-[#6b7280]" />
                          <span className="truncate max-w-[140px]" title={linkedRoutine.name}>
                            {linkedRoutine.name}
                          </span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-xs text-[#6b7280]">
                          <Link2Off className="w-3.5 h-3.5" />
                          <span>No routines linked</span>
                        </div>
                      )}
                    </div>

                    {/* Last Activity */}
                    <div className="flex flex-col gap-0.5 min-w-[130px]">
                      <span className="text-[10px] uppercase font-semibold text-[#6b7280]">
                        Last Activity
                      </span>
                      {agent.status === 'draft' ? (
                        <div className="flex items-center gap-1.5 text-xs text-[#6b7280]">
                          <span className="w-2 h-2 rounded-full bg-[#9ca3af]" />
                          <span className="font-mono text-[11px]">Never run</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-xs text-[#4b5563]">
                          <CheckCircle2 className="w-3.5 h-3.5 text-[#16a34a]" />
                          <span className="font-mono text-[11px]">
                            {linkedRoutine?.last_run_at ? 'Has routine history' : 'Ready'}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-1.5 relative">
                      {agent.status !== 'draft' ? (
                        <>
                          <Button
                            variant="surface"
                            size="sm"
                            onClick={() => navigate(`/agents/${agent.id}/chat`)}
                            className="h-8 shadow-2xs"
                          >
                            <MessageSquare className="w-3.5 h-3.5 text-[#6b7280]" />
                            <span>Chat</span>
                          </Button>
                          <Button
                            variant="surface"
                            size="sm"
                            onClick={() => navigate(`/agents/${agent.id}/edit`)}
                            className="h-8 shadow-2xs"
                          >
                            <Edit2 className="w-3.5 h-3.5 text-[#6b7280]" />
                            <span>Edit</span>
                          </Button>
                        </>
                      ) : (
                        <Button
                          variant="surface"
                          size="sm"
                          onClick={() => navigate(`/agents/${agent.id}/edit`)}
                          className="h-8 shadow-2xs"
                        >
                          <Sliders className="w-3.5 h-3.5 text-[#6b7280]" />
                          <span>Configure</span>
                        </Button>
                      )}

                      {/* Dropdown 3 dots menu */}
                      <div className="relative">
                        <button
                          onClick={() => setActiveMenuId(activeMenuId === agent.id ? null : agent.id)}
                          className="w-8 h-8 rounded-lg hover:bg-[#f3f4f6] border border-transparent hover:border-[#e5e7eb] flex items-center justify-center text-[#6b7280] hover:text-[#111827] transition-colors cursor-pointer"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>

                        {activeMenuId === agent.id && (
                          <div className="absolute right-0 top-full mt-1 w-44 bg-white border border-[#e5e7eb] rounded-lg shadow-lg py-1 z-20 animate-in fade-in-0 duration-100">
                            {agent.status === 'active' ? (
                              <button
                                onClick={() => toggleStatusMutation.mutate({ id: agent.id, status: 'paused' })}
                                className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#4b5563] hover:bg-[#f9fafb] text-left cursor-pointer"
                              >
                                <PauseCircle className="w-3.5 h-3.5" />
                                <span>Pause Agent</span>
                              </button>
                            ) : (
                              <button
                                onClick={() => toggleStatusMutation.mutate({ id: agent.id, status: 'active' })}
                                className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#4b5563] hover:bg-[#f9fafb] text-left cursor-pointer"
                              >
                                <PlayCircle className="w-3.5 h-3.5" />
                                <span>Activate Agent</span>
                              </button>
                            )}
                            <button
                              onClick={() => {
                                navigate(`/routines/new?agent_id=${agent.id}`);
                                setActiveMenuId(null);
                              }}
                              className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#4b5563] hover:bg-[#f9fafb] text-left cursor-pointer"
                            >
                              <Clock className="w-3.5 h-3.5" />
                              <span>Create Routine</span>
                            </button>
                            <div className="h-px bg-[#e5e7eb] my-1" />
                            <button
                              onClick={() => deleteMutation.mutate(agent.id)}
                              className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#dc2626] hover:bg-[#fee2e2] text-left cursor-pointer"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                              <span>Delete Agent</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Inspiration Recipes Section */}
      <div className="bg-[#f9fafb] rounded-xl p-5 sm:p-6 border border-[#e5e7eb] shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#f0fdfa] text-[#0f766e] border border-[#99f6e4] flex items-center justify-center shrink-0">
              <Lightbulb className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-[#111827]">
                Need inspiration?
              </h2>
              <p className="text-xs text-[#4b5563]">
                Start immediately using battle-tested agent recipes tuned for common automated tasks.
              </p>
            </div>
          </div>
          <button
            onClick={() => handleApplyTemplate(templates[0])}
            className="text-xs font-medium text-[#0f766e] hover:underline flex items-center gap-1 self-start md:self-auto cursor-pointer"
          >
            <span>Browse all 18 templates</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {templates.map((tmpl) => (
            <div
              key={tmpl.title}
              onClick={() => handleApplyTemplate(tmpl)}
              className="p-4 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs hover:border-[#0f766e]/40 hover:shadow-sm transition-all flex flex-col justify-between group cursor-pointer"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#f3f4f6] text-[#6b7280] group-hover:text-[#0f766e] transition-colors border border-[#e5e7eb]">
                    {tmpl.category}
                  </span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-[#6b7280] group-hover:translate-x-0.5 group-hover:text-[#0f766e] transition-all" />
                </div>
                <span className="text-xs font-semibold text-[#111827] block mb-1">
                  {tmpl.title}
                </span>
                <p className="text-xs text-[#4b5563] leading-relaxed">
                  {tmpl.description}
                </p>
              </div>

              <div className="flex items-center gap-2 mt-4 pt-2 border-t border-[#f3f4f6]">
                <span className="font-mono text-[10px] text-[#6b7280]">
                  {tmpl.toolsCount} tools bundled
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
