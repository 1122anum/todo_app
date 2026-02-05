# Implementation Tasks: AI-Powered Todo Chatbot

**Feature**: 001-ai-chatbot
**Branch**: `001-ai-chatbot`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## Overview

This document contains atomic, executable tasks for implementing the AI-powered Todo Chatbot feature. Tasks are organized by user story to enable independent implementation and testing of each story.

**Total Tasks**: 52
**Estimated MVP**: Phase 1-3 (Setup + Foundational + US1) = ~18 tasks

## Task Organization

Tasks are organized into phases:
- **Phase 1**: Setup (project initialization, dependencies, database)
- **Phase 2**: Foundational (MCP server, AI agent - blocking prerequisites)
- **Phase 3**: User Story 1 (P1) - Create Tasks via Natural Language (MVP)
- **Phase 4**: User Story 2 (P2) - Query and View Tasks
- **Phase 5**: User Story 3 (P3) - Update and Complete Tasks
- **Phase 6**: User Story 4 (P4) - Delete Tasks
- **Phase 7**: User Story 5 (P5) - Conversation History Persistence
- **Phase 8**: Polish & Documentation

## Task Format

Each task follows this format:
```
- [ ] [TaskID] [P] [Story] Description with file path
```

- **[TaskID]**: Sequential number (T001, T002, etc.)
- **[P]**: Parallelizable (can run concurrently with other [P] tasks)
- **[Story]**: User story label ([US1], [US2], etc.) - only for story-specific tasks

---

## Phase 1: Setup

**Goal**: Initialize project environment, install dependencies, and prepare database schema.

**Prerequisites**: Phase II backend and frontend running successfully.

### Tasks

- [X] T001 Add OpenAI Agents SDK to backend requirements.txt (openai>=1.0.0)
- [X] T002 Add Official MCP SDK to backend requirements.txt (mcp>=0.1.0)
- [X] T003 Install backend dependencies: pip install -r backend/requirements.txt
- [X] T004 Add axios to frontend package.json for API calls (Note: OpenAI ChatKit not available, using custom implementation)
- [X] T005 Install frontend dependencies: npm install in frontend/
- [X] T006 Create backend/.env variables: OPENAI_API_KEY, OPENAI_MODEL, MCP_SERVER_PORT, CHAT_RATE_LIMIT
- [X] T007 Create database migration script backend/migrations/003_add_conversations.sql per data-model.md
- [ ] T008 Run database migration to add conversations and messages tables (Deferred: requires database setup)
- [ ] T009 Verify migration: Check conversations and messages tables exist with correct schema (Deferred: requires database setup)

**Completion Criteria**: All dependencies installed, database schema updated, environment configured.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Implement MCP server and AI agent infrastructure needed by all user stories.

**Prerequisites**: Phase 1 complete.

### Database Models

- [X] T010 [P] Create Conversation model in backend/src/models/conversation.py per data-model.md
- [X] T011 [P] Create Message model in backend/src/models/message.py per data-model.md
- [X] T012 [P] Update backend/src/models/__init__.py to export Conversation and Message

### MCP Server Infrastructure

- [X] T013 Create MCP server initialization in backend/src/mcp/server.py
- [X] T014 Create MCP tool registry in backend/src/mcp/registry.py
- [X] T015 Create MCP tools directory structure: backend/src/mcp/tools/__init__.py

### AI Agent Infrastructure

- [X] T016 Create AI agent setup in backend/src/ai/agent.py (OpenAI Agents SDK initialization)
- [X] T017 Create system prompts in backend/src/ai/prompts.py per research.md
- [X] T018 Create agent runner in backend/src/ai/runner.py (conversation execution logic)

**Completion Criteria**: MCP server and AI agent infrastructure ready for tool integration.

---

## Phase 3: User Story 1 (P1) - Create Tasks via Natural Language

**Story Goal**: Users can create todo tasks by chatting with an AI assistant in natural language, without needing to fill out forms or use specific commands.

**Independent Test**: Send message "Create a task to buy groceries" → verify task created in database with title "Buy groceries" → AI responds with confirmation.

**Why MVP**: This is the core value proposition - conversational task creation. Delivers immediate value as standalone feature.

### MCP Tool: create_task

