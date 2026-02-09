<!--
  Sync Impact Report
  ==================
  Version Change: 2.0.0 → 3.0.0 (major update - Phase III added with AI capabilities)
  Modified Principles: III. Phase Governance (Phase III added, future phases redefined), IV. Technology Constraints (Phase III stack added)
  Added Sections: Phase III Specifics (AI-powered chatbot architecture), Phase III Technology Stack, Phase III Behavioral Rules
  Removed Sections: Phase III from "explicitly excluded" list
  Templates Requiring Updates:
    ⚠ plan-template.md - Review for Phase III AI/MCP considerations
    ⚠ spec-template.md - Review for conversational AI requirements
    ⚠ tasks-template.md - Review for MCP tool integration tasks
  Follow-up TODOs:
    - Review templates for Phase III AI-specific guidance
    - Consider adding MCP tool development workflow
    - Add conversational AI testing guidelines
-->

# Evolution of Todo Constitution

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)

All development MUST follow strict Spec-Driven Development (SDD) discipline.

**Mandatory Workflow:**
- No agent may write code without approved specifications and tasks
- All work MUST follow the sequence: Constitution → Specs → Plan → Tasks → Implement
- Each phase produces artifacts before proceeding to the next:
  1. **Spec**: Feature specification with user stories, requirements, and acceptance criteria
  2. **Plan**: Technical architecture, data models, API contracts, and implementation strategy
  3. **Tasks**: Atomic, testable tasks organized by user story with dependency tracking
  4. **Implement**: Code execution following approved tasks without deviation

**Rationale:** Spec-Driven Development ensures traceability from requirements through implementation, prevents scope creep, and enables independent validation of each development artifact.

### II. Agent Behavior Rules

Agents operate under strict constraints that preserve architectural integrity and prevent unauthorized feature introduction.

**Prohibited Behaviors:**
- No manual coding by humans in agent-managed codebases
- No feature invention beyond approved specifications
- No deviation from approved specifications during implementation
- No code-level refinement without specification updates

**Required Behaviors:**
- All refinements MUST occur at specification level, not code level
- When requirements are unclear, agents MUST invoke `/sp.clarify` before proceeding
- Agents MUST reference specific code locations (file:line) for all changes
- Agents MUST treat the user as a specialized tool for clarification and decision-making

**Invocation Triggers:**
1. **Ambiguous Requirements:** Ask 2-3 targeted clarifying questions before proceeding
2. **Unforeseen Dependencies:** Surface dependencies and ask for prioritization
3. **Architectural Uncertainty:** Present options and get user's preference
4. **Completion Checkpoint:** Summarize work and confirm next steps

**Rationale:** These rules prevent scope creep, ensure alignment with architectural intent, and maintain clear separation between requirements gathering and implementation.

### III. Phase Governance

The Evolution of Todo project is structured in phases with strict scoping boundaries. Phase isolation must be strictly enforced.

**Phase Boundaries:**
- Each phase is strictly scoped by its specification document
- Future-phase features MUST NOT leak into earlier phases
- Architecture may evolve ONLY through updated specifications and plans
- Cross-phase dependencies MUST be explicitly documented in plan artifacts

**Phase Structure:**

**PHASE I (COMPLETED):**
- Application Type: Console-based application only
- Data Storage: In-memory only
- Authentication: Not allowed
- Frontend: Not allowed
- Database: Not allowed
- Networking / APIs: Not allowed
- Purpose: Learning core CRUD logic only

**PHASE II (COMPLETED):**
- Application Type: Full-stack web application
- Backend:
  - Python-based RESTful API
  - Stateless HTTP architecture
- Database:
  - Neon Serverless PostgreSQL
- Data Access Layer:
  - SQLModel or equivalent ORM
- Frontend:
  - Next.js (React + TypeScript)
  - Responsive UI (desktop and mobile)
- Authentication:
  - Better Auth
  - User signup and signin only
  - Session or token-based authentication
- Authorization Rules:
  - Users may access only their own todos
  - No roles or permissions system
- Architecture Scope:
  - Monorepo or separated frontend/backend allowed
  - No microservices

**PHASE III (CURRENT PHASE):**
- Application Type: AI-powered Todo Chatbot
- Purpose: Natural language task management using Model Context Protocol (MCP)
- Backend:
  - FastAPI (Python) - MUST remain stateless
  - OpenAI Agents SDK for AI logic
  - Official MCP SDK for tool integration
