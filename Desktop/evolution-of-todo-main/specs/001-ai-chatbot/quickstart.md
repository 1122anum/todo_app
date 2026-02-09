# Quickstart Guide: AI-Powered Todo Chatbot

**Feature**: 001-ai-chatbot
**Date**: 2026-02-05
**Audience**: Developers

## Overview

This guide helps you set up and run the AI-powered Todo Chatbot locally for development and testing. The chatbot extends the existing Phase II Todo application with conversational task management using OpenAI Agents SDK and MCP tools.

## Prerequisites

### Required Software

- **Python 3.11+**: Backend runtime
- **Node.js 18+**: Frontend runtime
- **PostgreSQL**: Database (Neon Serverless PostgreSQL for production, local PostgreSQL for development)
- **Git**: Version control

### Required Accounts

- **OpenAI API Account**: For AI agent functionality
  - Sign up at https://platform.openai.com/
  - Create API key at https://platform.openai.com/api-keys
  - Ensure billing is set up (GPT-4 usage incurs costs)

### Existing Phase II Setup

This feature builds on Phase II. Ensure you have:
- Phase II backend running (FastAPI with task management)
- Phase II frontend running (Next.js with task UI)
- Database with User and Task tables
- Better Auth configured and working

---

## Setup Instructions

### 1. Environment Configuration

Create or update `.env` file in the backend directory:

```bash
# Backend: backend/.env

# Existing Phase II variables
DATABASE_URL=postgresql://user:password@localhost:5432/todo_db
SECRET_KEY=your-secret-key-here
BETTER_AUTH_SECRET=your-better-auth-secret

# New Phase III variables
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo for cost savings
MCP_SERVER_PORT=8001
CHAT_RATE_LIMIT=60  # requests per minute per user
```

Create or update `.env.local` file in the frontend directory:

```bash
# Frontend: frontend/.env.local

# Existing Phase II variables
NEXT_PUBLIC_API_URL=http://localhost:8000

# New Phase III variables (if needed)
NEXT_PUBLIC_CHAT_ENABLED=true
```

### 2. Install Dependencies

**Backend**:
```bash
cd backend
pip install -r requirements.txt

# New Phase III dependencies:
# - openai>=1.0.0 (OpenAI Agents SDK)
# - mcp>=0.1.0 (Official MCP SDK)
```

**Frontend**:
```bash
cd frontend
npm install

# New Phase III dependencies:
# - @openai/chatkit (OpenAI ChatKit UI components)
```

### 3. Database Migration

Run the Phase III migration to add Conversation and Message tables:

```bash
cd backend

# Apply migration
python -m alembic upgrade head

# Or run SQL directly
psql -U user -d todo_db -f migrations/003_add_conversations.sql
```

Verify tables were created:
```sql
-- Connect to database
psql -U user -d todo_db

-- Check tables
\dt

-- Should see:
-- users (Phase II)
-- tasks (Phase II)
-- conversations (Phase III - new)
-- messages (Phase III - new)
```

### 4. Start Backend Server

```bash
cd backend

# Development mode with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m src.main
```

Backend should start on http://localhost:8000

Verify backend is running:
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### 5. Start Frontend Server

```bash
cd frontend

# Development mode
npm run dev
```

Frontend should start on http://localhost:3000

### 6. Verify Setup

**Test Phase II functionality** (should still work):
1. Open http://localhost:3000
2. Sign up or sign in
3. Create a task using the form
4. Verify task appears in list

**Test Phase III functionality** (new):
1. Navigate to http://localhost:3000/chat
2. Send a message: "What are my tasks?"
3. Verify AI responds with task list
4. Send: "Create a task to buy groceries"
5. Verify AI creates task and confirms

---

## Development Workflow

### Running Tests

**Backend Tests**:
```bash
cd backend

# Run all tests
pytest

# Run specific test files
pytest tests/test_chat_api.py
pytest tests/test_mcp_tools.py
pytest tests/test_ai_agent.py

# Run with coverage
pytest --cov=src --cov-report=html
```

**Frontend Tests**:
```bash
cd frontend

# Run unit tests
npm test

# Run E2E tests
npm run test:e2e
```

### Testing MCP Tools Directly

