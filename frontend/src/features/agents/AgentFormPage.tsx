import React, { useEffect } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ApiError, api } from '../../lib/api-client';
import { Input } from '../../components/ui/Input';
import { Textarea } from '../../components/ui/Textarea';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { useToast } from '../../components/ui/Toast';
import { Agent } from '../../types';
import { Cpu, ArrowLeft, Trash2, Sparkles, Check } from 'lucide-react';

const agentFormSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  instructions: z.string().min(5, 'Instructions are required'),
  objective: z.string().min(5, 'Objective is required'),
  model: z.string().min(1, 'Model is required'),
  temperature: z.number().min(0).max(1),
  tools: z.array(z.string()),
  version: z.string().min(1),
  status: z.enum(['active', 'paused', 'draft']),
});

type AgentFormValues = z.infer<typeof agentFormSchema>;

const modelOptions = [
  { value: 'google/gemini-2.5-flash', label: 'Gemini 2.5 Flash (default, fast)' },
  { value: 'deepseek/deepseek-v4-pro', label: 'DeepSeek V4 Pro (smart)' },
  { value: 'nvidia/nemotron-3-ultra-550b-a55b', label: 'NVIDIA Nemotron 3 Ultra 550B (reasoning)' },
  { value: 'openai/gpt-3.5-turbo-0613', label: 'OpenAI GPT-3.5 Turbo 0613 (cheap)' },
  { value: 'gpt-5-mini', label: 'GPT-5 Mini (experimental)' },
];