- Database:
  - Neon Serverless PostgreSQL (continued from Phase II)
  - Conversation state persisted in database
- Data Access Layer:
  - SQLModel (continued from Phase II)
- Frontend:
  - OpenAI ChatKit for conversational interface
- Authentication:
  - Better Auth (continued from Phase II)
- AI Architecture Constraints:
  - Server MUST be stateless (no session/state in memory)
  - AI logic handled exclusively through OpenAI Agents SDK
  - Task operations ONLY through MCP tools (no direct database access by AI)
  - Conversation history fetched from database per request
  - Each request MUST be independent
- Behavioral Requirements:
  - Friendly confirmation for every user action
  - Graceful error handling with clear messages
  - Clear feedback for "task not found" or invalid input scenarios
- Prohibited:
  - AI directly accessing database
  - Storing conversation state in server memory
  - Stateful session management
  - Direct CRUD operations by AI (must use MCP tools)

**PHASE IV AND FUTURE PHASES (Explicitly Excluded):**
- Multi-agent systems
- Background workers
- Event-driven systems
- Real-time collaboration
- Cloud orchestration beyond basic deployment
- Advanced security models (RBAC, ABAC)
- Analytics or monitoring dashboards
- Third-party integrations beyond MCP

**Governance Rules:**
- Work in a phase MUST NOT anticipate or implement features from future phases
- Architecture decisions for future phases MUST NOT influence current phase design
- When phase transitions occur, update constitution and specifications explicitly
- Technologies allowed in later phases must not appear early
- Authentication is permitted starting Phase II only
- Web frontend is permitted starting Phase II only
- Neon PostgreSQL is permitted starting Phase II only
- AI and MCP are permitted starting Phase III only
- Multi-agent systems not permitted before Phase IV

**Rationale:** Strict phase governance prevents premature optimization, keeps each phase deliverable as a standalone product, ensures controlled architectural evolution, and maintains clear boundaries between development phases to prevent scope creep.

### IV. Technology Constraints

Technology choices are defined per phase and MUST be followed without deviation.

**Phase I Technology Stack (COMPLETED):**
- Backend: Python 3.11+
- Framework: Console application only
- Database: In-memory only
- API Style: Not applicable
- Deployment: Not applicable

**Phase II Technology Stack (COMPLETED):**
- Backend: Python 3.11+
- Framework: FastAPI for RESTful API
- Database: Neon Serverless PostgreSQL
- ORM: SQLModel or equivalent
- Frontend: Next.js (React + TypeScript)
- Authentication: Better Auth
- API Style: REST with JSON
- Deployment: Docker containerization

**Phase III Technology Stack (CURRENT):**
- Backend: Python 3.11+
- Framework: FastAPI (stateless architecture)
- AI Framework: OpenAI Agents SDK
- MCP Integration: Official MCP SDK
- Database: Neon Serverless PostgreSQL
- ORM: SQLModel
- Frontend: OpenAI ChatKit
- Authentication: Better Auth (continued from Phase II)
- API Style: REST with JSON + MCP tool protocol
- Deployment: Docker containerization
- Conversation Management: Database-persisted state

**Prohibited Technologies:**
- No alternative frameworks outside defined stack
- No proprietary or vendor-locked solutions without ADR
- No deprecated or unsupported technology versions
- No technologies from future phases (multi-agent, event-driven, etc.)
- No stateful session management in Phase III
- No direct database access by AI components

**Rationale:** Defined technology stack reduces complexity, enables team expertise depth, and ensures consistency across development phases.

### V. Quality Principles

Code and architecture MUST adhere to clean architecture and cloud-native principles.

**Clean Architecture Requirements:**
- Domain logic MUST be separated from infrastructure concerns
- Business rules MUST not depend on external frameworks
- Use dependency injection to invert control flow
- Maintain clear separation of concerns across layers

**Stateless Services:**
- HTTP services MUST be stateless
- State MUST be persisted in databases or external stores
- Session state MUST be stored client-side or in dedicated stores
- Enable horizontal scaling through statelessness
- **Phase III Specific:** Conversation state MUST be database-persisted, never in-memory