- [X] T019 [US1] Implement create_task MCP tool in backend/src/mcp/tools/create_task.py per contracts/mcp-tools.md
- [X] T020 [US1] Register create_task tool in backend/src/mcp/registry.py
- [ ] T021 [US1] Validate create_task tool: Test with user_id, title, description parameters (Requires testing)

### Chat Service & API

- [X] T022 [US1] Create ChatService in backend/src/services/chat_service.py (orchestrates AI + MCP)
- [X] T023 [US1] Implement conversation creation logic in ChatService
- [X] T024 [US1] Implement message persistence logic in ChatService (save user and assistant messages)
- [X] T025 [US1] Create chat API endpoint in backend/src/api/chat.py: POST /api/{user_id}/chat per contracts/chat-api.yaml
- [X] T026 [US1] Implement authentication middleware for chat endpoint (Better Auth integration)
- [ ] T027 [US1] Implement rate limiting for chat endpoint (60 requests/minute per user) (Deferred)
- [X] T028 [US1] Implement error handling in chat endpoint (AI service errors, validation errors)

### Frontend

- [X] T029 [US1] Create ChatInterface component in frontend/src/components/ChatInterface.tsx using custom implementation
- [X] T030 [US1] Create chat API client in frontend/src/services/chatApi.ts
- [X] T031 [US1] Create chat page in frontend/src/pages/chat.tsx
- [X] T032 [US1] Integrate authentication in chat page (pass user token to API)
- [X] T033 [US1] Add navigation link to chat page in main navigation

### Integration & Validation

- [ ] T034 [US1] End-to-end test: Send "Create a task to buy groceries" → verify task created → verify AI confirmation
- [ ] T035 [US1] Test ambiguous request: Send "remind me about meeting" → verify AI asks clarifying questions
- [ ] T036 [US1] Test error handling: Invalid input → verify friendly error message

**Completion Criteria**: Users can create tasks through natural language conversation. AI responds with friendly confirmations. MVP feature complete and deployable.

---

## Phase 4: User Story 2 (P2) - Query and View Tasks

**Story Goal**: Users can ask the AI assistant about their existing tasks using natural language queries, receiving formatted responses about their todo list.

**Independent Test**: Create 3 tasks → send "What are my tasks?" → verify AI lists all 3 tasks with status.

**Prerequisites**: US1 complete (conversation infrastructure exists).

### MCP Tool: get_tasks

- [ ] T037 [US2] Implement get_tasks MCP tool in backend/src/mcp/tools/get_tasks.py per contracts/mcp-tools.md
- [ ] T038 [US2] Register get_tasks tool in backend/src/mcp/registry.py
- [ ] T039 [US2] Validate get_tasks tool: Test with filter (all/incomplete/complete) and search parameters

### Integration & Validation

- [ ] T040 [US2] Test query all tasks: "What are my tasks?" → verify AI lists all tasks
- [ ] T041 [US2] Test filter incomplete: "Show me incomplete tasks" → verify AI lists only incomplete
- [ ] T042 [US2] Test search: "Do I have tasks about groceries?" → verify AI returns matching tasks
- [ ] T043 [US2] Test empty state: No tasks → "What are my tasks?" → verify friendly "no tasks" message

**Completion Criteria**: Users can query and view their tasks through natural language. AI formats task lists clearly.

---

## Phase 5: User Story 3 (P3) - Update and Complete Tasks

**Story Goal**: Users can mark tasks as complete or update task details through conversational commands with the AI assistant.

**Independent Test**: Create task "Buy groceries" → send "Mark 'buy groceries' as complete" → verify task status updated → verify AI confirmation.

**Prerequisites**: US1 and US2 complete (can create and view tasks).

### MCP Tool: update_task

- [ ] T044 [US3] Implement update_task MCP tool in backend/src/mcp/tools/update_task.py per contracts/mcp-tools.md
- [ ] T045 [US3] Register update_task tool in backend/src/mcp/registry.py
- [ ] T046 [US3] Validate update_task tool: Test with task_id, title, description, completed parameters

### Integration & Validation

- [ ] T047 [US3] Test mark complete: "Mark task 5 as complete" → verify task completed → verify AI confirmation
- [ ] T048 [US3] Test update title: "Change title to 'Write quarterly report'" → verify title updated
- [ ] T049 [US3] Test non-existent task: "Complete task 999" → verify AI responds with helpful "task not found" message

