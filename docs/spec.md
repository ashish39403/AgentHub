# AgentHub MVP Spec

## Product Summary

AgentHub is a personal AI automation backend where users create specialized agents that can chat, call tools, run scheduled routines, and save results for a dashboard.

The MVP is built around an engineering student use case: daily internship research, Gmail summarization, important email ranking, and scheduled task automation.

## Target User

An engineering student who is actively looking for internships and wants to reduce repetitive daily work:

- searching internship opportunities
- checking important emails
- summarizing updates
- tracking follow-ups
- scheduling simple automated tasks

## Must Have

### Authentication

- User registration with email and password
- User login
- JWT access token
- JWT refresh token
- Authenticated API routes

### Agents

- Create, read, update, and delete user-scoped agents
- Agent fields:
  - name
  - instructions
  - objective
  - created_at
- Users can only access their own agents

### Conversations

- Create conversations with agents
- Save user, assistant, and tool messages
- Return chat history
- Support agent responses through the backend API

### Agent Loop

- Custom loop without LangChain
- LLM call with system instructions, user message, history, and available tools
- Tool call detection
- Tool execution
- Tool result passed back to the LLM
- Max iteration limit
- Final answer saved to conversation history

### AI Engine V2 Planning

- Keep the MVP agent behavior stable while designing the next engine version.
- Define the engine as a backend orchestrator around LLM calls, tools, memory, safety policy, and logs.
- Prepare the architecture so LangGraph can be added later without changing frontend-facing API contracts.
- Keep the backend responsible for user ownership, tool permissions, confirmation gates, and persistence.
- Use [AI Engine V2 Design](./ai-engine-v2.md) as the source of truth before installing new AI orchestration dependencies.

### Internship Research Agent

- Run a prompt such as: "Find relevant internships for a software engineering student."
- Search or collect internship-like opportunities through safe tools.
- Summarize opportunities.
- Rank top opportunities by relevance.
- Save the result as a routine run output.

### Gmail Summary Agent

- Connect Gmail later through Composio or an equivalent integration.
- Read recent/unread email metadata and content only after user authorization.
- Summarize important emails.
- Rank emails by urgency and relevance.
- Extract action items.
- Do not send or delete emails by default.

### Routines

- Create, read, update, and delete routines
- Attach routines to agents
- Store prompt and schedule
- Enable or disable routines
- Scheduler triggers routine runs
- Routine results are saved

### Routine Logs

- Save each routine run with:
  - routine_id
  - status
  - output
  - error message if failed
  - started_at
  - finished_at
- Provide APIs for dashboard consumption

### Scheduled Task Automation

- Allow users to schedule an agent prompt at a specific time.
- MVP should support safe actions such as generating a message draft or saving a reminder.
- Sending messages automatically should require explicit confirmation or a safe allowlist configuration.

## Later

- Full Gmail send/delete support with confirmation flow
- More Composio integrations such as Slack, Notion, GitHub, and Google Calendar
- OAuth login with Google or GitHub
- E2B browser VM per agent
- Optional LangGraph-based orchestration for AI Engine V2
- Streaming responses through SSE
- Advanced notification system
- Better search provider integrations
- User preferences and agent templates
- Deployment observability

## Non-Goals

- Frontend implementation in this repository
- Mobile app
- Billing or subscriptions
- Team accounts, roles, or organization workspaces
- Public agent marketplace
- Fine-tuning
- RAG system
- Complex admin dashboard
- Fully autonomous destructive actions
- Heavy agent frameworks

## Success Criteria

- Backend runs locally with Docker Compose.
- Core APIs are documented and testable.
- User can register, log in, create an agent, chat with it, create a routine, run it, and inspect logs.
- Internship research routine produces a saved ranked summary.
- Gmail summary flow is designed safely and integrated when credentials are available.
- Tests cover auth, agent CRUD, routine creation, and core agent loop behavior.
