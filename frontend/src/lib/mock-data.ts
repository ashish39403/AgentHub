import {
  Agent,
  Conversation,
  Message,
  Routine,
  RoutineRun,
  ToolActionLog,
  ActionItem,
  DashboardSummary,
  ToolDefinition,
  User,
} from '../types';

export const mockUser: User = {
  id: 'usr_elena_vance',
  name: 'Elena Vance',
  email: 'elena@agenthub.dev',
  avatar_url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
  role: 'Admin',
  workspace_id: 'prod_us_east',
  created_at: '2026-01-15T08:00:00Z',
};

export const availableTools: ToolDefinition[] = [
  {
    id: 'web_search',
    name: 'web_search',
    displayName: 'Web Search',
    description: 'Searches the web through Serper with optional fallback handling',
    category: 'search',
    isBuiltIn: true,
  },
  {
    id: 'summarize_text',
    name: 'summarize_text',
    displayName: 'Text Summarizer',
    description: 'Summarizes text and extracts important points',
    category: 'internal',
    isBuiltIn: true,
  },
  {
    id: 'save_memory',
    name: 'save_memory',
    displayName: 'Save Memory',
    description: 'Persists useful agent memory in the database',
    category: 'memory',
    isBuiltIn: true,
  },
  {
    id: 'gmail_summary',
    name: 'gmail_summary',
    displayName: 'Gmail Summary',
    description: 'Fetches unread message threads, extracts metadata, and categorizes priority',
    category: 'communication',
    requiredPermissions: ['gmail.readonly'],
  },
  {
    id: 'draft_message',
    name: 'draft_message',
    displayName: 'Message Draft Generator',
    description: 'Generates concise synthesis email or Slack drafts with action items',
    category: 'communication',
    isBuiltIn: true,
  },
  {
    id: 'github_issue_search',
    name: 'github_issue_search',
    displayName: 'GitHub Issue Search',
    description: 'Monitors pull requests, release tags, and trending repo activity',
    category: 'code',
    requiredPermissions: ['repo.read'],
  },
  {
    id: 'send_slack_message',
    name: 'send_slack_message',
    displayName: 'Slack Message Preparation',
    description: 'Dispatches real-time structured blocks and alert cards into Slack channels',
    category: 'communication',
    requiredPermissions: ['chat:write'],
  },
  {
    id: 'datetime',
    name: 'datetime',
    displayName: 'Temporal Utilities',
    description: 'Calculates relative date deltas, timezone shifts, and schedule validation',
    category: 'system',
    isBuiltIn: true,
  },
  {
    id: 'web_search',
    name: 'web_search',
    displayName: 'Live Web Indexer',
    description: 'Performs low-latency search across documentation and tech publications',
    category: 'search',
    isBuiltIn: true,
  },
];

export const initialAgents: Agent[] = [
  {
    id: 'agent_scout_01',
    name: 'Internship Scout',
    objective: 'Find remote Summer 2025 AI/ML engineering internships at top labs or Series A/B startups and draft weekly synthesis reports.',
    instructions: 'You are an autonomous talent research assistant. Use web_search to find verified opportunities. Filter for recent roles and structure findings by company, role title, compensation, and key tech stack before drafting reports.',
    model: 'gemini-2.5-flash',
    temperature: 0.2,
    tools: ['web_search', 'summarize_text', 'save_memory', 'draft_message'],
    version: 'v2.1',
    status: 'active',
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-03-28T09:14:00Z',
  },
  {
    id: 'agent_inbox_02',
    name: 'Inbox Summarizer',
    objective: 'Scans unread Gmail inbox every morning, categorizes priority threads, and drafts action digests.',
    instructions: 'Summarize unread emails using gmail_summary. Categorize messages into Urgent, Action Required, Newsletters, and Low Priority. Draft a summary highlighting time-sensitive deliverables.',
    model: 'gemini-2.5-flash',
    temperature: 0.3,
    tools: ['gmail_summary', 'draft_message', 'datetime'],
    version: 'v1.4',
    status: 'active',
    created_at: '2026-02-10T14:30:00Z',
    updated_at: '2026-03-29T08:00:00Z',
  },
  {
    id: 'agent_github_03',
    name: 'GitHub Release Tracker',
    objective: 'Monitors upstream repository releases and commits, summarizing breaking changes and security notices.',
    instructions: 'Poll tracked GitHub repositories for new tagged releases. Parse changelog markdown for breaking changes and deprecations. Send a summary to the engineering Slack channel.',
    model: 'gemini-2.5-flash',
    temperature: 0.1,
    tools: ['github_issue_search', 'send_slack_message'],
    version: 'v0.9 (Draft)',
    status: 'draft',
    created_at: '2026-03-20T11:20:00Z',
    updated_at: '2026-03-25T16:45:00Z',
  },
];