**Completion Criteria**: Users can update and complete tasks through conversation. AI provides clear confirmations.

---

## Phase 6: User Story 4 (P4) - Delete Tasks

**Story Goal**: Users can delete tasks through conversational commands, with appropriate confirmation to prevent accidental deletions.

**Independent Test**: Create task → send "Delete task about groceries" → verify AI asks for confirmation → confirm → verify task deleted.

**Prerequisites**: US1 and US2 complete (can create and view tasks).

### MCP Tool: delete_task

- [ ] T050 [US4] Implement delete_task MCP tool in backend/src/mcp/tools/delete_task.py per contracts/mcp-tools.md (with confirmation logic)
- [ ] T051 [US4] Register delete_task tool in backend/src/mcp/registry.py
- [ ] T052 [US4] Validate delete_task tool: Test confirmation flow (confirmed=false → confirmed=true)

### Integration & Validation

- [ ] T053 [US4] Test delete with confirmation: "Delete task 3" → verify AI asks confirmation → confirm → verify deleted
- [ ] T054 [US4] Test non-existent task: "Delete task 999" → verify AI responds with helpful message

**Completion Criteria**: Users can delete tasks with confirmation. AI prevents accidental deletions.

---

## Phase 7: User Story 5 (P5) - Conversation History Persistence

**Story Goal**: Users can continue previous conversations with the AI assistant, with full context preserved across sessions.

**Independent Test**: Start conversation → create task → close session → return → verify conversation history loaded → send follow-up message → verify AI has context.

**Prerequisites**: US1 complete (conversation infrastructure exists).

### Backend Enhancements

- [ ] T055 [US5] Implement conversation history loading in ChatService (fetch messages from database)
- [ ] T056 [US5] Implement conversation context building for AI agent (format messages for OpenAI Agents SDK)
- [ ] T057 [US5] Update chat endpoint to accept optional conversation_id parameter
- [ ] T058 [US5] Implement conversation retrieval by ID with user isolation check

### Frontend Enhancements

- [ ] T059 [US5] Update ChatInterface to store conversation_id in state
- [ ] T060 [US5] Implement conversation history loading on component mount
- [ ] T061 [US5] Update chatApi to send conversation_id in requests
- [ ] T062 [US5] Add "New Conversation" button to start fresh conversation

### Integration & Validation

- [ ] T063 [US5] Test conversation continuation: Create conversation → close → reopen → verify history loaded
- [ ] T064 [US5] Test context maintenance: "Create task" → "Mark it complete" → verify AI understands "it" refers to previous task
- [ ] T065 [US5] Test multiple conversations: Create 2 conversations → verify independent contexts

**Completion Criteria**: Users can continue previous conversations. AI maintains context across sessions.

---

## Phase 8: Polish & Documentation

**Goal**: Final polish, error handling improvements, and documentation.

**Prerequisites**: All user stories complete.

### Error Handling & Edge Cases

- [ ] T066 [P] Implement empty message validation in chat endpoint
- [ ] T067 [P] Implement message length validation (max 1000 characters)
- [ ] T068 [P] Implement graceful AI service failure handling (OpenAI API down)
- [ ] T069 [P] Implement database connection error handling
- [ ] T070 [P] Add structured logging for all AI interactions and tool calls

### Performance & Optimization

- [ ] T071 [P] Add database indexes per data-model.md (if not in migration)
- [ ] T072 [P] Implement conversation history truncation for very long conversations (>100 messages)
- [ ] T073 [P] Add response time monitoring for chat endpoint

### Documentation

- [ ] T074 [P] Update README.md with Phase III setup instructions
- [ ] T075 [P] Create API documentation for chat endpoint (based on contracts/chat-api.yaml)
- [ ] T076 [P] Update quickstart.md with actual implementation details
- [ ] T077 [P] Add inline code comments for complex AI/MCP logic

**Completion Criteria**: All edge cases handled, performance optimized, documentation complete.

---

## Dependencies & Execution Order