Test MCP tools in isolation without AI agent:

```python
# backend/tests/manual_test_mcp.py
from src.mcp.tools.create_task import CreateTaskTool
from src.mcp.tools.get_tasks import GetTasksTool

# Create task
create_tool = CreateTaskTool()
result = create_tool.execute(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    title="Test task",
    description="Testing MCP tool"
)
print(result)
# Expected: {"success": true, "task_id": "...", "message": "..."}

# Get tasks
get_tool = GetTasksTool()
result = get_tool.execute(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    filter="all"
)
print(result)
# Expected: {"success": true, "tasks": [...], "count": 1}
```

### Testing AI Agent

Test AI agent with conversation context:

```python
# backend/tests/manual_test_agent.py
from src.ai.agent import create_agent
from src.mcp.registry import get_mcp_tools

# Initialize agent
agent = create_agent(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4",
    tools=get_mcp_tools()
)

# Test conversation
user_id = "550e8400-e29b-41d4-a716-446655440000"
conversation_history = []

# First message
response = agent.run(
    messages=conversation_history,
    user_message="Create a task to buy groceries",
    user_id=user_id
)
print(f"AI: {response.content}")
print(f"Tools called: {response.tool_calls}")

# Continue conversation
conversation_history.append({"role": "user", "content": "Create a task to buy groceries"})
conversation_history.append({"role": "assistant", "content": response.content})

response = agent.run(
    messages=conversation_history,
    user_message="What are my tasks?",
    user_id=user_id
)
print(f"AI: {response.content}")
```

### Testing Chat API Endpoint

Test the full chat endpoint with curl:

```bash
# Get auth token first (Phase II login)
TOKEN=$(curl -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' \
  | jq -r '.token')

USER_ID="550e8400-e29b-41d4-a716-446655440000"

# Send chat message (new conversation)
curl -X POST http://localhost:8000/api/${USER_ID}/chat \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a task to buy groceries"
  }' | jq

# Expected response:
# {
#   "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
#   "response": "I've created a task titled 'Buy groceries' for you...",
#   "tool_calls": [...]
# }

# Continue conversation
CONV_ID="7c9e6679-7425-40de-944b-e07fc1f90ae7"

curl -X POST http://localhost:8000/api/${USER_ID}/chat \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"conversation_id\": \"${CONV_ID}\",
    \"message\": \"What are my tasks?\"
  }" | jq
```

---

## Common Issues & Troubleshooting

### Issue: "OpenAI API key not found"

**Symptom**: Backend fails to start or chat endpoint returns 500 error

**Solution**:
1. Verify `OPENAI_API_KEY` is set in `backend/.env`
2. Ensure API key starts with `sk-proj-` or `sk-`
3. Check API key is valid at https://platform.openai.com/api-keys
4. Restart backend server after updating .env

### Issue: "Conversation not found" error

**Symptom**: Chat endpoint returns 404 when providing conversation_id

**Solution**:
1. Verify conversation_id is valid UUID
2. Check conversation belongs to authenticated user
3. Query database: `SELECT * FROM conversations WHERE id = 'conversation-id';`
4. If missing, start new conversation (omit conversation_id)

### Issue: AI responses are slow (>5 seconds)

**Symptom**: Chat endpoint takes long time to respond

**Solution**:
1. Check OpenAI API status: https://status.openai.com/
2. Consider switching to `gpt-3.5-turbo` for faster responses
3. Reduce conversation history length (limit to last 20 messages)
4. Check database query performance (conversation history fetch)

### Issue: "Rate limit exceeded" error

**Symptom**: Chat endpoint returns 429 error

**Solution**:
1. Wait 60 seconds before retrying (default rate limit)
2. Adjust `CHAT_RATE_LIMIT` in backend/.env if needed
3. Check OpenAI API rate limits: https://platform.openai.com/account/limits
4. Consider upgrading OpenAI API tier for higher limits

### Issue: MCP tools not working

**Symptom**: AI responds but tasks are not created/updated

**Solution**:
1. Check MCP server logs for errors
2. Verify tools are registered: Check `src/mcp/registry.py`
3. Test tools directly (see "Testing MCP Tools Directly" above)
4. Verify database connection and permissions
5. Check user_id is being passed correctly to tools

