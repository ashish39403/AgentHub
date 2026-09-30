import {
  Agent,
  AgentCreateInput,
  AgentUpdateInput,
  Conversation,
  Message,
  Routine,
  RoutineCreateInput,
  RoutineUpdateInput,
  RoutineRun,
  ToolActionLog,
  ActionItem,
  DashboardSummary,
  Integration,
  User,
  AuthResponse,
  ApiErrorResponse,
  ToolCallPayload,
  ToolDefinition,
} from '../types';
import {
  initialAgents,
  initialRoutines,
  initialRecentRuns,
  initialToolLogs,
  initialActionItems,
  initialSummary,
  initialConversations,
  initialMessages,
  initialIntegrations,
  mockUser,
} from './mock-data';

export class ApiError extends Error {
  code: string;
  details?: Record<string, unknown>;
  status: number;

  constructor(message: string, code: string = 'UNKNOWN_ERROR', status: number = 500, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

// In-memory token storage
let accessToken: string | null = null;
let refreshToken: string | null = null;

export const tokenStorage = {
  getAccessToken: () => accessToken,
  setAccessToken: (token: string | null) => {
    accessToken = token;
  },
  getRefreshToken: () => refreshToken || localStorage.getItem('agenthub_refresh_token'),
  setRefreshToken: (token: string | null) => {
    refreshToken = token;
    if (token) {
      localStorage.setItem('agenthub_refresh_token', token);
    } else {
      localStorage.removeItem('agenthub_refresh_token');
    }
  },
  clear: () => {
    accessToken = null;
    refreshToken = null;
    localStorage.removeItem('agenthub_refresh_token');
  },
};

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const API_PREFIX = `${BASE_URL}/api/v1`;
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';
const FALLBACK_TO_MOCKS = import.meta.env.VITE_FALLBACK_TO_MOCKS === 'true';

// Local Storage synced Mock Database for rich interactivity in mock mode
class MockDatabase {
  agents: Agent[];
  routines: Routine[];
  runs: RoutineRun[];
  toolLogs: ToolActionLog[];
  actionItems: ActionItem[];
  summary: DashboardSummary;
  conversations: Conversation[];
  messages: Record<string, Message[]>;
  integrations: Integration[];
  currentUser: User;

  constructor() {
    this.agents = this.load('agenthub_mock_agents', initialAgents);
    this.routines = this.load('agenthub_mock_routines', initialRoutines);
    this.runs = this.load('agenthub_mock_runs', initialRecentRuns);
    this.toolLogs = this.load('agenthub_mock_tool_logs', initialToolLogs);
    this.actionItems = this.load('agenthub_mock_action_items', initialActionItems);
    this.summary = this.load('agenthub_mock_summary', initialSummary);
    this.conversations = this.load('agenthub_mock_conversations', initialConversations);
    this.messages = this.load('agenthub_mock_messages', initialMessages);
    this.integrations = this.load('agenthub_mock_integrations', initialIntegrations);
    this.currentUser = mockUser;
  }

  private load<T>(key: string, fallback: T): T {
    try {
      const stored = localStorage.getItem(key);
      if (stored) return JSON.parse(stored);
    } catch {
      // fallback
    }
    return fallback;
  }

  save() {
    try {
      localStorage.setItem('agenthub_mock_agents', JSON.stringify(this.agents));
      localStorage.setItem('agenthub_mock_routines', JSON.stringify(this.routines));
      localStorage.setItem('agenthub_mock_runs', JSON.stringify(this.runs));
      localStorage.setItem('agenthub_mock_tool_logs', JSON.stringify(this.toolLogs));
      localStorage.setItem('agenthub_mock_action_items', JSON.stringify(this.actionItems));
      localStorage.setItem('agenthub_mock_conversations', JSON.stringify(this.conversations));
      localStorage.setItem('agenthub_mock_messages', JSON.stringify(this.messages));
      localStorage.setItem('agenthub_mock_integrations', JSON.stringify(this.integrations));
    } catch {
      // ignore
    }
  }

  reset() {
    this.agents = [...initialAgents];
    this.routines = [...initialRoutines];
    this.runs = [...initialRecentRuns];
    this.toolLogs = [...initialToolLogs];
    this.actionItems = [...initialActionItems];
    this.summary = { ...initialSummary };
    this.conversations = [...initialConversations];
    this.messages = { ...initialMessages };
    this.integrations = [...initialIntegrations];
    this.save();
  }
}

export const mockDb = new MockDatabase();

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function onRefreshed(token: string) {
  refreshSubscribers.map((cb) => cb(token));
  refreshSubscribers = [];
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  if (USE_MOCKS) {
    // Artificial small latency for realistic feedback
    await new Promise((r) => setTimeout(r, 60));
    return handleMockRequest<T>(endpoint, options);
  }

  const url = `${API_PREFIX}${endpoint}`;
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');

  const token = tokenStorage.getAccessToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401 && !endpoint.includes('/auth/')) {
      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const refreshTokenVal = tokenStorage.getRefreshToken();
          if (!refreshTokenVal) throw new Error('No refresh token');

          const refreshRes = await fetch(`${API_PREFIX}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshTokenVal }),
          });

          if (!refreshRes.ok) throw new Error('Refresh failed');
          const refreshData = normalizeAuthResponse(await refreshRes.json());
          tokenStorage.setAccessToken(refreshData.access_token);
          isRefreshing = false;
          onRefreshed(refreshData.access_token);

          // Retry original request
          headers.set('Authorization', `Bearer ${refreshData.access_token}`);
          const retryRes = await fetch(url, { ...options, headers });
          return handleResponse<T>(retryRes);
        } catch {
          isRefreshing = false;
          tokenStorage.clear();
          window.location.href = '/login';
          throw new ApiError('Session expired. Please log in again.', 'UNAUTHORIZED', 401);
        }
      } else {
        return new Promise<T>((resolve, reject) => {
          refreshSubscribers.push(async (newToken) => {
            try {
              headers.set('Authorization', `Bearer ${newToken}`);
              const retryRes = await fetch(url, { ...options, headers });
              resolve(await handleResponse<T>(retryRes));
            } catch (err) {
              reject(err);
            }
          });
        });
      }
    }

    return handleResponse<T>(response);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (!FALLBACK_TO_MOCKS) {
      throw new ApiError('Could not connect to the backend API.', 'NETWORK_ERROR', 0);
    }
    return handleMockRequest<T>(endpoint, options);
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type');
  const isJson = contentType && contentType.includes('application/json');

  if (!response.ok) {
    if (isJson) {
      const errorData: ApiErrorResponse = await response.json().catch(() => ({
        error: { code: 'HTTP_ERROR', message: response.statusText },
      }));
      throw new ApiError(
        errorData.error.message || 'Request failed',
        errorData.error.code || 'UNKNOWN_ERROR',
        response.status,
        errorData.error.details
      );
    }
    throw new ApiError(response.statusText || 'Request failed', 'HTTP_ERROR', response.status);
  }

  if (isJson) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}

function normalizeUser(raw: any): User {
  return {
    id: String(raw.id),
    email: raw.email,
    name: raw.name,
    avatar_url: raw.avatar_url,
    role: raw.role || 'admin',
    workspace_id: raw.workspace_id || 'local_workspace',
    created_at: raw.created_at || new Date().toISOString(),
  };
}

function normalizeAuthResponse(raw: any): AuthResponse {
  const access = raw.access_token || raw.tokens?.access_token;
  const refresh = raw.refresh_token || raw.tokens?.refresh_token;
  const normalized: AuthResponse = {
    access_token: access,
    token_type: 'Bearer',
    expires_in: raw.expires_in,
    user: normalizeUser(raw.user),
  };
  tokenStorage.setAccessToken(access);
  tokenStorage.setRefreshToken(refresh || null);
  return normalized;
}

const backendToFrontendTool: Record<string, string> = {
  datetime: 'date_time',
  gmail_summary: 'gmail_read',
  send_slack_message: 'slack_notify',
  github_issue_search: 'github_api',
};

const frontendToBackendTool: Record<string, string> = {
  internship_research: 'web_search',
  date_time: 'datetime',
  gmail_read: 'gmail_summary',
  slack_notify: 'send_slack_message',
  github_api: 'github_issue_search',
  parse_job_requirements: 'summarize_text',
  save_report: 'save_memory',
};

function normalizeToolNameForFrontend(toolName: string): string {
  return backendToFrontendTool[toolName] || toolName;
}

function normalizeToolNameForBackend(toolName: string): string {
  return frontendToBackendTool[toolName] || toolName;
}

function normalizeAgent(raw: any): Agent {
  const tools = (raw.tools || raw.enabled_tools || []).map(normalizeToolNameForFrontend);
  return {
    id: String(raw.id),
    name: raw.name,
    objective: raw.objective,
    instructions: raw.instructions,
    model: raw.model || 'google/gemini-2.5-flash',
    temperature: raw.temperature ?? 0.2,
    tools,
    version: raw.version || 'v1.0',
    status: raw.status || 'active',
    created_at: raw.created_at,
    updated_at: raw.updated_at,
  };
}

function toBackendAgentPayload(input: AgentCreateInput | AgentUpdateInput): Record<string, unknown> {
  return {
    name: input.name,
    objective: input.objective,
    instructions: input.instructions,
    model: input.model,
    temperature: input.temperature,
    enabled_tools: input.tools?.map(normalizeToolNameForBackend),
  };
}

function normalizeConversation(raw: any): Conversation {
  return {
    id: String(raw.id),
    agent_id: String(raw.agent_id),
    title: raw.title || 'New Conversation',
    created_at: raw.created_at,
    updated_at: raw.updated_at,
  };
}

function normalizeToolCalls(rawToolCalls: any): ToolCallPayload[] | null {
  if (!rawToolCalls) return null;
  const rawCalls = Array.isArray(rawToolCalls) ? rawToolCalls : [rawToolCalls];
  return rawCalls.map((call, index) => ({
    id: String(call.id || `tool_${index}_${Date.now()}`),
    tool_name: call.tool_name || call.name || 'tool',
    input: call.input || {},
    output: call.output,
    status: call.status || 'succeeded',
    duration_ms: call.duration_ms,
    error: call.error,
  }));
}

function normalizeMessage(raw: any): Message {
  return {
    id: String(raw.id),
    conversation_id: String(raw.conversation_id),
    role: raw.role,
    content: raw.content,
    tool_calls: normalizeToolCalls(raw.tool_calls),
    created_at: raw.created_at,
  };
}

function normalizeConversationDetail(raw: any): Conversation & { messages: Message[] } {
  return {
    ...normalizeConversation(raw),
    messages: (raw.messages || []).map(normalizeMessage),
  };
}

function normalizeRoutine(raw: any): Routine {
  return {
    id: String(raw.id),
    agent_id: String(raw.agent_id),
    name: raw.name,
    prompt: raw.prompt,
    schedule: raw.schedule,
    timezone: raw.timezone || 'UTC',
    is_active: Boolean(raw.is_active),
    last_run_at: raw.last_run_at ?? null,
    last_run_status: raw.last_run_status ?? null,
    created_at: raw.created_at,
    updated_at: raw.updated_at,
  };
}

function normalizeRoutineRun(raw: any): RoutineRun {
  return {
    id: String(raw.id),
    routine_id: String(raw.routine_id),
    agent_id: String(raw.agent_id),
    status: raw.status,
    trigger: raw.trigger || 'manual',
    output: raw.output,
    error: raw.error,
    duration: raw.duration || calculateDuration(raw.started_at, raw.finished_at),
    started_at: raw.started_at,
    finished_at: raw.finished_at,
    tools_executed: raw.tools_executed || inferToolsFromOutput(raw.output),
  };
}

function calculateDuration(startedAt?: string, finishedAt?: string | null): string | undefined {
  if (!startedAt || !finishedAt) return undefined;
  const ms = new Date(finishedAt).getTime() - new Date(startedAt).getTime();
  if (!Number.isFinite(ms) || ms < 0) return undefined;
  return `${Math.max(1, Math.round(ms / 1000))}s`;
}

function inferToolsFromOutput(output?: string | null): string[] {
  if (!output) return [];
  const tools = ['datetime', 'web_search', 'gmail_summary', 'draft_message'].filter((tool) =>
    output.toLowerCase().includes(tool)
  );
  return tools.length > 0 ? tools : ['agent_loop'];
}

function normalizeDashboardSummary(raw: any): DashboardSummary {
  const totalRuns = raw.total_routine_runs_count ?? 0;
  const failedRuns = raw.failed_routine_runs_count ?? 0;
  const succeededRuns = raw.succeeded_routine_runs_count ?? 0;
  const successRate = totalRuns > 0 ? Math.round((succeededRuns / totalRuns) * 1000) / 10 : 100;
  return {
    active_agents_count: raw.active_agents_count ?? raw.agents_count ?? 0,
    healthy_agents_count: raw.healthy_agents_count ?? raw.agents_count ?? 0,
    active_routines_count: raw.active_routines_count ?? 0,
    next_routine_in_minutes: raw.next_routine_in_minutes ?? 0,
    runs_this_week_count: raw.runs_this_week_count ?? totalRuns,
    success_rate_percentage: raw.success_rate_percentage ?? successRate,
    failed_runs_count: raw.failed_runs_count ?? failedRuns,
    runs_trend_data: raw.runs_trend_data || [],
  };
}

function normalizeActionItem(raw: any): ActionItem {
  const requiresConfirmation = Boolean(raw.requires_confirmation);
  return {
    id: String(raw.id),
    title: raw.title || `${raw.tool_name || 'Action'} needs attention`,
    description: raw.description || raw.title || 'Review this item before continuing.',
    level: requiresConfirmation ? 'warning' : raw.status === 'failed' ? 'error' : 'info',
    badge_text: raw.status || raw.tool_name,
    action_label: requiresConfirmation ? 'Review' : undefined,
    secondary_action_label: 'Dismiss',
    created_at: raw.created_at || new Date().toISOString(),
  };
}

function normalizeIntegration(raw: any): Integration {
  const connected = raw.connected || raw.status === 'connected';
  return {
    id: raw.id || raw.provider || 'gmail',
    name: raw.name || `${String(raw.provider || 'gmail').toUpperCase()} Integration`,
    provider: raw.provider || 'gmail',
    description: raw.description || raw.message || 'External integration status.',
    status: connected ? 'connected' : raw.status || 'disconnected',
    scopes: raw.scopes || [],
    icon: raw.icon || raw.provider || 'gmail',
    account_email: raw.account_email,
    last_synced_at: raw.last_synced_at,
    expires_at: raw.expires_at,
    configured: Boolean(raw.configured),
    connected,
    message: raw.message,
    connect_url: raw.connect_url,
  };
}

function normalizeToolDefinition(raw: any): ToolDefinition {
  return {
    id: raw.name || raw.id,
    name: normalizeToolNameForFrontend(raw.name || raw.id),
    displayName: raw.displayName || raw.display_name || raw.name || raw.id,
    description: raw.description || 'Tool available to agents.',
    category: raw.category || 'system',
    requiredPermissions: raw.requiredPermissions || raw.required_permissions || [],
    isBuiltIn: raw.isBuiltIn ?? raw.is_built_in ?? true,
    safety_level: raw.safety_level,
    requires_confirmation: Boolean(raw.requires_confirmation),
  };
}

// Mock Request Handler
function handleMockRequest<T>(endpoint: string, options: RequestInit): T {
  const method = (options.method || 'GET').toUpperCase();
  const body = options.body ? JSON.parse(options.body as string) : {};

  // Auth endpoints
  if (endpoint === '/auth/login' || endpoint === '/auth/register') {
    const authRes: AuthResponse = {
      access_token: 'mock_jwt_token_' + Date.now(),
      token_type: 'Bearer',
      expires_in: 3600,
      user: {
        ...mockDb.currentUser,
        email: body.email || mockDb.currentUser.email,
        name: body.name || mockDb.currentUser.name,
      },
    };
    tokenStorage.setAccessToken(authRes.access_token);
    tokenStorage.setRefreshToken('mock_refresh_token_' + Date.now());
    return authRes as unknown as T;
  }

  if (endpoint === '/auth/me') {
    return mockDb.currentUser as unknown as T;
  }

  if (endpoint === '/auth/logout') {
    tokenStorage.clear();
    return { success: true } as unknown as T;
  }

  if (endpoint === '/auth/refresh') {
    const authRes: AuthResponse = {
      access_token: 'mock_jwt_refreshed_' + Date.now(),
      token_type: 'Bearer',
      expires_in: 3600,
      user: mockDb.currentUser,
    };
    tokenStorage.setAccessToken(authRes.access_token);
    return authRes as unknown as T;
  }

  // Dashboard
  if (endpoint === '/dashboard/summary') {
    return {
      ...mockDb.summary,
      active_agents_count: mockDb.agents.filter((a) => a.status === 'active').length,
      active_routines_count: mockDb.routines.filter((r) => r.is_active).length,
    } as unknown as T;
  }

  if (endpoint === '/dashboard/recent-runs') {
    return mockDb.runs as unknown as T;
  }

  if (endpoint === '/dashboard/action-items') {
    return mockDb.actionItems as unknown as T;
  }

  // Agents
  if (endpoint === '/agents' && method === 'GET') {
    return mockDb.agents as unknown as T;
  }

  if (endpoint === '/agents' && method === 'POST') {
    const newAgent: Agent = {
      id: `agent_${Date.now()}`,
      name: body.name,
      objective: body.objective,
      instructions: body.instructions,
        model: body.model || 'google/gemini-2.5-flash',
      temperature: body.temperature ?? 0.7,
      tools: body.tools || [],
      version: 'v1.0',
      status: body.status || 'active',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    mockDb.agents.unshift(newAgent);
    mockDb.save();
    return newAgent as unknown as T;
  }

  const agentMatch = endpoint.match(/^\/agents\/([^/]+)$/);
  if (agentMatch) {
    const agentId = agentMatch[1];
    const index = mockDb.agents.findIndex((a) => a.id === agentId);
    if (index === -1) throw new ApiError('Agent not found', 'NOT_FOUND', 404);

    if (method === 'GET') {
      return mockDb.agents[index] as unknown as T;
    }
    if (method === 'PATCH') {
      mockDb.agents[index] = {
        ...mockDb.agents[index],
        ...body,
        updated_at: new Date().toISOString(),
      };
      mockDb.save();
      return mockDb.agents[index] as unknown as T;
    }
    if (method === 'DELETE') {
      mockDb.agents.splice(index, 1);
      mockDb.save();
      return { success: true } as unknown as T;
    }
  }

  // Conversations
  const agentConvMatch = endpoint.match(/^\/agents\/([^/]+)\/conversations$/);
  if (agentConvMatch) {
    const agentId = agentConvMatch[1];
    if (method === 'GET') {
      return mockDb.conversations.filter((c) => c.agent_id === agentId) as unknown as T;
    }
    if (method === 'POST') {
      const newConv: Conversation = {
        id: `conv_${Date.now()}`,
        agent_id: agentId,
        title: body.title || 'New Conversation',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      mockDb.conversations.unshift(newConv);
      mockDb.messages[newConv.id] = [];
      mockDb.save();
      return newConv as unknown as T;
    }
  }

  if (endpoint === '/conversations' && method === 'GET') {
    return mockDb.conversations as unknown as T;
  }

  const singleConvMatch = endpoint.match(/^\/conversations\/([^/]+)$/);
  if (singleConvMatch) {
    const convId = singleConvMatch[1];
    const conv = mockDb.conversations.find((c) => c.id === convId);
    if (!conv) throw new ApiError('Conversation not found', 'NOT_FOUND', 404);
    return {
      ...conv,
      messages: mockDb.messages[convId] || [],
    } as unknown as T;
  }

  const convMessagesMatch = endpoint.match(/^\/conversations\/([^/]+)\/messages$/);
  if (convMessagesMatch) {
    const convId = convMessagesMatch[1];
    const userMsg: Message = {
      id: `msg_user_${Date.now()}`,
      conversation_id: convId,
      role: 'user',
      content: body.content,
      created_at: new Date().toISOString(),
    };
    if (!mockDb.messages[convId]) mockDb.messages[convId] = [];
    mockDb.messages[convId].push(userMsg);

    // Mock assistant response with tool calls
    const assistantMsg: Message = {
      id: `msg_asst_${Date.now()}`,
      conversation_id: convId,
      role: 'assistant',
      content: `I've processed your request: "${body.content.slice(0, 40)}...". All parameters validated and executed cleanly.`,
      tool_calls: [
        {
          id: `tc_${Date.now()}`,
          tool_name: 'parse_job_requirements',
          input: { query: body.content },
          output: { status: '200 OK', verified: true },
          status: 'succeeded',
          duration_ms: 450,
        },
      ],
      created_at: new Date().toISOString(),
    };
    mockDb.messages[convId].push(assistantMsg);
    mockDb.save();
    return assistantMsg as unknown as T;
  }

  // Routines
  if (endpoint === '/routines' && method === 'GET') {
    return mockDb.routines as unknown as T;
  }

  if (endpoint === '/routines' && method === 'POST') {
    const newRoutine: Routine = {
      id: `rtn_${Date.now()}`,
      agent_id: body.agent_id,
      name: body.name,
      prompt: body.prompt,
      schedule: body.schedule,
      timezone: body.timezone || 'UTC',
      is_active: body.is_active ?? true,
      last_run_at: null,
      last_run_status: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    mockDb.routines.unshift(newRoutine);
    mockDb.save();
    return newRoutine as unknown as T;
  }

  const routineMatch = endpoint.match(/^\/routines\/([^/]+)$/);
  if (routineMatch) {
    const routineId = routineMatch[1];
    const index = mockDb.routines.findIndex((r) => r.id === routineId);
    if (index === -1) throw new ApiError('Routine not found', 'NOT_FOUND', 404);

    if (method === 'GET') {
      return mockDb.routines[index] as unknown as T;
    }
    if (method === 'PATCH') {
      mockDb.routines[index] = {
        ...mockDb.routines[index],
        ...body,
        updated_at: new Date().toISOString(),
      };
      mockDb.save();
      return mockDb.routines[index] as unknown as T;
    }
    if (method === 'DELETE') {
      mockDb.routines.splice(index, 1);
      mockDb.save();
      return { success: true } as unknown as T;
    }
  }

  // Trigger Routine Run
  const routineRunTriggerMatch = endpoint.match(/^\/routines\/([^/]+)\/run$/);
  if (routineRunTriggerMatch) {
    const routineId = routineRunTriggerMatch[1];
    const routine = mockDb.routines.find((r) => r.id === routineId);
    if (!routine) throw new ApiError('Routine not found', 'NOT_FOUND', 404);

    const newRun: RoutineRun = {
      id: `run_${Date.now()}`,
      routine_id: routineId,
      agent_id: routine.agent_id,
      status: 'running',
      trigger: 'manual',
      duration: 'In progress...',
      started_at: new Date().toISOString(),
      tools_executed: ['internship_research', 'save_report'],
      output: `Manual run dispatched for routine "${routine.name}". Running execution graph across workers.`,
    };
    mockDb.runs.unshift(newRun);
    routine.last_run_at = newRun.started_at;
    routine.last_run_status = 'running';
    mockDb.save();

    // Simulate completion after 3s
    setTimeout(() => {
      newRun.status = 'succeeded';
      newRun.duration = '1m 12s';
      newRun.finished_at = new Date().toISOString();
      routine.last_run_status = 'succeeded';
      mockDb.save();
    }, 3000);

    return newRun as unknown as T;
  }

  // Routine Runs list
  const routineRunsMatch = endpoint.match(/^\/routines\/([^/]+)\/runs$/);
  if (routineRunsMatch) {
    const routineId = routineRunsMatch[1];
    return mockDb.runs.filter((r) => r.routine_id === routineId) as unknown as T;
  }

  // Integrations
  if (endpoint === '/integrations') {
    return mockDb.integrations as unknown as T;
  }

  const integrationActionMatch = endpoint.match(/^\/integrations\/([^/]+)\/(connect|disconnect)$/);
  if (integrationActionMatch) {
    const provider = integrationActionMatch[1];
    const action = integrationActionMatch[2];
    const intItem = mockDb.integrations.find((i) => i.provider === provider || i.id === provider);
    if (!intItem) throw new ApiError('Integration not found', 'NOT_FOUND', 404);
    intItem.status = action === 'connect' ? 'pending' : 'disconnected';
    intItem.connected = false;
    intItem.message =
      action === 'connect'
        ? 'Mock connection requested. Complete OAuth before agents can use this provider.'
        : 'Mock integration disconnected.';
    mockDb.save();
    return intItem as unknown as T;
  }

  const integrationMatch = endpoint.match(/^\/integrations\/([^/]+)$/);
  if (integrationMatch) {
    const intId = integrationMatch[1];
    const intItem = mockDb.integrations.find((i) => i.id === intId);
    if (!intItem) throw new ApiError('Integration not found', 'NOT_FOUND', 404);
    if (method === 'PATCH') {
      Object.assign(intItem, body);
      mockDb.save();
      return intItem as unknown as T;
    }
    return intItem as unknown as T;
  }

  // Default fallback
  return {} as unknown as T;
}

export const api = {
  // Auth
  login: (credentials: { email: string; password?: string }) =>
    request<unknown>('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }).then(normalizeAuthResponse),
  register: (data: { name: string; email: string; password?: string }) =>
    request<unknown>('/auth/register', { method: 'POST', body: JSON.stringify(data) }).then(normalizeAuthResponse),
  refreshSession: (refreshToken: string) =>
    request<unknown>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }).then(normalizeAuthResponse),
  getMe: () => request<unknown>('/auth/me').then(normalizeUser),
  logout: () => request<{ success: boolean }>('/auth/logout', { method: 'POST' }),

  // Dashboard
  getDashboardSummary: (): Promise<DashboardSummary> => request<unknown>('/dashboard/summary').then(normalizeDashboardSummary),
  getRecentRuns: (): Promise<RoutineRun[]> =>
    request<any>('/dashboard/recent-runs').then((raw) => {
      const runs = (Array.isArray(raw) ? raw : raw.runs || []).map(normalizeRoutineRun);
      mockDb.runs = runs;
      return runs;
    }),
  getActionItems: (): Promise<ActionItem[]> =>
    request<any>('/dashboard/action-items').then((raw) =>
      (Array.isArray(raw) ? raw : raw.action_items || []).map(normalizeActionItem)
    ),
  dismissActionItem: (id: string) => {
    mockDb.actionItems = mockDb.actionItems.filter((item) => item.id !== id);
    mockDb.save();
    return Promise.resolve({ success: true });
  },

  // Agents
  getAgents: (): Promise<Agent[]> =>
    request<any>('/agents').then((raw) => {
      const agents = (Array.isArray(raw) ? raw : raw.agents || []).map(normalizeAgent);
      mockDb.agents = agents;
      return agents;
    }),
  getAgent: (id: string): Promise<Agent> => request<unknown>(`/agents/${id}`).then(normalizeAgent),
  createAgent: (input: AgentCreateInput) =>
    request<unknown>('/agents', { method: 'POST', body: JSON.stringify(toBackendAgentPayload(input)) }).then(normalizeAgent),
  updateAgent: (id: string, input: AgentUpdateInput) =>
    request<unknown>(`/agents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(toBackendAgentPayload(input)),
    }).then(normalizeAgent),
  deleteAgent: (id: string) =>
    request<{ success: boolean }>(`/agents/${id}`, { method: 'DELETE' }),

  // Conversations & Chat
  getConversations: (agentId?: string): Promise<Conversation[]> =>
    agentId
      ? request<any>(`/agents/${agentId}/conversations`).then((raw) =>
          (Array.isArray(raw) ? raw : raw.conversations || []).map(normalizeConversation)
        )
      : request<Conversation[]>('/conversations'),
  createConversation: (agentId: string, title?: string) =>
    request<unknown>(`/agents/${agentId}/conversations`, {
      method: 'POST',
      body: JSON.stringify({ title }),
    }).then(normalizeConversation),
  getConversation: (conversationId: string): Promise<Conversation & { messages: Message[] }> =>
    request<unknown>(`/conversations/${conversationId}`).then(normalizeConversationDetail),
  deleteConversation: (conversationId: string) =>
    request<void>(`/conversations/${conversationId}`, { method: 'DELETE' }),
  sendMessage: (conversationId: string, content: string) =>
    request<any>(`/conversations/${conversationId}/runs`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }).then((raw) => normalizeMessage(raw.assistant_message || raw)),

  // Routines
  getRoutines: (): Promise<Routine[]> =>
    request<any>('/routines').then((raw) => {
      const routines = (Array.isArray(raw) ? raw : raw.routines || []).map(normalizeRoutine);
      mockDb.routines = routines;
      return routines;
    }),
  getRoutine: (id: string): Promise<Routine> => request<unknown>(`/routines/${id}`).then(normalizeRoutine),
  createRoutine: (input: RoutineCreateInput) =>
    request<unknown>('/routines', { method: 'POST', body: JSON.stringify(input) }).then(normalizeRoutine),
  updateRoutine: (id: string, input: RoutineUpdateInput) =>
    request<unknown>(`/routines/${id}`, { method: 'PATCH', body: JSON.stringify(input) }).then(normalizeRoutine),
  deleteRoutine: (id: string) =>
    request<{ success: boolean }>(`/routines/${id}`, { method: 'DELETE' }),
  triggerRoutineRun: (id: string) =>
    request<unknown>(`/routines/${id}/run`, { method: 'POST' }).then(normalizeRoutineRun),
  getRoutineRuns: (routineId: string) =>
    request<any>(`/routines/${routineId}/runs`).then((raw) =>
      (Array.isArray(raw) ? raw : raw.runs || []).map(normalizeRoutineRun)
    ),
  getRoutineRun: (routineId: string, runId: string) =>
    request<unknown>(`/routines/${routineId}/runs/${runId}`).then(normalizeRoutineRun),

  // Tool Logs & Run Details
  getToolLogsForRun: (routineId: string, runId: string): Promise<ToolActionLog[]> =>
    request<any>(`/routines/${routineId}/runs/${runId}/tool-logs`).then((raw) =>
      (Array.isArray(raw) ? raw : raw.tool_logs || []).map((log: any) => ({
        ...log,
        id: String(log.id),
        agent_id: String(log.agent_id),
        routine_run_id: log.routine_run_id ? String(log.routine_run_id) : null,
      }))
    ),
  getTools: (): Promise<ToolDefinition[]> =>
    request<any>('/tools').then((raw) => (Array.isArray(raw) ? raw : raw.tools || []).map(normalizeToolDefinition)),

  // Integrations
  getIntegrations: () =>
    request<any>('/integrations').then((raw) =>
      (Array.isArray(raw) ? raw : raw.integrations || []).map(normalizeIntegration)
    ),
  connectIntegration: (provider: string) =>
    request<unknown>(`/integrations/${provider}/connect`, { method: 'POST' }).then(normalizeIntegration),
  disconnectIntegration: (provider: string) =>
    request<unknown>(`/integrations/${provider}/disconnect`, { method: 'POST' }).then(normalizeIntegration),
  updateIntegration: (id: string, patch: Partial<Integration>) =>
    request<Integration>(`/integrations/${id}`, { method: 'PATCH', body: JSON.stringify(patch) }),
};

/**
 * Stream message helper using fetch + ReadableStream for tokens and tool execution events
 */
export async function streamMessageHelper({
  conversationId,
  content,
  onToken,
  onToolCall,
  onComplete,
  onError,
  signal,
}: {
  conversationId: string;
  content: string;
  onToken: (text: string) => void;
  onToolCall?: (toolCall: ToolCallPayload) => void;
  onComplete: (fullMessage: Message) => void;
  onError: (err: Error) => void;
  signal?: AbortSignal;
}) {
  const url = `${API_PREFIX}/conversations/${conversationId}/runs`;
  const token = tokenStorage.getAccessToken();

  try {
    if (USE_MOCKS) {
      // Simulate realistic streaming chunks and tool calls
      const userMsg: Message = {
        id: `msg_user_${Date.now()}`,
        conversation_id: conversationId,
        role: 'user',
        content,
        created_at: new Date().toISOString(),
      };
      if (!mockDb.messages[conversationId]) mockDb.messages[conversationId] = [];
      mockDb.messages[conversationId].push(userMsg);

      // Tool call 1
      if (onToolCall) {
        onToolCall({
          id: `tc_stream_${Date.now()}_1`,
          tool_name: 'internship_research',
          input: { query: content },
          status: 'running',
        });
        await new Promise((r) => setTimeout(r, 600));
        onToolCall({
          id: `tc_stream_${Date.now()}_1`,
          tool_name: 'internship_research',
          input: { query: content },
          output: { status: '200 OK (8 matches found)' },
          status: 'succeeded',
          duration_ms: 600,
        });
      }

      // Stream text chunks
      const responseStreamText = `I analyzed your request for "${content}". 

Here are the key findings compiled from live search nodes:
- **Verified Sources**: All listings checked against Greenhouse and Lever ATS endpoints.
- **Compensation Bracket**: Average $55–$70/hr for engineering internships.
- **Action Required**: 2 roles have application deadlines closing in 48 hours.

The full synthesis report has been formatted and stored in the workspace registry.`;

      const words = responseStreamText.split(' ');
      let accumulated = '';
      for (let i = 0; i < words.length; i++) {
        if (signal?.aborted) return;
        await new Promise((r) => setTimeout(r, 45));
        const chunk = words[i] + ' ';
        accumulated += chunk;
        onToken(chunk);
      }

      const finalAssistantMsg: Message = {
        id: `msg_asst_${Date.now()}`,
        conversation_id: conversationId,
        role: 'assistant',
        content: responseStreamText,
        tool_calls: [
          {
            id: `tc_stream_${Date.now()}_1`,
            tool_name: 'internship_research',
            input: { query: content },
            output: { status: '200 OK (8 matches found)' },
            status: 'succeeded',
            duration_ms: 600,
          },
        ],
        created_at: new Date().toISOString(),
      };
      mockDb.messages[conversationId].push(finalAssistantMsg);
      mockDb.save();
      onComplete(finalAssistantMsg);
      return;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ content }),
      signal,
    });

    if (!response.ok) {
      const errorJson = await response.json().catch(() => ({}));
      throw new ApiError(errorJson.error?.message || 'Streaming failed', errorJson.error?.code, response.status);
    }

    // If server returned plain JSON
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      const toolMessages = (data.tool_messages || []).map(normalizeMessage);
      toolMessages.forEach((toolMessage: Message) => {
        const toolCall = normalizeToolCalls(toolMessage.tool_calls)?.[0];
        if (toolCall && onToolCall) {
          onToolCall({
            ...toolCall,
            output: toolMessage.content,
            status: 'succeeded',
          });
        }
      });
      const assistantMessage = normalizeMessage(data.assistant_message || data);
      const chunks = assistantMessage.content.match(/.{1,140}(?:\s|$)/g) || [assistantMessage.content];
      for (const chunk of chunks) {
        if (signal?.aborted) return;
        await new Promise((resolve) => setTimeout(resolve, 35));
        onToken(chunk);
      }
      onComplete(assistantMessage);
      return;
    }

    // Read stream
    if (!response.body) throw new Error('Response body is null');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const textChunk = decoder.decode(value, { stream: true });
      accumulatedText += textChunk;
      onToken(textChunk);
    }

    const finalMsg: Message = {
      id: `msg_${Date.now()}`,
      conversation_id: conversationId,
      role: 'assistant',
      content: accumulatedText,
      created_at: new Date().toISOString(),
    };
    onComplete(finalMsg);
  } catch (err: unknown) {
    if (signal?.aborted) return;
    onError(err instanceof Error ? err : new Error(String(err)));
  }
}