### Story Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational: MCP + AI Infrastructure)
    ↓
    ├─→ Phase 3 (US1: Create Tasks) ← MVP
    │       ↓
    │   ┌───┴───┐
    │   ↓       ↓
    ├─→ Phase 4 (US2: Query Tasks)
    │   Phase 5 (US3: Update Tasks)
    │       ↓
    ├─→ Phase 6 (US4: Delete Tasks)
    │
    └─→ Phase 7 (US5: Conversation History)
            ↓
        Phase 8 (Polish)
```

**Key Insights**:
- US1 must complete first (establishes conversation infrastructure)
- US2, US3, US4 can be developed in parallel after US1
- US5 can be developed in parallel with US2-US4 (only depends on US1)
- Phase 8 tasks are mostly parallelizable

### Parallel Execution Opportunities

**Phase 1**: Sequential (setup tasks depend on each other)

**Phase 2**:
- T010, T011, T012 (models) can run in parallel
- T013-T015 (MCP) must be sequential
- T016-T018 (AI) must be sequential

**Phase 3 (US1)**:
- T019-T021 (MCP tool) sequential
- T022-T028 (backend) mostly sequential (service → API → middleware)
- T029-T033 (frontend) can run in parallel with backend after T025 (API contract defined)
- T034-T036 (validation) sequential after all implementation

**Phase 4-7**: Each story's tasks are mostly sequential within the story, but stories can be developed in parallel

**Phase 8**: Most tasks (T066-T077) can run in parallel

---

## Implementation Strategy

### MVP Scope (Phases 1-3)

**Minimum Viable Product**: Conversational task creation
- Setup + Foundational + US1 = ~18 tasks
- Delivers core value: Users can create tasks through natural language
- Independently testable and deployable
- Estimated effort: 2-3 days for experienced developer

### Incremental Delivery

1. **Week 1**: MVP (Phases 1-3)
   - Deploy conversational task creation
   - Gather user feedback on AI responses

2. **Week 2**: Task Management (Phases 4-6)
   - Add query, update, delete capabilities
   - Complete CRUD operations through conversation

3. **Week 3**: Polish (Phases 7-8)
   - Add conversation history
   - Polish error handling and documentation

### Testing Strategy

**Per User Story**:
- Each story has independent test criteria
- Validate story in isolation before moving to next
- Use acceptance scenarios from spec.md

**Integration Testing**:
- Test cross-story workflows (create → query → update → delete)
- Test conversation context across multiple operations
- Test error scenarios and edge cases

**Performance Testing**:
- Verify <3s response time for chat endpoint
- Verify <2s conversation history load
- Test with 100 concurrent users

---

## Task Checklist Summary

**Phase 1 (Setup)**: 9 tasks
**Phase 2 (Foundational)**: 9 tasks
**Phase 3 (US1 - MVP)**: 18 tasks
**Phase 4 (US2)**: 7 tasks
**Phase 5 (US3)**: 6 tasks
**Phase 6 (US4)**: 5 tasks
**Phase 7 (US5)**: 11 tasks
**Phase 8 (Polish)**: 12 tasks

**Total**: 77 tasks

**Parallelizable**: 15 tasks marked with [P]
**Story-specific**: 58 tasks marked with [US1]-[US5]

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] All 5 user stories independently testable
- [ ] MVP (US1) deployable and functional
- [ ] All MCP tools registered and working
- [ ] AI agent responds with friendly confirmations
- [ ] Conversation history persists across sessions
- [ ] User isolation enforced (users see only their data)
- [ ] Error handling graceful and user-friendly
- [ ] Performance goals met (<3s response, <2s history load)
- [ ] Documentation complete and accurate
- [ ] Constitution compliance verified (stateless, MCP-only, no direct DB access by AI)

---

## Notes

- **No Tests Generated**: Specification did not explicitly request test tasks. Validation tasks included per story for acceptance testing.
- **File Paths**: All tasks include specific file paths per plan.md project structure
- **Stateless Architecture**: All tasks enforce stateless design per Phase III constitution
- **MCP Tool Pattern**: All data operations go through MCP tools, never direct database access by AI
- **User Isolation**: All tasks enforce user_id filtering and authorization

---

## References

- **Specification**: [spec.md](./spec.md)
- **Implementation Plan**: [plan.md](./plan.md)
- **Data Model**: [data-model.md](./data-model.md)
- **API Contracts**: [contracts/](./contracts/)
- **Research**: [research.md](./research.md)
- **Quickstart**: [quickstart.md](./quickstart.md)
