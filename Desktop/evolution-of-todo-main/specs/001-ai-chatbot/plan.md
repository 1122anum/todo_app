# Implementation Plan: AI-Powered Todo Chatbot

**Branch**: `001-ai-chatbot` | **Date**: 2026-02-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-chatbot/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

AI-powered Todo Chatbot enabling natural language task management through conversational interface. Users create, query, update, and delete tasks by chatting with an AI assistant instead of using traditional forms. System uses OpenAI Agents SDK for AI logic, MCP (Model Context Protocol) tools as exclusive interface between AI and data operations, and maintains stateless server architecture with database-persisted conversation state. Frontend uses OpenAI ChatKit for conversational UI, backend extends existing Phase II FastAPI application with new chat endpoint and conversation/message persistence.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), JavaScript/TypeScript (Frontend)
**Primary Dependencies**: FastAPI (Backend Framework), OpenAI Agents SDK (AI Logic), Official MCP SDK (Tool Integration), OpenAI ChatKit (Frontend UI), SQLModel (ORM), Better Auth (Authentication), Neon Serverless PostgreSQL (Database)
**Storage**: Neon Serverless PostgreSQL (existing from Phase II) - stores Tasks, Conversations, Messages
**Testing**: pytest (Backend), Jest/Cypress (Frontend), MCP tool testing, AI conversation testing
**Target Platform**: Web application - Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (extends existing Phase II full-stack application)
**Performance Goals**: <3s API response time (95th percentile including AI processing), <2s conversation history load (up to 100 messages), 100 concurrent chat sessions, <500ms database queries
**Constraints**: Stateless server architecture (no in-memory conversation state), AI must NOT directly access database (only through MCP tools), all task operations through MCP interface, each request independent (fetch context from database), conversation state database-persisted
**Scale/Scope**: 100 concurrent users, conversations with up to 100 messages, 1000 character message limit, 5 user stories (P1-P5), 20 functional requirements, 3 new database entities (Task existing, Conversation new, Message new)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Phase III Requirements Validation:**

✅ **Stateless Server Architecture**: Plan enforces stateless FastAPI backend with no in-memory conversation state. All conversation context fetched from database per request.

✅ **AI Logic Isolation**: OpenAI Agents SDK exclusively handles all AI logic and natural language processing. No AI logic in application code.

✅ **MCP Tool Interface**: All task operations (create, read, update, delete) go through MCP tools only. AI cannot directly access database or task service.

✅ **Database-Persisted State**: Conversation and Message entities stored in Neon PostgreSQL. No session state in server memory.

✅ **Technology Stack Compliance**:
- Backend: FastAPI (Python 3.11+) ✓
- AI Framework: OpenAI Agents SDK ✓
- MCP Integration: Official MCP SDK ✓
- Database: Neon Serverless PostgreSQL (continued from Phase II) ✓
- ORM: SQLModel (continued from Phase II) ✓
- Frontend: OpenAI ChatKit ✓
- Authentication: Better Auth (continued from Phase II) ✓

✅ **Behavioral Requirements**: Plan includes friendly confirmations, graceful error handling, and clear feedback for all user actions.

✅ **User Isolation**: All endpoints enforce user_id filtering. Users can only access their own conversations and tasks.

✅ **Phase Boundaries**: No Phase IV features (multi-agent, event-driven, real-time collaboration). Builds on Phase II foundation without violating phase governance.

**GATE STATUS: PASS** - All Phase III constitutional requirements satisfied. No violations requiring justification.

**Post-Design Re-Evaluation (Phase 1 Complete)**:

✅ **Stateless Architecture Maintained**: Data model and API contracts enforce stateless design. Conversation history fetched from database per request (data-model.md). No in-memory session state.

✅ **MCP Tool Isolation Verified**: MCP tools contract (contracts/mcp-tools.md) defines 4 stateless tools (create_task, get_tasks, update_task, delete_task) as exclusive AI-to-data interface. Tools accept user_id parameter and enforce user isolation.

✅ **Database Schema Compliant**: Migration script (data-model.md) adds Conversations and Messages tables without modifying existing Phase II tables. Backward compatible.

✅ **API Contract Aligned**: Chat API (contracts/chat-api.yaml) follows REST conventions, enforces authentication, and maintains stateless request/response pattern.

✅ **Technology Stack Verified**: All design artifacts use approved Phase III technologies (OpenAI Agents SDK, MCP SDK, ChatKit, FastAPI, SQLModel, PostgreSQL).

✅ **User Isolation Enforced**: All database queries filter by user_id. Foreign key constraints and indexes support user isolation (data-model.md).

**FINAL GATE STATUS: PASS** - Design artifacts fully compliant with Phase III constitution. Ready for task generation (/sp.tasks).

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── task.py              # Existing from Phase II
│   │   ├── conversation.py      # New - Phase III
│   │   └── message.py           # New - Phase III
│   ├── services/
│   │   ├── task_service.py      # Existing from Phase II
│   │   ├── auth_service.py      # Existing from Phase II
│   │   └── chat_service.py      # New - Phase III (orchestrates AI + MCP)
│   ├── api/
│   │   ├── tasks.py             # Existing from Phase II
│   │   ├── auth.py              # Existing from Phase II
│   │   └── chat.py              # New - Phase III (POST /api/{user_id}/chat)
│   ├── mcp/
│   │   ├── server.py            # New - MCP server initialization
│   │   ├── tools/
│   │   │   ├── create_task.py   # New - MCP tool
│   │   │   ├── get_tasks.py     # New - MCP tool
│   │   │   ├── update_task.py   # New - MCP tool
│   │   │   └── delete_task.py   # New - MCP tool
│   │   └── registry.py          # New - Tool registration
│   └── ai/
│       ├── agent.py             # New - OpenAI Agents SDK setup
│       ├── prompts.py           # New - System prompts and rules
│       └── runner.py            # New - Agent execution logic
└── tests/
    ├── test_chat_api.py         # New - Chat endpoint tests
    ├── test_mcp_tools.py        # New - MCP tool tests
    ├── test_ai_agent.py         # New - AI agent tests
    └── test_conversation.py     # New - Conversation persistence tests

frontend/
├── src/
│   ├── components/
│   │   ├── TaskList.tsx         # Existing from Phase II
│   │   ├── TaskForm.tsx         # Existing from Phase II
│   │   └── ChatInterface.tsx    # New - Phase III (OpenAI ChatKit)
│   ├── pages/
│   │   ├── index.tsx            # Existing from Phase II
│   │   ├── tasks.tsx            # Existing from Phase II
│   │   └── chat.tsx             # New - Phase III (Chat page)
│   └── services/
│       ├── api.ts               # Existing from Phase II
│       └── chatApi.ts           # New - Phase III (Chat API client)
└── tests/
    └── chat.test.tsx            # New - Chat interface tests
```

**Structure Decision**: Web application structure (Option 2) selected. Extends existing Phase II backend/frontend separation. New Phase III components added to existing structure: backend adds mcp/ and ai/ directories for MCP server and AI agent logic, api/chat.py for chat endpoint, models for Conversation/Message entities. Frontend adds ChatInterface component and chat page using OpenAI ChatKit. Maintains clear separation between AI logic (ai/), MCP tools (mcp/), and application services (services/).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
