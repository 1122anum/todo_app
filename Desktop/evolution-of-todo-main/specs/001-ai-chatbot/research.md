# Research: AI-Powered Todo Chatbot

**Feature**: 001-ai-chatbot
**Date**: 2026-02-05
**Phase**: 0 - Research

## Purpose

Document technical research findings and architectural decisions for integrating OpenAI Agents SDK, MCP (Model Context Protocol) tools, and OpenAI ChatKit into the existing Phase II Todo application.

## Research Areas

### 1. OpenAI Agents SDK Integration

**Decision**: Use OpenAI Agents SDK for all AI logic and natural language processing

**Rationale**:
- Provides high-level abstractions for building conversational AI agents
- Handles conversation context management and tool calling
- Integrates seamlessly with OpenAI's language models
- Supports streaming responses for better UX
- Built-in error handling and retry logic

**Integration Pattern**:
```python
# backend/src/ai/agent.py
from openai import OpenAI
from openai.agents import Agent

# Initialize agent with system prompt and tools
agent = Agent(
    client=OpenAI(api_key=os.getenv("OPENAI_API_KEY")),
    model="gpt-4",  # or gpt-3.5-turbo for cost optimization
    instructions=SYSTEM_PROMPT,
    tools=mcp_tools  # MCP tools registered here
)

# Run agent with conversation history
response = agent.run(
    messages=conversation_history,
    user_message=user_input
)
```

**Alternatives Considered**:
- **LangChain**: More complex, heavier framework with many abstractions. OpenAI Agents SDK is simpler and more focused.
- **Direct OpenAI API**: Would require manual conversation management, tool calling logic, and error handling. Agents SDK provides these out of the box.
- **Custom AI Framework**: Would require significant development effort and maintenance. Not justified for Phase III scope.

**Key Considerations**:
- API key management: Store in environment variables, never commit to repository
- Model selection: Start with gpt-4 for accuracy, consider gpt-3.5-turbo for cost optimization
- Token limits: Monitor conversation history length, implement truncation if needed
- Rate limiting: Implement at application level to prevent API quota exhaustion

---

### 2. MCP (Model Context Protocol) Tool Implementation

**Decision**: Use Official MCP SDK to create stateless tools as exclusive AI-to-data interface

**Rationale**:
- Enforces clean separation between AI logic and data operations
- Tools are stateless and testable in isolation
- Provides standardized interface for tool registration and execution
- Enables tool reusability across different AI frameworks
- Aligns with Phase III constitutional requirement: "AI MUST NOT directly access database"

**Tool Pattern**:
```python
# backend/src/mcp/tools/create_task.py
from mcp import Tool

class CreateTaskTool(Tool):
    name = "create_task"
    description = "Creates a new todo task for the user"

    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Task title"},
            "description": {"type": "string", "description": "Task description (optional)"}
        },
        "required": ["title"]
    }

    def execute(self, user_id: str, title: str, description: str = "") -> dict:
        # Call existing Phase II task service
        task = task_service.create_task(
            user_id=user_id,
            title=title,
            description=description
        )
        return {
            "success": True,
            "task_id": task.id,
            "message": f"Task '{title}' created successfully"
        }
```

**Tool Registry**:
- `create_task`: Creates new task with title and optional description
- `get_tasks`: Retrieves user's tasks with optional filters (completed, search term)
- `update_task`: Updates task title, description, or completion status
- `delete_task`: Deletes task with confirmation (returns confirmation prompt)

**Alternatives Considered**:
- **Direct Service Calls**: Would violate constitutional requirement for MCP-only interface
- **Custom Tool Framework**: MCP SDK provides standardized patterns, no need to reinvent
- **GraphQL/REST from AI**: Would create tight coupling and violate stateless architecture

**Key Considerations**:
- User isolation: All tools must accept user_id parameter and enforce filtering
- Error handling: Tools return structured responses with success/error status
- Validation: Tools validate inputs before calling services
- Idempotency: Update/delete operations should be idempotent where possible

---

### 3. OpenAI ChatKit Frontend Integration

**Decision**: Use OpenAI ChatKit for conversational UI component

**Rationale**:
- Pre-built React components for chat interface
- Handles message rendering, input, and streaming responses
- Consistent UX with OpenAI's chat interfaces
- Reduces frontend development effort
- Supports markdown rendering and code blocks

**Integration Pattern**:
```typescript
// frontend/src/components/ChatInterface.tsx
import { ChatKit } from '@openai/chatkit';

export function ChatInterface() {
  const [conversationId, setConversationId] = useState<string | null>(null);

  const handleSendMessage = async (message: string) => {
    const response = await fetch(`/api/${userId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: conversationId,
        message: message
      })
    });

    const data = await response.json();
    setConversationId(data.conversation_id);
    return data.response;
  };

  return (
    <ChatKit
      onSendMessage={handleSendMessage}
      placeholder="Ask me to create, view, or manage your tasks..."
    />
  );
}
```

**Alternatives Considered**:
- **Custom Chat UI**: Would require significant development effort for message rendering, input handling, and streaming
- **react-chatbot-kit**: Less polished, not optimized for OpenAI integration
- **Vercel AI SDK**: Good alternative but ChatKit is more focused on chat UI

**Key Considerations**:
- Authentication: Pass user token in API requests
- Error handling: Display user-friendly error messages in chat
- Loading states: Show typing indicator while AI processes
- Message history: Load previous conversation on mount

---

### 4. Stateless Conversation Context Management

**Decision**: Fetch conversation history from database for each request, no in-memory state

**Rationale**:
- Aligns with Phase III constitutional requirement: "Server MUST be stateless"
- Enables horizontal scaling without session affinity
- Simplifies deployment and reduces memory usage
- Conversation state survives server restarts

**Implementation Pattern**:
```python
# backend/src/services/chat_service.py
async def process_chat_message(user_id: str, message: str, conversation_id: str = None):
    # 1. Get or create conversation
    if conversation_id:
        conversation = await get_conversation(conversation_id, user_id)
    else:
        conversation = await create_conversation(user_id)

    # 2. Fetch conversation history from database
    messages = await get_messages(conversation.id, user_id)
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    # 3. Save user message
    await save_message(conversation.id, user_id, "user", message)

    # 4. Run AI agent with history
    response = await agent.run(
        messages=conversation_history,
        user_message=message,
        user_id=user_id  # Pass to MCP tools
    )

    # 5. Save assistant response
    await save_message(conversation.id, user_id, "assistant", response.content)

    # 6. Return response with conversation_id
    return {
        "conversation_id": conversation.id,
        "response": response.content,
        "tool_calls": response.tool_calls
    }
