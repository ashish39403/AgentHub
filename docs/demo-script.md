# Demo Script

Use this flow to present AgentHub clearly.

## 1. Start Services

```bash
docker compose up -d postgres
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## 2. Register And Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Ashish\",\"email\":\"ashish@example.com\",\"password\":\"secure-password-123\"}"
```

Copy the `access_token` from the response.

## 3. Create An Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer <ACCESS_TOKEN>" ^
  -d "{\"name\":\"Internship Research Agent\",\"instructions\":\"Find useful internships and summarize clearly.\",\"objective\":\"Help an engineering student find internships daily.\",\"enabled_tools\":[\"datetime\",\"web_search\",\"gmail_summary\"]}"
```

## 4. Create And Run A Routine

```bash
curl -X POST http://localhost:8000/api/v1/routines ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer <ACCESS_TOKEN>" ^
  -d "{\"agent_id\":\"<AGENT_ID>\",\"name\":\"Morning Internship Brief\",\"prompt\":\"Find relevant software engineering internships for me.\",\"schedule\":\"daily@09:00\",\"timezone\":\"Asia/Kolkata\",\"is_active\":true}"
```

```bash
curl -X POST http://localhost:8000/api/v1/routines/<ROUTINE_ID>/run ^
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## 5. Show Dashboard APIs

```bash
curl http://localhost:8000/api/v1/dashboard/summary ^
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

```bash
curl http://localhost:8000/api/v1/dashboard/recent-runs ^
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

```bash
curl http://localhost:8000/api/v1/dashboard/action-items ^
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
