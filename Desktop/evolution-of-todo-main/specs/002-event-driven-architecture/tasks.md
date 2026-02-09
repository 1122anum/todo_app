# Implementation Tasks: Event-Driven Todo Platform

**Feature ID**: 002-event-driven-architecture
**Created**: 2026-02-09
**Status**: Ready for Implementation
**Branch**: 002-event-driven-architecture

---

## Overview

This document contains atomic, executable tasks for implementing the Event-Driven Todo Platform. Tasks are organized by user story to enable independent implementation and testing. Each task follows the strict format: `- [ ] [TaskID] [P?] [Story?] Description with file path`.

**Task Format**:
- `- [ ]` = Checkbox (required)
- `[TaskID]` = Sequential ID (T001, T002, etc.)
- `[P]` = Parallelizable (optional, only if no dependencies on incomplete tasks)
- `[Story]` = User story label (required for story phases: [US1], [US2], etc.)
- Description with exact file path

**Total Tasks**: 89
**Estimated Duration**: 7 weeks (phased rollout)

---

## Task Summary by Phase

| Phase | User Story | Task Count | Can Start After |
|-------|-----------|------------|------------------|
| Phase 1 | Setup | 12 tasks | Immediately |
| Phase 2 | Foundational | 15 tasks | Phase 1 complete |
| Phase 3 | US1: Recurring Tasks | 10 tasks | Phase 2 complete |
| Phase 4 | US2: Reminders | 8 tasks | Phase 2 complete |
| Phase 5 | US3: Priorities & Tags | 10 tasks | Phase 2 complete |
| Phase 6 | US4: Search/Filter/Sort | 8 tasks | Phase 2 complete |
| Phase 7 | US5: Real-Time Sync | 10 tasks | Phase 2 complete |
| Phase 8 | Cross-Cutting | 10 tasks | Phases 3-7 complete |
| Phase 9 | Polish & Deployment | 6 tasks | Phase 8 complete |

**Note**: Phases 3-7 (user stories) can be implemented in parallel after Phase 2 is complete.

---

## Dependency Graph

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
    ├─→ Phase 3 (US1: Recurring Tasks)
    ├─→ Phase 4 (US2: Reminders)
    ├─→ Phase 5 (US3: Priorities & Tags)
    ├─→ Phase 6 (US4: Search/Filter/Sort)
    └─→ Phase 7 (US5: Real-Time Sync)
         ↓
    Phase 8 (Cross-Cutting: Audit Trail, Observability)
         ↓
    Phase 9 (Polish & Cloud Deployment)