```

**Alternatives Considered**:
- **In-Memory Session State**: Violates constitutional requirement, prevents horizontal scaling
- **Redis Session Store**: Adds complexity and external dependency, not needed for Phase III
- **Client-Side State**: Would require sending full history in each request, inefficient

**Key Considerations**:
- Database query optimization: Index on conversation_id and user_id
- Message history limits: Consider truncating very long conversations (>100 messages)
- Caching: Consider short-lived cache (5-10 minutes) for active conversations if performance issues arise
- Concurrency: Handle concurrent requests to same conversation gracefully

---

### 5. AI Model Selection

**Decision**: Start with GPT-4 for accuracy, evaluate GPT-3.5-turbo for cost optimization

**Rationale**:
- GPT-4 provides better intent interpretation and fewer errors
- Task management is relatively simple domain, GPT-3.5-turbo may be sufficient
- Cost vs. accuracy tradeoff should be evaluated with real usage data

**Model Comparison**:
| Model | Accuracy | Cost | Latency | Recommendation |
|-------|----------|------|---------|----------------|
| GPT-4 | High | High | ~2-3s | Start here for quality |
| GPT-3.5-turbo | Good | Low | ~1-2s | Evaluate after testing |
| GPT-4-turbo | High | Medium | ~1-2s | Good middle ground |

**Key Considerations**:
- Make model configurable via environment variable
- Monitor accuracy metrics (successful operations without clarification)
- Monitor cost per conversation
- Consider A/B testing different models

---

### 6. System Prompt Design

**Decision**: Create comprehensive system prompt with task management rules and behavioral guidelines

**System Prompt Structure**:
```
You are a helpful AI assistant for managing todo tasks. Your role is to help users create, view, update, and delete their tasks through natural conversation.

CAPABILITIES:
- Create tasks with titles and optional descriptions
- View all tasks or filter by completion status
- Update task details or mark tasks as complete
- Delete tasks (always ask for confirmation first)

BEHAVIORAL RULES:
1. Always provide friendly confirmations after successful operations
2. Ask clarifying questions when user intent is ambiguous
3. For delete operations, always confirm before executing
4. If multiple tasks match a query, list them and ask which one
5. Provide helpful error messages when operations fail
6. Stay focused on task management - politely decline unrelated requests

RESPONSE STYLE:
- Be concise and friendly
- Use natural language, not technical jargon
- Confirm actions with specific details (e.g., "I've created a task titled 'Buy groceries'")
- When listing tasks, format them clearly with status indicators
```

**Key Considerations**:
- Keep prompt concise to reduce token usage
- Include examples of good responses
- Update prompt based on user feedback and common issues
- Version control prompt changes

---

## Technical Decisions Summary

| Decision Area | Choice | Rationale |
|--------------|--------|-----------|
| AI Framework | OpenAI Agents SDK | High-level abstractions, built-in tool calling |
| Tool Interface | Official MCP SDK | Enforces separation, stateless, testable |
| Frontend UI | OpenAI ChatKit | Pre-built components, consistent UX |
| State Management | Database-persisted | Stateless architecture, horizontal scaling |
| AI Model | GPT-4 (initial) | Accuracy priority, evaluate cost later |
| Conversation Limit | 100 messages | Balance context vs. performance |
| Message Length | 1000 characters | Reasonable for chat, prevents abuse |

---

## Open Questions Resolved

1. **Q: Which OpenAI model to use?**
   A: Start with GPT-4 for accuracy, make configurable for future optimization

2. **Q: How to handle very long conversations?**
   A: Load full history initially, implement truncation if performance issues arise (deferred to implementation)

3. **Q: Should we cache conversation history?**
   A: No caching initially (stateless requirement), consider short-lived cache only if performance issues arise

4. **Q: How to handle concurrent requests to same conversation?**
   A: Database transactions ensure consistency, last-write-wins for message ordering (acceptable for Phase III)

5. **Q: Should we support conversation export/backup?**
   A: Out of scope for Phase III (documented in spec)

---

## Next Steps

Phase 1 artifacts to generate:
1. **data-model.md**: Define Conversation and Message entities with relationships
2. **contracts/chat-api.yaml**: OpenAPI spec for POST /api/{user_id}/chat endpoint
3. **contracts/mcp-tools.yaml**: MCP tool schemas for all 4 tools
4. **quickstart.md**: Developer guide for running and testing the chatbot locally

---

## References

- OpenAI Agents SDK Documentation: https://platform.openai.com/docs/agents
- MCP Protocol Specification: https://modelcontextprotocol.io/
- OpenAI ChatKit: https://github.com/openai/chatkit
- Phase III Constitution: `.specify/memory/constitution.md`
- Feature Specification: `specs/001-ai-chatbot/spec.md`