export const initialRoutines: Routine[] = [
  {
    id: 'rtn_inbox_digest',
    agent_id: 'agent_inbox_02',
    name: 'Morning inbox digest',
    prompt: 'Read all unread threads from the last 24 hours, identify blockers, and draft a morning priorities digest.',
    schedule: '0 8 * * *',
    timezone: 'UTC',
    is_active: true,
    last_run_at: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
    last_run_status: 'succeeded',
    created_at: '2026-02-10T15:00:00Z',
    updated_at: '2026-03-29T08:01:24Z',
  },
  {
    id: 'rtn_live_run',
    agent_id: 'agent_scout_01',
    name: 'Internship Scout Live Run',
    prompt: 'Query ATS boards for open Summer 2025 AI/ML internship roles posted in the last 7 days.',
    schedule: 'Manual',
    timezone: 'UTC',
    is_active: true,
    last_run_at: new Date(Date.now() - 45 * 1000).toISOString(),
    last_run_status: 'running',
    created_at: '2026-03-29T09:00:00Z',
    updated_at: '2026-03-29T09:14:00Z',
  },
  {
    id: 'rtn_weekly_scout',
    agent_id: 'agent_scout_01',
    name: 'Weekly internship report',
    prompt: 'Compile full weekly ATS listings, compute salary/stipend percentiles, and generate markdown digest report.',
    schedule: '0 9 * * 1',
    timezone: 'UTC',
    is_active: true,
    last_run_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    last_run_status: 'failed',
    created_at: '2026-02-01T11:00:00Z',
    updated_at: '2026-03-28T09:00:32Z',
  },
  {
    id: 'rtn_github_stars',
    agent_id: 'agent_github_03',
    name: 'GitHub Star Monitor',
    prompt: 'Check repository metrics and notify team on Slack of milestone changes.',
    schedule: '0 * * * *',
    timezone: 'UTC',
    is_active: true,
    last_run_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    last_run_status: 'succeeded',
    created_at: '2026-03-01T12:00:00Z',
    updated_at: '2026-03-29T07:00:18Z',
  },
];

export const initialRecentRuns: RoutineRun[] = [
  {
    id: 'run_1044',
    routine_id: 'rtn_inbox_digest',
    agent_id: 'agent_inbox_02',
    status: 'succeeded',
    trigger: 'scheduled',
    duration: '1m 24s',
    started_at: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
    finished_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
    tools_executed: ['gmail_summary', 'summarize_text', 'draft_message'],
    output: 'Analyzed 18 unread emails. 3 high-priority threads identified: Cloud provider invoice renewal, Product review agenda, and Customer security question. Draft created in inbox.',
  },
  {
    id: 'run_1043',
    routine_id: 'rtn_live_run',
    agent_id: 'agent_scout_01',
    status: 'running',
    trigger: 'manual',
    duration: '45s...',
    started_at: new Date(Date.now() - 45 * 1000).toISOString(),
    tools_executed: ['web_search', 'summarize_text'],
    output: 'Querying Lever and Greenhouse career pages for 14 companies. Filtered 6 matching criteria.',
  },
  {
    id: 'run_1042',
    routine_id: 'rtn_weekly_scout',
    agent_id: 'agent_scout_01',
    status: 'failed',
    trigger: 'scheduled',
    duration: '32s',
    started_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    finished_at: new Date(Date.now() - 24 * 60 * 60 * 1000 + 32000).toISOString(),
    tools_executed: ['web_search'],
    error: 'Failed at tool web_search: HTTP 429 rate limit exceeded from search provider.',
  },
  {
    id: 'run_1041',
    routine_id: 'rtn_github_stars',
    agent_id: 'agent_github_03',
    status: 'succeeded',
    trigger: 'scheduled',
    duration: '18s',
    started_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    finished_at: new Date(Date.now() - 2 * 60 * 60 * 1000 + 18000).toISOString(),
    tools_executed: ['github_issue_search', 'send_slack_message'],
    output: 'Verified 6 tracked repositories. Dispatched update to #engineering-feed.',
  },
];

export const initialToolLogs: ToolActionLog[] = [
  {
    id: 'tlog_01',
    agent_id: 'agent_scout_01',
    routine_run_id: 'run_1043',
    tool_name: 'web_search',
    input: { query: 'site:lever.co OR site:greenhouse.io AI intern 2025', filter_days: 7 },
    output: { status: '200 OK', matches_parsed: 14, sources: ['Anthropic', 'Perplexity AI', 'Adept', 'Cohere'] },
    status: 'succeeded',
    duration_ms: 1800,
    created_at: new Date(Date.now() - 40 * 1000).toISOString(),
  },
  {
    id: 'tlog_02',
    agent_id: 'agent_scout_01',
    routine_run_id: 'run_1043',
    tool_name: 'summarize_text',
    input: { candidate_roles: 14, min_stipend: 45, allow_remote: true },
    output: { evaluated: 14, passed_criteria: 6, top_roles: ['Anthropic Research Engineer Intern', 'Perplexity ML Systems Intern'] },
    status: 'succeeded',
    duration_ms: 850,
    created_at: new Date(Date.now() - 25 * 1000).toISOString(),
  },
  {
    id: 'tlog_03',
    agent_id: 'agent_scout_01',
    routine_run_id: 'run_1043',
    tool_name: 'draft_message',
    input: { format: 'markdown', include_stipends: true },
    output: null,
    status: 'succeeded',
    duration_ms: 320,
    created_at: new Date(Date.now() - 10 * 1000).toISOString(),
  },
];

