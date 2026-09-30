import { z } from 'zod';

export type StatusType = 'queued' | 'running' | 'succeeded' | 'failed' | 'active' | 'paused' | 'draft';

// User & Auth
export const UserSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string(),
  avatar_url: z.string().optional(),
  role: z.string().default('admin'),
  workspace_id: z.string().default('prod_us_east'),
  created_at: z.string(),
});
export type User = z.infer<typeof UserSchema>;

export const AuthResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.literal('Bearer'),
  expires_in: z.number().optional(),
  user: UserSchema,
});
export type AuthResponse = z.infer<typeof AuthResponseSchema>;

// Agent
export const AgentSchema = z.object({
  id: z.string(),
  name: z.string().min(2, 'Name must be at least 2 characters'),
  instructions: z.string().min(5, 'Instructions are required'),
  objective: z.string().min(5, 'Objective is required'),
  model: z.string().default('google/gemini-2.5-flash'),
  temperature: z.number().min(0).max(1).default(0.7),
  tools: z.array(z.string()).default([]),
  version: z.string().default('v1.0'),
  status: z.enum(['active', 'paused', 'draft']).default('active'),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Agent = z.infer<typeof AgentSchema>;

export const AgentCreateInputSchema = AgentSchema.omit({
  id: true,
  created_at: true,
  updated_at: true,
});
export type AgentCreateInput = z.infer<typeof AgentCreateInputSchema>;

export const AgentUpdateInputSchema = AgentCreateInputSchema.partial();
export type AgentUpdateInput = z.infer<typeof AgentUpdateInputSchema>;

// Tool Definition
export interface ToolDefinition {
  id: string;
  name: string;
  displayName: string;
  description: string;
  category: 'search' | 'communication' | 'code' | 'system' | 'productivity' | 'internal' | 'memory' | 'action' | 'integration';
  requiredPermissions?: string[];
  isBuiltIn?: boolean;
  safety_level?: string;
  requires_confirmation?: boolean;
}

// Conversation & Messages
export interface ToolCallPayload {
  id: string;
  tool_name: string;
  input: Record<string, unknown>;
  output?: Record<string, unknown> | string;
  status: 'running' | 'succeeded' | 'failed';
  duration_ms?: number;
  error?: string;
}

export const MessageSchema = z.object({
  id: z.string(),
  conversation_id: z.string(),
  role: z.enum(['user', 'assistant', 'tool', 'system']),
  content: z.string(),
  tool_calls: z.array(z.custom<ToolCallPayload>()).nullable().optional(),
  created_at: z.string(),
});
export type Message = z.infer<typeof MessageSchema>;

export const ConversationSchema = z.object({
  id: z.string(),
  agent_id: z.string(),
  title: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Conversation = z.infer<typeof ConversationSchema>;

// Routine
export const RoutineSchema = z.object({
  id: z.string(),
  agent_id: z.string(),
  name: z.string().min(2, 'Name must be at least 2 characters'),
  prompt: z.string().min(5, 'Prompt is required'),
  schedule: z.string().min(1, 'Schedule is required (e.g. cron or preset)'),
  timezone: z.string().default('UTC'),
  is_active: z.boolean().default(true),
  last_run_at: z.string().nullable().optional(),
  last_run_status: z.enum(['queued', 'running', 'succeeded', 'failed']).nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Routine = z.infer<typeof RoutineSchema>;

export const RoutineCreateInputSchema = RoutineSchema.omit({
  id: true,
  last_run_at: true,
  last_run_status: true,
  created_at: true,
  updated_at: true,
});
export type RoutineCreateInput = z.infer<typeof RoutineCreateInputSchema>;

export const RoutineUpdateInputSchema = RoutineCreateInputSchema.partial();
export type RoutineUpdateInput = z.infer<typeof RoutineUpdateInputSchema>;

// Routine Run
export const RoutineRunSchema = z.object({
  id: z.string(),
  routine_id: z.string(),
  agent_id: z.string(),
  status: z.enum(['queued', 'running', 'succeeded', 'failed']),
  trigger: z.enum(['scheduled', 'manual']).default('scheduled'),
  output: z.string().nullable().optional(),
  error: z.string().nullable().optional(),
  duration: z.string().optional(),
  started_at: z.string(),
  finished_at: z.string().nullable().optional(),
  tools_executed: z.array(z.string()).default([]),
});
export type RoutineRun = z.infer<typeof RoutineRunSchema>;

// Tool Action Log
export const ToolActionLogSchema = z.object({
  id: z.string(),
  agent_id: z.string(),
  routine_run_id: z.string().nullable().optional(),
  tool_name: z.string(),
  input: z.record(z.string(), z.unknown()),
  output: z.union([z.record(z.string(), z.unknown()), z.string()]).nullable().optional(),
  status: z.enum(['succeeded', 'failed']),
  error: z.string().nullable().optional(),
  duration_ms: z.number().optional(),
  created_at: z.string(),
});
export type ToolActionLog = z.infer<typeof ToolActionLogSchema>;

// System Action Items & Alerts
export interface ActionItem {
  id: string;
  title: string;
  description: string;
  level: 'warning' | 'error' | 'info';
  badge_text?: string;
  target_url?: string;
  action_label?: string;
  secondary_action_label?: string;
  time_remaining?: string;
  acknowledged?: boolean;
  created_at: string;
}

// Dashboard Summary
export interface DashboardSummary {
  active_agents_count: number;
  healthy_agents_count: number;
  active_routines_count: number;
  next_routine_in_minutes: number;
  runs_this_week_count: number;
  success_rate_percentage: number;
  failed_runs_count: number;
  runs_trend_data: number[];
}

// Integrations
export interface Integration {
  id: string;
  name: string;
  provider: 'gmail' | 'github' | 'slack' | 'linear' | 'notion' | 'custom_webhook';
  description: string;
  status: 'connected' | 'disconnected' | 'pending' | 'expiring_soon' | 'error';
  scopes: string[];
  last_synced_at?: string;
  expires_at?: string;
  icon: string;
  account_email?: string;
  configured?: boolean;
  connected?: boolean;
  message?: string;
  connect_url?: string;
}

// Standard API Error
export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