**Separation of Concerns:**
- Models MUST represent data without business logic
- Services MUST contain business logic without framework dependencies
- Controllers/API layers MUST handle transport concerns only
- Each module MUST have a single, well-defined responsibility
- **Phase III Specific:** AI logic MUST be isolated in OpenAI Agents SDK layer
- **Phase III Specific:** MCP tools MUST be the only interface between AI and data operations

**Cloud-Native Readiness:**
- Services MUST be containerizable (12-factor app principles)
- Configuration MUST be externalized (environment variables, config services)
- Logging MUST be structured and standardized
- Health checks MUST be exposed for orchestration
- Graceful shutdowns MUST be handled

**Code Quality Standards:**
- Type safety enforced (mypy or equivalent)
- Linting and formatting consistent across codebase
- Documentation inline for non-obvious logic
- Tests accompany production code

**Authentication and Authorization:**
- User authentication implemented with Better Auth
- Users may access only their own todos
- No roles or permissions system (enforced at API level)
- Session or token-based authentication only

**Phase III AI-Specific Quality Requirements:**
- AI responses MUST include friendly confirmations for user actions
- Error handling MUST be graceful with clear, user-friendly messages
- Invalid input or "task not found" scenarios MUST provide helpful feedback
- Conversation context MUST be loaded from database for each request
- No conversation state stored in server memory

**Rationale:** These principles ensure maintainability, testability, and operational readiness across all phases of the project while enforcing security through proper authorization and maintaining stateless architecture for AI components.

## Technology Stack

### By Phase

**Phase I - Console Foundation (COMPLETED):**
- Language: Python 3.11+
- Backend: Console application only
- Database: In-memory only
- Testing: pytest
- Container: Not applicable

**Phase II - Full-Stack Web Application (COMPLETED):**
- Language: Python 3.11+ (Backend), JavaScript/TypeScript (Frontend)
- Backend: FastAPI for RESTful API
- Database: Neon Serverless PostgreSQL
- ORM: SQLModel or equivalent
- Frontend: Next.js (React + TypeScript)
- Authentication: Better Auth
- Testing: pytest (Backend), Jest/Cypress (Frontend)
- Container: Docker
- Deployment: Containerized deployment

**Phase III - AI-Powered Todo Chatbot (CURRENT):**
- Language: Python 3.11+ (Backend)
- Backend: FastAPI (stateless architecture)
- AI Framework: OpenAI Agents SDK
- MCP Integration: Official MCP SDK
- Database: Neon Serverless PostgreSQL
- ORM: SQLModel
- Frontend: OpenAI ChatKit
- Authentication: Better Auth
- Testing: pytest (Backend), MCP tool testing, AI conversation testing
- Container: Docker
- Deployment: Containerized deployment
- Architecture: Stateless server with database-persisted conversation state

### Constraints

- Technology stack choices MUST be documented in phase specifications
- No technology additions without ADR approval
- Versioning managed through dependency management tools
- Security patches applied within defined SLA
- Strict adherence to phase-specific technology boundaries
- **Phase III Specific:** MCP tools MUST be the exclusive interface for AI-to-data operations
- **Phase III Specific:** OpenAI Agents SDK MUST handle all AI logic

## Development Workflow

### Spec-Driven Development Cycle

1. **Constitution:** Review constitution for guidance and constraints
2. **Specification:** Create feature spec with user stories, requirements, acceptance criteria
3. **Planning:** Generate technical plan with architecture, data models, contracts
4. **Tasks:** Create atomic, dependency-ordered tasks organized by user story
5. **Implementation:** Execute tasks following approved specification without deviation
6. **Validation:** Verify against acceptance criteria before proceeding

### Artifact Flow

```
User Input
    ↓
.specify/memory/constitution.md (governs all)
    ↓
/specs/<feature>/spec.md (user stories, requirements)
    ↓
/specs/<feature>/plan.md (architecture, contracts, research)
    ↓
/specs/<feature>/tasks.md (atomic implementation tasks)
    ↓
Code Implementation (executes tasks verbatim)
```

### Quality Gates

- **Spec Review:** User stories are independent and testable
- **Plan Review:** Architecture decisions justified in ADRs
- **Tasks Review:** Each task is atomic and references specific files
- **Implementation Review:** Code matches tasks, no deviation
- **Validation Review:** Acceptance criteria met before merging

