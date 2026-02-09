---
id: 2
title: Phase III AI Chatbot Constitution
stage: constitution
date: 2026-02-05
surface: agent
model: claude-sonnet-4-5
feature: none
branch: 001-full-stack-web-app
user: 1122anum
command: /sp.constitution
labels: ["constitution", "phase-iii", "ai-chatbot", "mcp", "governance"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (documentation update)
---

## Prompt

```text
# SP Constitution – Todo AI Chatbot (Phase III)

## 1. Purpose
Is phase ka goal ek AI-powered Todo Chatbot banana hai jo natural language
ke zariye tasks manage kare using MCP (Model Context Protocol).

## 2. Core Principles
- Server MUST be stateless
- AI logic OpenAI Agents SDK se handle hogi
- Task operations sirf MCP tools ke through hongi
- Conversation state database mein persist hogi
- AI kabhi directly database access nahi karega

## 3. Architectural Constraints
- Backend: FastAPI (Python)
- AI Framework: OpenAI Agents SDK
- MCP Server: Official MCP SDK
- Database: Neon Serverless PostgreSQL
- ORM: SQLModel
- Auth: Better Auth
- Frontend: OpenAI ChatKit

## 4. Behavioral Rules
- User ke har action par friendly confirmation zaroori hai
- Errors gracefully handle hongi
- Task not found ya invalid input ka clear message diya jayega

## 5. Stateless Guarantee
- Har request independent hogi
- Conversation history database se fetch hogi
- Server memory mein koi session/state store nahi hoga
```

## Response snapshot

Constitution successfully updated from v2.0.0 to v3.0.0 (MAJOR version bump).

**Key Changes:**
- Added Phase III specifications for AI-powered Todo Chatbot
- Integrated MCP (Model Context Protocol) architecture
- Defined OpenAI Agents SDK as the AI framework
- Specified OpenAI ChatKit for conversational frontend
- Established stateless architecture requirements for AI layer
- Added behavioral rules for friendly AI interactions
- Defined MCP tools as exclusive interface between AI and data operations

**Phase III Core Principles:**
1. Server MUST remain stateless (no in-memory conversation state)
2. AI logic exclusively through OpenAI Agents SDK
3. Task operations ONLY through MCP tools
4. Conversation state persisted in database
5. AI never directly accesses database

**Technology Stack Added:**
- AI Framework: OpenAI Agents SDK
- MCP Integration: Official MCP SDK
- Frontend: OpenAI ChatKit
- Backend: FastAPI (continued, stateless)
- Database: Neon Serverless PostgreSQL (continued)

**Governance Updates:**
- Moved Phase III from "explicitly excluded" to "current phase"
- Added Phase III-specific quality requirements
- Added Phase III-specific risk management (stateful AI, direct DB access)
- Updated phase boundaries and technology constraints

**Files Modified:**
- `.specify/memory/constitution.md` - Complete rewrite with Phase III specifications

**Sync Impact:**
- Templates flagged for review (plan, spec, tasks) for Phase III AI/MCP considerations
- Follow-up TODOs: Review templates for AI-specific guidance, MCP tool workflow, conversational AI testing

## Outcome

- ✅ Impact: Constitution updated to v3.0.0, Phase III governance established
- 🧪 Tests: N/A (documentation update)
- 📁 Files: 1 file modified (.specify/memory/constitution.md)
- 🔁 Next prompts: Review and update templates for Phase III, create Phase III specification
- 🧠 Reflection: Major version bump justified by introduction of AI capabilities previously excluded. Stateless architecture principle maintained across all phases. MCP tool pattern ensures clean separation between AI and data layers.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual review - PASS (all placeholders filled, version incremented correctly, governance rules consistent)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Create Phase III feature specification following updated constitution