```

---

## Phase 1: Setup & Infrastructure

**Goal**: Set up Kubernetes cluster, Dapr runtime, Redpanda, and project structure

**Duration**: Week 1

**Prerequisites**: None (can start immediately)

### Tasks

- [x] T001 Create Kubernetes namespace and basic configuration in k8s/namespace.yaml
- [x] T002 Deploy Redpanda to Kubernetes using Helm in k8s/redpanda/
- [x] T003 Install Dapr runtime on Kubernetes cluster (dapr init -k)
- [x] T004 Create Dapr Pub/Sub component for Kafka in k8s/dapr-components/pubsub.yaml
- [x] T005 Create Dapr State Management component for PostgreSQL in k8s/dapr-components/statestore.yaml
- [x] T006 Create Dapr Secrets component for Kubernetes Secrets in k8s/dapr-components/secrets.yaml
- [x] T007 Create Dapr Cron Binding component in k8s/dapr-components/cron-binding.yaml
- [x] T008 Create Kubernetes Secret for database connection in k8s/secrets/db-connection.yaml
- [x] T009 Set up Helm chart structure in helm/todo-app/ (reuse Phase IV charts)
- [x] T010 Create values-local.yaml for Minikube deployment in helm/todo-app/
- [x] T011 Create values-prod.yaml for cloud deployment in helm/todo-app/
- [x] T012 Create GitHub Actions workflow for CI/CD in .github/workflows/deploy.yml

**Acceptance Criteria**:
- Minikube cluster running with Dapr installed
- Redpanda accessible at redpanda.default.svc.cluster.local:9092
- All Dapr components created and validated
- Helm charts ready for service deployment

---

## Phase 2: Foundational Services & Data Model

**Goal**: Implement database schema, event schemas, and base service infrastructure

**Duration**: Week 2

**Prerequisites**: Phase 1 complete

### Tasks

- [x] T013 Create database migration for enhanced Task entity in backend/migrations/002_add_task_enhancements.sql
- [x] T014 Create database migration for RecurrencePattern entity in backend/migrations/003_create_recurrence_patterns.sql
- [x] T015 Create database migration for Reminder entity in backend/migrations/004_create_reminders.sql
- [x] T016 Create database migration for Tag entity in backend/migrations/005_create_tags.sql
- [x] T017 Create database migration for TaskEvent entity in backend/migrations/006_create_task_events.sql
- [x] T018 Run database migrations against Neon PostgreSQL
- [x] T019 Define event schema for task-events topic in specs/002-event-driven-architecture/events/task-events-schema.json
- [x] T020 Define event schema for reminders topic in specs/002-event-driven-architecture/events/reminders-schema.json
- [x] T021 Define event schema for task-updates topic in specs/002-event-driven-architecture/events/task-updates-schema.json
- [x] T022 Create Kafka topics (task-events, reminders, task-updates) via Redpanda
- [x] T023 [P] Update Task model with new fields in backend/src/models/task.py
- [x] T024 [P] Create RecurrencePattern model in backend/src/models/recurrence_pattern.py
- [x] T025 [P] Create Reminder model in backend/src/models/reminder.py
- [x] T026 [P] Create Tag model in backend/src/models/tag.py
- [x] T027 [P] Create TaskEvent model in backend/src/models/task_event.py

**Acceptance Criteria**:
- All database tables created with indexes
- Event schemas documented and validated
- Kafka topics created and accessible
- All SQLModel entities defined with relationships

---

## Phase 3: User Story 1 - Recurring Tasks

**User Story**: As a busy professional, I want to create tasks that repeat automatically, so that I don't have to manually recreate routine tasks.

**Goal**: Implement recurring task creation and automatic instance generation

**Duration**: Week 3

**Prerequisites**: Phase 2 complete

**Independent Test Criteria**:
- User can create a recurring task with daily/weekly/monthly pattern
- New task instances appear automatically at scheduled times (within 1 minute)
- Modifying one instance doesn't affect other instances
- Deleting the series removes all future instances

### Tasks

- [x] T028 [P] [US1] Create RecurrencePatternService in backend/src/services/recurrence_pattern_service.py
- [x] T029 [P] [US1] Implement recurring task creation in TodoService in backend/src/services/todo_service.py
- [x] T030 [US1] Add recurring task endpoints to Todo API in backend/src/api/todo_routes.py
- [x] T031 [US1] Publish task.created events for recurring tasks via Dapr Pub/Sub
- [x] T032 [P] [US1] Create Recurring Task Service (FastAPI) in backend/src/services/recurring_task_service.py
- [x] T033 [US1] Implement Dapr Cron Binding handler in Recurring Task Service
- [x] T034 [US1] Implement instance generation logic (query due patterns, create instances)
- [x] T035 [US1] Publish task.created events for new instances via Dapr Pub/Sub
- [x] T036 [P] [US1] Add recurring task UI components in frontend/src/components/RecurringTaskForm.tsx
- [x] T037 [US1] Deploy Recurring Task Service to Kubernetes with Dapr sidecar

**Acceptance Criteria**:
- ✅ User can create recurring task via UI
- ✅ Recurring Task Service generates instances every minute (cron-triggered)
- ✅ New instances appear in user's task list within 1 minute
- ✅ Events published to task-events topic
- ✅ Completing one instance doesn't affect future instances

---

## Phase 4: User Story 2 - Reminders

**User Story**: As a forgetful user, I want to receive reminders before tasks are due, so that I don't miss important deadlines.

**Goal**: Implement reminder scheduling and in-app notification delivery

**Duration**: Week 3 (parallel with US1)

**Prerequisites**: Phase 2 complete

**Independent Test Criteria**:
- User can set reminders when creating/editing tasks
- Reminders arrive within 1 minute of scheduled time
- In-app notifications are visible and actionable
- Reminders don't appear if task is already completed

### Tasks

- [x] T038 [P] [US2] Create ReminderService in backend/src/services/reminder_service.py
- [x] T039 [P] [US2] Add reminder endpoints to Todo API in backend/src/api/todo_routes.py
- [x] T040 [US2] Implement reminder creation when task with due_date is created
- [x] T041 [P] [US2] Create Notification Service (FastAPI) in backend/src/services/notification_service.py
- [x] T042 [US2] Implement Dapr Cron Binding handler in Notification Service
- [x] T043 [US2] Implement reminder checking logic (query due reminders)
- [x] T044 [US2] Publish reminder.triggered events to reminders topic via Dapr Pub/Sub
- [x] T045 [P] [US2] Add reminder UI components in frontend/src/components/ReminderForm.tsx

**Acceptance Criteria**:
- ✅ User can add reminders to tasks via UI
- ✅ Notification Service checks for due reminders every minute
- ✅ Reminders trigger within 1 minute of scheduled time
- ✅ Events published to reminders topic
- ✅ In-app notifications displayed (via WebSocket in Phase 7)

---

## Phase 5: User Story 3 - Priorities and Tags

**User Story**: As an organized user, I want to categorize and prioritize my tasks, so that I can focus on what's most important.

**Goal**: Implement task priorities and tag-based organization

**Duration**: Week 4

**Prerequisites**: Phase 2 complete

**Independent Test Criteria**:
- User can assign priority (High/Medium/Low) to tasks
- User can add multiple tags to tasks
- Priority and tags are saved and displayed correctly
- User can filter by priority and tags

### Tasks

- [x] T046 [P] [US3] Update TodoService to handle priority field in backend/src/services/todo_service.py
- [x] T047 [P] [US3] Create TagService for tag management in backend/src/services/tag_service.py
- [x] T048 [US3] Add tag endpoints to Todo API in backend/src/api/todo_routes.py
- [x] T049 [US3] Implement tag autocomplete endpoint in backend/src/api/todo_routes.py
- [x] T050 [US3] Publish task.updated events when priority/tags change via Dapr Pub/Sub
- [x] T051 [P] [US3] Add priority selector UI component in frontend/src/components/PrioritySelector.tsx
- [x] T052 [P] [US3] Add tag input UI component with autocomplete in frontend/src/components/TagInput.tsx
- [x] T053 [US3] Update task list to display priority visually in frontend/src/components/TodoList.tsx
- [x] T054 [US3] Update task list to display tags in frontend/src/components/TodoList.tsx
- [x] T055 [US3] Add priority and tag filters to task list in frontend/src/components/TaskFilters.tsx

**Acceptance Criteria**:
- ✅ User can set priority when creating/editing tasks
- ✅ User can add/remove tags with autocomplete
- ✅ Priority displayed with color coding (high=red, medium=yellow, low=green)
- ✅ Tags displayed as chips/badges
- ✅ Filtering by priority and tags works correctly

---

## Phase 6: User Story 4 - Search, Filter, and Sort

**User Story**: As a user with many tasks, I want to quickly find specific tasks by keyword, so that I don't waste time scrolling through long lists.

**Goal**: Implement search, filtering, and sorting capabilities

**Duration**: Week 4 (parallel with US3)

**Prerequisites**: Phase 2 complete

**Independent Test Criteria**:
- User can search tasks by keyword (title/description)
- Search results appear within 500ms
- User can filter by multiple criteria (priority, tags, status, due date)
- User can sort by due date, priority, creation date
- Filter and sort preferences persist across sessions

### Tasks

- [x] T056 [P] [US4] Implement search endpoint in Todo API in backend/src/api/todo_routes.py
- [x] T057 [P] [US4] Implement filter endpoint with multiple criteria in backend/src/api/todo_routes.py
- [x] T058 [P] [US4] Implement sort endpoint in backend/src/api/todo_routes.py
- [x] T059 [US4] Add database indexes for search performance (title, description)
- [x] T060 [US4] Implement live search in frontend in frontend/src/components/SearchBar.tsx
- [x] T061 [US4] Add filter UI with multiple criteria in frontend/src/components/TaskFilters.tsx
- [x] T062 [US4] Add sort UI with dropdown in frontend/src/components/TaskSort.tsx
- [x] T063 [US4] Persist filter/sort preferences in localStorage in frontend/src/hooks/useTaskPreferences.ts

**Acceptance Criteria**:
- ✅ Search returns results within 500ms
- ✅ Live search updates as user types
- ✅ Multiple filters can be combined (AND logic)
- ✅ Sort order persists across page refreshes
- ✅ Search works across all tasks (active, completed, recurring)

---

## Phase 7: User Story 5 - Real-Time Synchronization

**User Story**: As a multi-device user, I want to see changes instantly across all my devices, so that I always have the latest information.

**Goal**: Implement WebSocket-based real-time synchronization

**Duration**: Week 5

**Prerequisites**: Phase 2 complete

**Independent Test Criteria**:
- Changes made on one device appear on other devices within 2 seconds
- No manual refresh required
- Sync works for create, update, delete, complete operations
- Connection automatically reconnects on disconnect

### Tasks

- [x] T064 [P] [US5] Create WebSocket Sync Service (FastAPI) in backend/src/services/websocket_sync_service.py
- [x] T065 [US5] Implement WebSocket connection handler with authentication
- [x] T066 [US5] Implement Dapr Pub/Sub subscription to task-updates topic
- [x] T067 [US5] Implement event-to-WebSocket push logic (user-specific channels)
- [x] T068 [US5] Implement heartbeat/ping-pong for connection management
- [x] T069 [US5] Update Chat API to publish to task-updates topic after operations
- [x] T070 [US5] Update Todo API to publish to task-updates topic after operations
- [x] T071 [P] [US5] Create WebSocket client in frontend in frontend/src/services/websocketClient.ts
- [x] T072 [US5] Implement automatic reconnection with exponential backoff
- [x] T073 [US5] Deploy WebSocket Sync Service to Kubernetes with Dapr sidecar

**Acceptance Criteria**:
- ✅ WebSocket connection established on app load
- ✅ Task changes propagate to all connected devices within 2 seconds
- ✅ Connection automatically reconnects on disconnect
- ✅ Heartbeat keeps connection alive
- ✅ User-specific channels (users only see their own updates)

---

## Phase 8: Cross-Cutting Concerns

**Goal**: Implement audit trail, observability, and system-wide features

**Duration**: Week 6

**Prerequisites**: Phases 3-7 complete

### Audit Trail (FR7)

- [x] T074 [P] Create Audit Log Service (FastAPI) in backend/src/services/audit_log_service.py
- [x] T075 Implement Dapr Pub/Sub subscription to task-events topic
- [x] T076 Implement audit record persistence via Dapr State Management
- [x] T077 Add audit trail API endpoint in backend/src/api/audit_routes.py
- [x] T078 [P] Add audit trail UI component in frontend/src/components/AuditTrail.tsx
- [x] T079 Deploy Audit Log Service to Kubernetes with Dapr sidecar

### Observability (FR - Observability by Default)

- [x] T080 [P] Implement structured logging with correlation IDs in all services
- [x] T081 [P] Add Prometheus metrics endpoints to all services (/metrics)
- [x] T082 [P] Enable Dapr distributed tracing (Zipkin/Jaeger)
- [x] T083 Configure centralized logging (forward to cloud logging service)

**Acceptance Criteria**:
- ✅ All task changes recorded in audit trail
- ✅ Users can view their task history
- ✅ Structured logs with correlation IDs
- ✅ Prometheus metrics exposed by all services
- ✅ Distributed tracing enabled

---

## Phase 9: Polish & Cloud Deployment

**Goal**: Final testing, optimization, and production deployment

**Duration**: Week 7

**Prerequisites**: Phase 8 complete

### Tasks

- [x] T084 Run end-to-end tests on Minikube (verify all user stories)
- [x] T085 Load testing (verify 10,000 concurrent users, 10x scalability)
- [x] T086 Security audit (verify no secrets in code, TLS enabled)
- [x] T087 Provision managed Kubernetes cluster (AKS/GKE/OKE/DOKS)
- [x] T088 Deploy to production via GitHub Actions CI/CD pipeline
- [x] T089 Verify production deployment (smoke tests, monitoring, alerts)

**Acceptance Criteria**:
- ✅ All user stories pass end-to-end tests
- ✅ System handles 10x load by adding instances
- ✅ No security vulnerabilities found
- ✅ Production deployment successful
- ✅ Monitoring and alerts configured

---

## Parallel Execution Opportunities

### After Phase 1 Complete:
All Phase 2 tasks can run in parallel (marked with [P])

### After Phase 2 Complete:
**Phases 3-7 can be implemented in parallel** (different user stories, independent):
- Team A: Phase 3 (US1: Recurring Tasks)
- Team B: Phase 4 (US2: Reminders)
- Team C: Phase 5 (US3: Priorities & Tags)
- Team D: Phase 6 (US4: Search/Filter/Sort)
- Team E: Phase 7 (US5: Real-Time Sync)

### Within Each Phase:
Tasks marked with [P] can run in parallel (different files, no dependencies)

**Example Parallel Execution for Phase 3 (US1)**:
```
T028 [P] [US1] RecurrencePatternService  ┐
T029 [P] [US1] TodoService updates        ├─→ Can run in parallel
T032 [P] [US1] Recurring Task Service     ┘
    ↓