### Branch Strategy

- Feature branches: `###-feature-name` format
- Work in branch tied to specific spec
- PRs reference spec and tasks documents
- ADRs linked in PRs for significant decisions

## Governance

### Constitution Authority

This constitution is the supreme governing document for all agents and development activities. Constitution overrides specs, plans, tasks, and implementations.

**Precedence:**
- Constitution overrides conflicting practices in any other document
- All specifications, plans, and tasks MUST align with constitution
- Agents MUST validate compliance before proceeding with work

### Amendment Process

**Constitution Amendments:**
- Amendments require documentation of need and impact analysis
- Amendments must be approved by project owner
- Amendment version MUST increment (MAJOR.MINOR.PATCH semantic versioning)
- Existing work MUST be reviewed for compliance with new constitution

**Versioning Policy:**
- **MAJOR:** Backward-incompatible governance or principle removal/redefinition
- **MINOR:** New principle or section added, material expansion of guidance
- **PATCH:** Clarifications, wording improvements, typo fixes

### Compliance Review

**Pre-Work Check:**
- All agents MUST verify constitution compliance before starting work
- Plan template includes "Constitution Check" section requiring explicit validation
- Non-compliance MUST be documented with justification in plan complexity tracking

**Ongoing Compliance:**
- Code reviews MUST verify constitution adherence
- Violations MUST be escalated to project owner
- Systematic violations trigger constitution review

### Architectural Decision Records (ADR)

**ADR Trigger Test:**
A decision requires an ADR when ALL of these are true:
- **Impact:** Long-term consequences (framework, data model, API, security, platform)
- **Alternatives:** Multiple viable options considered
- **Scope:** Cross-cutting and influences system design

**ADR Process:**
- Detect architecturally significant decision during `/sp.plan` or `/sp.tasks`
- Suggest ADR creation: "📋 Architectural decision detected: <brief> — Document reasoning and tradeoffs? Run `/sp.adr <decision-title>`"
- Wait for user consent (NEVER auto-create ADRs)
- Create ADR with rationale, alternatives, tradeoffs
- Link ADR in plan and PRs

**ADR Content:**
- Context and problem statement
- Decision drivers and constraints
- Considered alternatives with pros/cons
- Chosen decision with rationale
- Consequences (positive and negative)

### Prompt History Records (PHR)

**Creation Requirement:**
PHRs MUST be created for all non-trivial interactions:
- Implementation work (code changes, new features)
- Planning/architecture discussions
- Debugging sessions
- Spec/task/plan creation
- Multi-step workflows

**Routing:**
- Constitution → `history/prompts/constitution/`
- Feature-specific → `history/prompts/<feature-name>/`
- General → `history/prompts/general/`

**Content:**
- Full user input (verbatim, not truncated)
- Assistant output (concise but representative)
- Context: files modified, tests run, outcomes
- Links to related specs, tasks, ADRs, PRs

### Risk Management

**Top Project Risks:**
1. **Phase Leakage:** Future features appearing in current phase
   - Mitigation: Strict scope validation in specs and plans
   - Kill switch: Review any cross-phase dependency

2. **Technology Drift:** Deviation from approved stack
   - Mitigation: Constitution compliance checks
   - Kill switch: ADR required for any tech stack change

3. **Scope Creep:** Feature expansion during implementation
   - Mitigation: Specification freeze before tasks phase
   - Kill switch: Revert any non-approved code

4. **Phase Isolation Violation:** Using future-phase technologies early
   - Mitigation: Strict phase governance enforcement
   - Kill switch: Block any non-phase-appropriate technology

5. **Phase III Specific - Stateful AI:** AI storing state in memory instead of database
   - Mitigation: Architecture reviews enforcing stateless design
   - Kill switch: Reject any in-memory conversation state

6. **Phase III Specific - Direct Database Access:** AI bypassing MCP tools
   - Mitigation: Code reviews verifying MCP tool usage
   - Kill switch: Reject any direct database calls from AI layer

**Blast Radius Control:**
- Each user story is independently deployable
- Each phase produces a working product
- Rollback paths documented in plans
- Feature flags for risky changes

---

**Version**: 3.0.0 | **Ratified**: 2025-12-31 | **Last Amended**: 2026-02-05
