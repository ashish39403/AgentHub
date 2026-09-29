import React, { useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, mockDb } from '../../lib/api-client';
import { Input } from '../../components/ui/Input';
import { Textarea } from '../../components/ui/Textarea';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { Switch } from '../../components/ui/Switch';
import { useToast } from '../../components/ui/Toast';
import { describeCronExpression } from '../../lib/utils';
import { Clock, ArrowLeft, Sparkles, Check } from 'lucide-react';

const routineFormSchema = z.object({
  agent_id: z.string().min(1, 'Agent is required'),
  name: z.string().min(2, 'Name must be at least 2 characters'),
  prompt: z.string().min(5, 'Prompt is required'),
  schedule: z.string().min(1, 'Schedule is required'),
  timezone: z.string().min(1, 'Timezone is required'),
  is_active: z.boolean(),
});

type RoutineFormValues = z.infer<typeof routineFormSchema>;

export function RoutineFormPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const defaultAgentId = searchParams.get('agent_id') || mockDb.agents[0]?.id || '';
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: routine } = useQuery({
    queryKey: ['routine-detail', id],
    queryFn: () => (id ? api.getRoutine(id) : null),
    enabled: isEdit,
  });

  const {
    register,
    handleSubmit,
    control,
    reset,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<RoutineFormValues>({
    resolver: zodResolver(routineFormSchema),
    defaultValues: {
      agent_id: defaultAgentId,
      name: '',
      prompt: '',
      schedule: '0 8 * * *',
      timezone: 'UTC',
      is_active: true,
    },
  });

  useEffect(() => {
    if (routine) {
      reset({
        agent_id: routine.agent_id,
        name: routine.name,
        prompt: routine.prompt,
        schedule: routine.schedule,
        timezone: routine.timezone || 'UTC',
        is_active: routine.is_active,
      });
    }
  }, [routine, reset]);

  const currentSchedule = watch('schedule') || '';

  const presets = [
    { label: 'Daily at 08:00 UTC', value: '0 8 * * *' },
    { label: 'Weekly on Monday at 09:00 UTC', value: '0 9 * * 1' },
    { label: 'Hourly', value: '0 * * * *' },
    { label: 'Every 5 minutes', value: '*/5 * * * *' },
    { label: 'Weekdays at 18:00 UTC', value: '0 18 * * 1-5' },
  ];

  const createMutation = useMutation({
    mutationFn: (data: RoutineFormValues) => api.createRoutine(data),
    onSuccess: (newRoutine) => {
      queryClient.invalidateQueries({ queryKey: ['routines-list'] });
      toast.success('Routine scheduled', `Created routine "${newRoutine.name}".`);
      navigate('/routines');
    },
    onError: () => toast.error('Error', 'Failed to create routine.'),
  });

  const updateMutation = useMutation({
    mutationFn: (data: RoutineFormValues) => api.updateRoutine(id!, data),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['routines-list'] });
      queryClient.invalidateQueries({ queryKey: ['routine-detail', id] });
      toast.success('Routine updated', `Saved "${updated.name}".`);
      navigate('/routines');
    },
    onError: () => toast.error('Error', 'Failed to update routine.'),
  });

  const onSubmit = (data: RoutineFormValues) => {
    if (isEdit) {
      updateMutation.mutate(data);
    } else {
      createMutation.mutate(data);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto w-full space-y-6 animate-in fade-in duration-200">
      {/* Top Breadcrumb */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/routines')}
          className="flex items-center gap-1.5 text-xs text-[#6b7280] hover:text-[#111827] transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Routines</span>
        </button>
      </div>

      {/* Header Info */}
      <div className="flex items-start gap-3.5">
        <div className="w-10 h-10 rounded-xl bg-[#f0fdfa] text-[#0f766e] border border-[#99f6e4] flex items-center justify-center shrink-0">
          <Clock className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-[#111827] tracking-tight">
            {isEdit ? `Edit Routine: ${routine?.name || 'Loading...'}` : 'Create Recurring Routine'}
          </h1>
          <p className="text-xs text-[#4b5563] mt-0.5">
            Configure automated cron jobs, prompt instructions, and assigned AI agents.
          </p>
        </div>
      </div>

      {/* Form Container */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Core Config */}
        <div className="p-5 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs space-y-4">
          <h2 className="text-sm font-semibold text-[#111827] pb-2 border-b border-[#f3f4f6]">
            Job Specification
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Routine Name"
              placeholder="e.g. Weekly internship report"
              error={errors.name?.message}
              {...register('name')}
            />

            <Select
              label="Assigned Agent"
              error={errors.agent_id?.message}
              {...register('agent_id')}
              options={mockDb.agents.map((a) => ({
                value: a.id,
                label: `${a.name} (${a.tools.length} tools)`,
              }))}
            />
          </div>

          <Textarea
            label="Execution Prompt"
            hint="The exact instruction dispatched to the agent on each run"
            placeholder="e.g. Scrape AI engineering internships from the past 24 hours and format as markdown digest..."
            rows={4}
            error={errors.prompt?.message}
            {...register('prompt')}
          />
        </div>

        {/* Schedule & Timing Card */}
        <div className="p-5 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs space-y-4">
          <h2 className="text-sm font-semibold text-[#111827] pb-2 border-b border-[#f3f4f6]">
            Cadence & Schedule (Cron)
          </h2>

          {/* Preset Buttons */}
          <div className="space-y-1.5">
            <span className="text-xs font-medium text-[#111827]">Quick Presets</span>
            <div className="flex flex-wrap gap-2">
              {presets.map((p) => {
                const isSelected = currentSchedule === p.value;
                return (
                  <button
                    key={p.value}
                    type="button"
                    onClick={() => setValue('schedule', p.value)}
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-[#f0fdfa] text-[#0f766e] border-[#0f766e]'
                        : 'bg-white text-[#4b5563] border-[#e5e7eb] hover:border-[#9ca3af]'
                    }`}
                  >
                    {p.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <Input
                label="Cron Expression"
                mono
                placeholder="0 8 * * *"
                error={errors.schedule?.message}
                {...register('schedule')}
              />
              <div className="mt-1.5 p-2 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] flex items-center gap-2">
                <span className="text-[11px] font-mono text-[#6b7280]">Preview:</span>
                <span className="text-xs font-medium text-[#0f766e]">
                  {describeCronExpression(currentSchedule)}
                </span>
              </div>
            </div>

            <Select
              label="Timezone"
              error={errors.timezone?.message}
              {...register('timezone')}
              options={[
                { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
                { value: 'America/New_York', label: 'America/New_York (EST/EDT)' },
                { value: 'America/Los_Angeles', label: 'America/Los_Angeles (PST/PDT)' },
                { value: 'Europe/London', label: 'Europe/London (GMT/BST)' },
                { value: 'Asia/Tokyo', label: 'Asia/Tokyo (JST)' },
              ]}
            />
          </div>

          <div className="pt-2 border-t border-[#f3f4f6]">
            <Controller
              name="is_active"
              control={control}
              render={({ field }) => (
                <Switch
                  label="Enable routine schedule"
                  description="When active, background workers will trigger this job according to the cron cadence."
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              )}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Button
            type="button"
            variant="surface"
            onClick={() => navigate('/routines')}
          >
            Cancel
          </Button>

          <Button
            type="submit"
            variant="primary"
            isLoading={isSubmitting || createMutation.isPending || updateMutation.isPending}
          >
            <Sparkles className="w-4 h-4" />
            <span>{isEdit ? 'Save Routine' : 'Schedule Routine'}</span>
          </Button>
        </div>
      </form>
    </div>
  );
}