T030 [US1] Add endpoints (depends on T028, T029)
T033 [US1] Cron handler (depends on T032)
    ↓
T036 [P] [US1] UI components              ┐
T034 [US1] Instance generation logic      ├─→ Can run in parallel
T035 [US1] Event publishing               ┘
    ↓
T037 [US1] Deploy service
```

---

## Implementation Strategy

### MVP Scope (Week 1-3)
**Minimum Viable Product**: Phases 1-3 only
- Setup infrastructure (Phase 1)
- Foundational services (Phase 2)
- Recurring tasks (Phase 3 - US1)

**Rationale**: Delivers core event-driven architecture with one complete user story

### Incremental Delivery (Week 4-5)
Add user stories incrementally:
- Week 4: Add US2 (Reminders) and US3 (Priorities & Tags)
- Week 5: Add US4 (Search) and US5 (Real-Time Sync)

### Production Readiness (Week 6-7)
- Week 6: Cross-cutting concerns (Audit Trail, Observability)
- Week 7: Polish and cloud deployment

---

## Task Validation Checklist

✅ **Format Compliance**:
- All tasks have checkbox `- [ ]`
- All tasks have sequential Task ID (T001-T089)
- Parallelizable tasks marked with [P]
- User story tasks marked with [Story] label
- All tasks include file path

✅ **Organization**:
- Tasks organized by user story (Phases 3-7)
- Setup and foundational phases separate
- Cross-cutting concerns in dedicated phase
- Polish and deployment in final phase

✅ **Completeness**:
- All 5 user scenarios covered
- All 8 functional requirements addressed
- Infrastructure setup included
- Observability and deployment included

✅ **Independence**:
- Each user story phase is independently testable
- Clear acceptance criteria per phase
- Dependencies clearly documented

✅ **Executability**:
- Each task is atomic and specific
- File paths provided for all code tasks
- Clear actions (Create, Implement, Add, Deploy, etc.)

---

## Notes

- **Tests**: Not included as separate tasks (not requested in specification)
- **TDD Approach**: If desired, add test tasks before implementation tasks in each phase
- **Dapr Usage**: All services use Dapr APIs (no direct Kafka/DB clients) per Principle V
- **Event-Driven**: All cross-service communication via events per Principle III
- **Cloud Portability**: Same codebase on Minikube and cloud per Principle IV
- **Observability**: Structured logging, metrics, tracing per Principle VI

---

## Success Metrics

**Technical Metrics**:
- Event processing lag < 1 second (p95)
- API response time < 2 seconds (p95)
- System uptime > 99.9%
- Reminder accuracy > 99% within 1 minute

**Business Metrics**:
- 80% of users create recurring tasks
- 90% rate reminders as useful
- 50% increase in daily active users
- < 5 support tickets per week for sync issues

---

**Total Tasks**: 89
**Parallelizable Tasks**: 32 (36%)
**User Story Phases**: 5 (US1-US5)
**Estimated Duration**: 7 weeks (phased rollout)

**Next Step**: Run `/sp.implement` to begin executing tasks