export function AgentFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const toast = useToast();

  const templateState = (location.state as { template?: Partial<AgentFormValues> })?.template;

  const { data: agent } = useQuery({
    queryKey: ['agent-detail', id],
    queryFn: () => (id ? api.getAgent(id) : null),
    enabled: isEdit,
  });

  const { data: availableTools = [] } = useQuery({
    queryKey: ['tool-catalog'],
    queryFn: () => api.getTools(),
  });

  const {
    register,
    handleSubmit,
    control,
    reset,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<AgentFormValues>({
    resolver: zodResolver(agentFormSchema),
    defaultValues: {
      name: '',
      objective: '',
      instructions: '',
      model: 'google/gemini-2.5-flash',
      temperature: 0.2,
      tools: ['internship_research', 'draft_message'],
      version: 'v1.0',
      status: 'active',
    },
  });

  useEffect(() => {
    if (agent) {
      reset({
        name: agent.name,
        objective: agent.objective,
        instructions: agent.instructions,
        model: agent.model || 'google/gemini-2.5-flash',
        temperature: agent.temperature ?? 0.2,
        tools: agent.tools || [],
        version: agent.version || 'v1.0',
        status: agent.status || 'active',
      });
    } else if (templateState) {
      reset({
        name: templateState.name || '',
        objective: templateState.objective || '',
        instructions: templateState.instructions || '',
        model: templateState.model || 'google/gemini-2.5-flash',
        temperature: templateState.temperature ?? 0.2,
        tools: templateState.tools || [],
        version: 'v1.0',
        status: 'active',
      });
    }
  }, [agent, templateState, reset]);

  const selectedTools = watch('tools') || [];

  const toggleTool = (toolName: string) => {
    if (selectedTools.includes(toolName)) {
      setValue('tools', selectedTools.filter((t) => t !== toolName));
    } else {
      setValue('tools', [...selectedTools, toolName]);
    }
  };

  const createMutation = useMutation({
    mutationFn: (data: AgentFormValues) => api.createAgent(data),
    onSuccess: (newAgent) => {
      queryClient.setQueryData<Agent[]>(['agents-list'], (old) =>
        old ? [newAgent, ...old.filter((agent) => agent.id !== newAgent.id)] : [newAgent]
      );
      queryClient.invalidateQueries({ queryKey: ['agents-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      toast.success('Agent initialized', `Created "${newAgent.name}" successfully.`);
      navigate('/agents');
    },
    onError: () => toast.error('Error', 'Failed to create agent.'),
  });

  const updateMutation = useMutation({
    mutationFn: (data: AgentFormValues) => api.updateAgent(id!, data),
    onSuccess: (updated) => {
      queryClient.setQueryData(['agent-detail', id], updated);
      queryClient.setQueryData(['agent-chat-detail', id], updated);
      queryClient.invalidateQueries({ queryKey: ['agents-list'] });
      queryClient.invalidateQueries({ queryKey: ['agent-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['agent-chat-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['agent-conversations', id] });
      toast.success('Agent saved', `Updated "${updated.name}" successfully.`);
      navigate('/agents');
    },
    onError: () => toast.error('Error', 'Failed to update agent.'),
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteAgent(id!),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['agents-list'] });
      const previousAgents = queryClient.getQueryData<Agent[]>(['agents-list']);

      queryClient.setQueryData<Agent[]>(['agents-list'], (old) =>
        old ? old.filter((agent) => agent.id !== id) : old
      );
      queryClient.removeQueries({ queryKey: ['agent-detail', id] });
      queryClient.removeQueries({ queryKey: ['agent-chat-detail', id] });
      queryClient.removeQueries({ queryKey: ['agent-conversations', id] });
      navigate('/agents');

      return { previousAgents };
    },
    onSuccess: () => {
      toast.success('Agent deleted');
    },
    onError: (error, _variables, context) => {
      if (error instanceof ApiError && error.status === 404) {
        toast.info('Agent was already removed.');
        return;
      }
      if (context?.previousAgents) {
        queryClient.setQueryData(['agents-list'], context.previousAgents);
      }
      toast.error('Delete failed', 'Could not delete this agent.');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['agents-list'] });
      queryClient.invalidateQueries({ queryKey: ['routines-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-recent-runs'] });
    },
  });

  const onSubmit = (data: AgentFormValues) => {
    if (isEdit) {
      updateMutation.mutate(data);
    } else {
      createMutation.mutate(data);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto w-full space-y-6 animate-in fade-in duration-200">
      {/* Top Breadcrumb & Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/agents')}
          className="flex items-center gap-1.5 text-xs text-[#6b7280] hover:text-[#111827] transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Agents</span>
        </button>

        {isEdit && (
          <Button
            variant="destructive"
            size="sm"
            onClick={() => {
              if (confirm('Are you sure you want to delete this agent?')) {
                deleteMutation.mutate();
              }
            }}
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Delete Agent</span>
          </Button>
        )}
      </div>

      {/* Header Info */}
      <div className="flex items-start gap-3.5">
        <div className="w-10 h-10 rounded-xl bg-[#f0fdfa] text-[#0f766e] border border-[#99f6e4] flex items-center justify-center shrink-0">
          <Cpu className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-[#111827] tracking-tight">
            {isEdit ? `Configure Agent: ${agent?.name || 'Loading...'}` : 'Create New Agent'}
          </h1>
          <p className="text-xs text-[#4b5563] mt-0.5">
            Define system instructions, operational boundary rules, and execution tool scopes.
          </p>
        </div>
      </div>

      {/* Form Container */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Core Info Card */}
        <div className="p-5 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs space-y-4">
          <h2 className="text-sm font-semibold text-[#111827] pb-2 border-b border-[#f3f4f6]">
            Identity & Objective
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Agent Name"
              placeholder="e.g. Internship Scout"
              error={errors.name?.message}
              {...register('name')}
            />

            <Select
              label="Status"
              error={errors.status?.message}
              {...register('status')}
              options={[
                { value: 'active', label: 'Active (Autonomous triggers enabled)' },
                { value: 'paused', label: 'Paused (Standby)' },
                { value: 'draft', label: 'Draft (Unpublished)' },
              ]}
            />
          </div>

          <Textarea
            label="Primary Objective"
            hint="High-level mission summarized in telemetry"
            placeholder="e.g. Researches top AI research internships across verified ATS boards and drafts weekly report."
            rows={2}
            error={errors.objective?.message}
            {...register('objective')}
          />

          <Textarea
            label="System Instructions & Operational Boundaries"
            hint="Guidance on behavior, reasoning steps, tool calling constraints"
            placeholder="You are an autonomous talent research assistant. Use the internship_research tool to query verified career boards..."
            rows={5}
            mono
            error={errors.instructions?.message}
            {...register('instructions')}
          />
        </div>

        {/* Runtime & Model Parameters */}
        <div className="p-5 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs space-y-4">
          <h2 className="text-sm font-semibold text-[#111827] pb-2 border-b border-[#f3f4f6]">
            Runtime Model & Parameters
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select
              label="Foundation Model"
              error={errors.model?.message}
              {...register('model')}
              options={modelOptions}
            />

            <Controller
              name="temperature"
              control={control}
              render={({ field }) => (
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between text-xs font-medium text-[#111827]">
                    <span>Temperature</span>
                    <span className="font-mono text-[#0f766e]">{field.value}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={field.value}
                    onChange={(e) => field.onChange(parseFloat(e.target.value))}
                    className="w-full accent-[#0f766e] cursor-pointer"
                  />
                  <span className="text-[11px] text-[#6b7280]">
                    Lower values (0.0-0.3) provide surgical determinism for tool calls.
                  </span>
                </div>
              )}
            />
          </div>
        </div>

        {/* Tools Scope Card */}
        <div className="p-5 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-[#f3f4f6]">
            <div>
              <h2 className="text-sm font-semibold text-[#111827]">
                Tool Execution Scope
              </h2>
              <p className="text-xs text-[#4b5563]">
                Attach verified integrations and system tools for this agent to invoke.
              </p>
            </div>
            <span className="font-mono text-xs text-[#0f766e] font-medium">
              {selectedTools.length} selected
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {availableTools.map((tool) => {
              const isSelected = selectedTools.includes(tool.name);

              return (
                <div
                  key={tool.id}
                  onClick={() => toggleTool(tool.name)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-start justify-between gap-3 ${
                    isSelected
                      ? 'bg-[#f0fdfa] border-[#0f766e]'
                      : 'bg-white border-[#e5e7eb] hover:border-[#9ca3af]'
                  }`}
                >
                  <div className="flex flex-col min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-[#111827]">
                        {tool.name}
                      </span>
                      <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-[#f3f4f6] text-[#6b7280] border border-[#e5e7eb]">
                        {tool.category}
                      </span>
                    </div>
                    <p className="text-xs text-[#4b5563] mt-1 leading-relaxed">
                      {tool.description}
                    </p>
                    {tool.requiredPermissions && (
                      <span className="text-[10px] text-[#6b7280] font-mono mt-1">
                        Scope: {tool.requiredPermissions.join(', ')}
                      </span>
                    )}
                  </div>

                  <div
                    className={`w-5 h-5 rounded-md border flex items-center justify-center shrink-0 mt-0.5 transition-colors ${
                      isSelected
                        ? 'bg-[#0f766e] border-[#0f766e] text-white'
                        : 'border-[#d1d5db]'
                    }`}
                  >
                    {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Submit Actions */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Button
            type="button"
            variant="surface"
            onClick={() => navigate('/agents')}
          >
            Cancel
          </Button>

          <Button
            type="submit"
            variant="primary"
            isLoading={isSubmitting || createMutation.isPending || updateMutation.isPending}
          >
            <Sparkles className="w-4 h-4" />
            <span>{isEdit ? 'Save Changes' : 'Create Agent'}</span>
          </Button>
        </div>
      </form>
    </div>
  );
}