export const initialActionItems: ActionItem[] = [
  {
    id: 'act_01',
    title: 'Review morning inbox routine',
    description: 'The morning digest routine needs a quick manual check before the next scheduled run.',
    level: 'warning',
    badge_text: 'Routine check',
    target_url: '/routines',
    action_label: 'Open routines',
    secondary_action_label: 'Dismiss',
    time_remaining: '3h remaining',
    acknowledged: false,
    created_at: '2026-03-29T06:00:00Z',
  },
  {
    id: 'act_02',
    title: 'Routine failed: Weekly internship report',
    description: 'Failed at tool web_search: HTTP 429 rate limit exceeded from search provider.',
    level: 'error',
    badge_text: 'Run #1042',
    target_url: '/routines/rtn_weekly_scout/runs/run_1042',
    action_label: 'Retry',
    secondary_action_label: 'View run details',
    acknowledged: false,
    created_at: '2026-03-28T09:01:00Z',
  },
];

export const initialSummary: DashboardSummary = {
  active_agents_count: 2,
  healthy_agents_count: 2,
  active_routines_count: 4,
  next_routine_in_minutes: 42,
  runs_this_week_count: 148,
  success_rate_percentage: 98.6,
  failed_runs_count: 2,
  runs_trend_data: [18, 16, 20, 10, 12, 24, 28, 22],
};

export const initialConversations: Conversation[] = [
  {
    id: 'conv_scout_01',
    agent_id: 'agent_scout_01',
    title: 'Research AI internships Q2',
    created_at: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 60 * 1000).toISOString(),
  },
  {
    id: 'conv_inbox_01',
    agent_id: 'agent_inbox_02',
    title: 'Inbox triage & priority',
    created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'conv_scout_02',
    agent_id: 'agent_scout_01',
    title: 'Weekly report dry run',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
  },
];

export const initialMessages: Record<string, Message[]> = {
  conv_scout_01: [
    {
      id: 'msg_01',
      conversation_id: 'conv_scout_01',
      role: 'user',
      content: 'Find me remote Summer 2025 AI/ML engineering internships at top labs or Series-A/B startups, filter for listings posted in the last 7 days, and draft a markdown report with stipend notes.',
      created_at: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
    },
    {
      id: 'msg_02',
      conversation_id: 'conv_scout_01',
      role: 'assistant',
      content: `I've identified 3 top-tier machine learning roles that meet all parameters: strictly posted within the last 7 days, open to remote, and featuring competitive stipends.

### Verified Positions:
1. **Anthropic** — *Research Engineer Intern* ($68/hr • Remote-friendly)  
   Focus: Interpretability, scalable alignment algorithms, PyTorch.
2. **Perplexity AI** — *Machine Learning Systems Intern* ($9,500/mo • US Remote)  
   Focus: Real-time RAG latency reduction, vLLM/TensorRT-LLM optimizations.
3. **Adept** — *Foundation Model Intern* ($60/hr • SF / Hybrid)  
   Focus: Multimodal action transformers, browser-environment agent trajectories.

All roles have verified active application links saved in your workspace vault.`,
      tool_calls: [
        {
          id: 'tc_01',
          tool_name: 'web_search',
          input: { query: 'site:lever.co OR site:greenhouse.io AI intern 2025' },
          output: { status: '200 OK (14 matches parsed)' },
          status: 'succeeded',
          duration_ms: 1800,
        },
        {
          id: 'tc_02',
          tool_name: 'summarize_text',
          input: { evaluated: 14 },
          output: { passed_criteria: 6 },
          status: 'succeeded',
          duration_ms: 850,
        },
        {
          id: 'tc_03',
          tool_name: 'draft_message',
          input: { format: 'markdown', count: 3 },
          output: 'Report draft formatted successfully.',
          status: 'succeeded',
          duration_ms: 320,
        },
      ],
      created_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    },
  ],
  conv_inbox_01: [
    {
      id: 'msg_inbox_01',
      conversation_id: 'conv_inbox_01',
      role: 'user',
      content: 'Run a quick scan on my priority inbox and list anything needing action before 11:00 AM.',
      created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: 'msg_inbox_02',
      conversation_id: 'conv_inbox_01',
      role: 'assistant',
      content: `Here is your morning inbox summary:

- **Cloud Platform Renewal**: Contract approval required by 12:00 PM UTC.
- **Sprint Retrospective**: Slides draft shared by Marcus for review.
- **Security Audit Questionnaire**: Vendor review request from Enterprise client.

Would you like me to draft affirmative responses for any of these?`,
      tool_calls: [
        {
          id: 'tc_inbox_01',
          tool_name: 'gmail_summary',
          input: { label: 'UNREAD', max_results: 20 },
          output: { unread_found: 18, high_priority: 3 },
          status: 'succeeded',
          duration_ms: 640,
        },
      ],
      created_at: new Date(Date.now() - 4 * 60 * 60 * 1000 + 4000).toISOString(),
    },
  ],
};