### Issue: Frontend chat interface not loading

**Symptom**: /chat page shows error or blank screen

**Solution**:
1. Verify OpenAI ChatKit is installed: `npm list @openai/chatkit`
2. Check browser console for errors
3. Verify API endpoint is correct in frontend/.env.local
4. Test chat API directly with curl (see above)
5. Check authentication token is valid

---

## Development Tips

### Monitoring AI Costs

OpenAI API usage incurs costs. Monitor usage:

1. Check OpenAI dashboard: https://platform.openai.com/usage
2. Set usage limits: https://platform.openai.com/account/billing/limits
3. Use `gpt-3.5-turbo` for development (cheaper than GPT-4)
4. Limit conversation history length to reduce token usage

**Estimated Costs** (as of 2026-02):
- GPT-4: ~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens
- GPT-3.5-turbo: ~$0.0015 per 1K input tokens, ~$0.002 per 1K output tokens
- Average conversation: 500-1000 tokens per message
- 100 messages with GPT-4: ~$3-5
- 100 messages with GPT-3.5-turbo: ~$0.15-0.25

### Debugging AI Responses

Enable verbose logging to see AI reasoning:

```python
# backend/src/ai/agent.py
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Log all AI interactions
logger.debug(f"User message: {user_message}")
logger.debug(f"Conversation history: {conversation_history}")
logger.debug(f"AI response: {response.content}")
logger.debug(f"Tool calls: {response.tool_calls}")
```

### Testing Different AI Models

Compare model performance:

```bash
# Test with GPT-4 (accurate but expensive)
OPENAI_MODEL=gpt-4 pytest tests/test_ai_agent.py

# Test with GPT-3.5-turbo (faster and cheaper)
OPENAI_MODEL=gpt-3.5-turbo pytest tests/test_ai_agent.py

# Test with GPT-4-turbo (good balance)
OPENAI_MODEL=gpt-4-turbo pytest tests/test_ai_agent.py
```

### Hot Reloading

Both backend and frontend support hot reloading:

- **Backend**: `uvicorn --reload` automatically restarts on code changes
- **Frontend**: `npm run dev` automatically rebuilds on code changes
- **Database**: Migrations require manual application

---

## Next Steps

After verifying local setup:

1. **Implement User Stories**: Follow tasks.md (generated by `/sp.tasks`)
2. **Write Tests**: Add tests for each user story
3. **Iterate on AI Prompts**: Refine system prompts based on testing
4. **Optimize Performance**: Profile and optimize slow queries
5. **Deploy to Staging**: Test in production-like environment

---

## Useful Commands

```bash
# Backend
cd backend
uvicorn src.main:app --reload                    # Start dev server
pytest                                            # Run tests
pytest --cov=src                                  # Run tests with coverage
python -m alembic upgrade head                    # Apply migrations
python -m alembic downgrade -1                    # Rollback migration

# Frontend
cd frontend
npm run dev                                       # Start dev server
npm test                                          # Run tests
npm run build                                     # Build for production
npm run lint                                      # Lint code

# Database
psql -U user -d todo_db                          # Connect to database
psql -U user -d todo_db -f migrations/003_add_conversations.sql  # Run migration
psql -U user -d todo_db -c "SELECT * FROM conversations;"        # Query conversations

# Docker (if using)
docker-compose up -d                             # Start all services
docker-compose logs -f backend                   # View backend logs
docker-compose down                              # Stop all services
```

---

## Resources

- **OpenAI Agents SDK**: https://platform.openai.com/docs/agents
- **MCP Protocol**: https://modelcontextprotocol.io/
- **OpenAI ChatKit**: https://github.com/openai/chatkit
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Next.js Docs**: https://nextjs.org/docs
- **Feature Specification**: `specs/001-ai-chatbot/spec.md`
- **Data Model**: `specs/001-ai-chatbot/data-model.md`
- **API Contracts**: `specs/001-ai-chatbot/contracts/`

---

## Support

For issues or questions:
1. Check this quickstart guide
2. Review feature specification and contracts
3. Check backend/frontend logs for errors
4. Test components in isolation (MCP tools, AI agent, API endpoint)
5. Consult OpenAI documentation for API-specific issues
