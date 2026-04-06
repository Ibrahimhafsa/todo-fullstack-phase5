# Feature Specification: Local Event Architecture

**Feature Branch**: `007-local-event-architecture`
**Created**: 2026-03-15
**Status**: Draft
**Input**: Deploy the complete todo-fullstack system locally on Kubernetes with Kafka and Dapr providing the event-driven runtime, extending existing Spec-006 architecture without breaking changes.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deploy Local Kubernetes Cluster (Priority: P1)

**Actor**: DevOps Engineer / Developer
**Goal**: Set up a fully functional Minikube cluster that can run the entire todo application stack locally for development and testing.

As a developer, I need a local Kubernetes environment that mirrors production to test deployments without cloud infrastructure costs, so I can rapidly iterate on infrastructure changes and debug cluster-related issues before pushing to production.

**Why this priority**: This is the foundational requirement. Without a working Minikube cluster, no other infrastructure components can be deployed. It unblocks all subsequent P2-P3 work.

**Independent Test**: Can be fully tested by: starting Minikube, deploying basic services (nginx, PostgreSQL), verifying pods are running and healthy. Delivers: local Kubernetes environment ready for application deployment.

**Acceptance Scenarios**:

1. **Given** Minikube is not running, **When** operator runs `minikube start`, **Then** Minikube cluster is operational and ready to accept deployments
2. **Given** Minikube is running, **When** operator deploys a test pod (e.g., nginx), **Then** pod starts, becomes ready, and is accessible via service DNS
3. **Given** Minikube cluster is operational, **When** operator checks node status, **Then** system shows 1 ready node with correct resource allocation (CPU, memory)

---

### User Story 2 - Deploy Kafka Cluster with Strimzi (Priority: P1)

**Actor**: DevOps Engineer / Developer
**Goal**: Install and configure Kafka cluster inside Kubernetes using Strimzi Operator, ensuring high availability and proper topic creation for event-driven architecture.

As a developer, I need Kafka running inside Kubernetes so the backend can publish events and worker services can consume them, enabling the event-driven architecture defined in Spec-006.

**Why this priority**: Kafka is the message bus for all event communication (task-events, reminders, task-updates topics). Without it, events cannot flow between services. This blocks both the backend event publishing and worker service consumption.

**Independent Test**: Can be fully tested by: installing Strimzi operator, deploying Kafka cluster, creating required topics, publishing a test message, verifying a consumer receives it. Delivers: operational Kafka cluster with 3 topics ready for application event traffic.

**Acceptance Scenarios**:

1. **Given** Strimzi operator is not installed, **When** operator applies Strimzi operator YAML, **Then** operator is running in kafka namespace with CRD support
2. **Given** Strimzi operator is running, **When** operator applies Kafka cluster YAML, **Then** Kafka cluster with 3 brokers becomes available and all brokers report healthy status
3. **Given** Kafka cluster is running, **When** operator creates topics (task-events, reminders, task-updates) via KafkaTopic CRD, **Then** topics exist with correct partition count and replication factor
4. **Given** topics are created, **When** test message is published to task-events topic, **Then** message persists and is consumable by subscribers

---

### User Story 3 - Install Dapr in Kubernetes Mode (Priority: P1)

**Actor**: DevOps Engineer / Developer
**Goal**: Install Dapr control plane and runtime in Kubernetes, enabling Dapr sidecars on application pods for Pub/Sub abstraction over Kafka.

As a developer, I need Dapr running in the cluster so backend and worker services can publish/subscribe to events through Dapr HTTP API instead of direct Kafka clients, providing abstraction and flexibility.

**Why this priority**: Dapr is the abstraction layer between applications and Kafka (Constitution XXVIII requirement). It enables non-blocking event publishing via HTTP and decouples services from Kafka implementation details. Without Dapr, services must use direct Kafka clients (forbidden by constitution).

**Independent Test**: Can be fully tested by: installing Dapr, deploying a test pod with Dapr sidecar, calling Dapr pub/sub HTTP API, verifying message reaches Kafka. Delivers: Dapr control plane + sidecar injection mechanism ready for all application services.

**Acceptance Scenarios**:

1. **Given** Dapr is not installed, **When** operator runs Dapr installation command, **Then** Dapr control plane is running with daprd, placement, sentry services
2. **Given** Dapr is installed, **When** operator creates pod with Dapr annotations (dapr.io/enabled: true), **Then** pod automatically gets Dapr sidecar injected
3. **Given** pod has Dapr sidecar, **When** application calls `POST http://localhost:3500/v1.0/publish/kafka-pubsub/task-events`, **Then** Dapr sidecar forwards message to Kafka

---

### User Story 4 - Configure Dapr Components (Priority: P2)

**Actor**: Platform Engineer / DevOps
**Goal**: Create Kubernetes YAML configuration files defining Dapr components (Pub/Sub for Kafka, State Store for PostgreSQL, Secrets Management for credentials).

As an infrastructure engineer, I need Dapr components configured so services know how to reach Kafka, PostgreSQL, and secrets vault, enabling proper event publishing, state management, and secure credential access.

**Why this priority**: Dapr components are the bridge between abstract Dapr API calls and concrete infrastructure. Without them, Dapr sidecars don't know where Kafka or PostgreSQL are. This is required for P1 scenarios to actually work.

**Independent Test**: Can be fully tested by: creating Dapr component YAML files, applying them to cluster, verifying components status shows "RUNNING". Delivers: Dapr components configured and ready for use by applications.

**Acceptance Scenarios**:

1. **Given** Dapr is installed but components are not configured, **When** operator applies kafka-pubsub component YAML, **Then** component is created and reported as RUNNING in Dapr dashboard
2. **Given** kafka-pubsub component exists, **When** application publishes message via `POST http://localhost:3500/v1.0/publish/kafka-pubsub/topic-name`, **Then** message successfully reaches Kafka topic
3. **Given** postgresql state store component is configured, **When** application saves state via Dapr State API, **Then** state is persisted in PostgreSQL

---

### User Story 5 - Deploy Backend API with Dapr Sidecar (Priority: P2)

**Actor**: Developer / DevOps
**Goal**: Update backend API deployment to include Dapr sidecar annotation, enabling event publishing through Dapr HTTP API instead of direct clients.

As a developer, I need the backend FastAPI service to run with a Dapr sidecar so it can publish events without bundling Kafka client libraries, maintaining clean separation of concerns and enabling easy provider switching.

**Why this priority**: This integrates the backend (from Spec-006) with the new infrastructure (Spec-007). It's P2 because Dapr must be installed first (P1). Once Dapr is ready, deploying backend with sidecar is straightforward configuration change.

**Independent Test**: Can be fully tested by: deploying backend with Dapr sidecar annotation, verifying sidecar is injected, calling backend API to create task, checking Kafka topic for TaskCreated event. Delivers: backend event publishing working end-to-end through Dapr.

**Acceptance Scenarios**:

1. **Given** Dapr is installed and Kafka is running, **When** operator applies backend deployment with dapr.io annotations, **Then** backend pod starts with 2 containers (fastapi + daprd)
2. **Given** backend is running with sidecar, **When** application calls backend POST /api/user123/tasks with task data, **Then** TaskCreated event appears in Kafka task-events topic
3. **Given** event is in Kafka, **When** operator checks event payload, **Then** event includes user_id, task_id, timestamp, version, and complete task data

---

### User Story 6 - Deploy Worker Services (Priority: P2)

**Actor**: Developer / DevOps
**Goal**: Deploy 4 independent worker services (recurring, notification, audit, websocket consumers) to Kubernetes, each consuming from appropriate Kafka topics through Dapr sidecars.

As a developer, I need worker services running so events published by backend are consumed and processed (generating recurring instances, sending notifications, logging audits, broadcasting updates).

**Why this priority**: Workers consume the events published by backend. P1 infrastructure must be ready first. Once P1 is complete, deploying workers is configuration + existing code from Spec-006.

**Independent Test**: Can be fully tested by: deploying all 4 workers, verifying each pod has Dapr sidecar, creating task in backend, verifying consumers process event. Delivers: complete event pipeline from backend through workers operational.

**Acceptance Scenarios**:

1. **Given** backend and Kafka are running, **When** operator applies all 4 worker deployment YAMLs, **Then** 4 worker pods start (recurring, notification, audit, websocket) with Dapr sidecars
2. **Given** workers are running, **When** backend creates a recurring task, **Then** task appears in backend, TaskCreated event appears in Kafka, audit-consumer logs the event
3. **Given** recurring task is completed, **When** backend marks task complete, **Then** TaskCompleted event is published, recurring-consumer generates next instance, next instance appears in backend task list
4. **Given** task has reminder_time, **When** reminder time arrives, **Then** notification-consumer receives ReminderTriggered event and sends in-app notification

---

### User Story 7 - Verify Event Flow End-to-End (Priority: P2)

**Actor**: QA / Developer
**Goal**: Verify complete event pipeline works: backend → Dapr → Kafka → workers, with proper event schema, user isolation, and no message loss.

As a tester, I need to validate that events flow correctly through the entire system so I can be confident in reliability before production deployment.

**Why this priority**: This is verification of the complete system. Depends on all P1-P2 infrastructure being ready. Validates that Spec-006 event logic integrates correctly with Spec-007 infrastructure.

**Independent Test**: Can be fully tested by: creating tasks, completing tasks, scheduling reminders, verifying state changes propagate correctly through all services. Delivers: confidence that event architecture works end-to-end.

**Acceptance Scenarios**:

1. **Given** all services are running, **When** user creates task with priority, tags, due_date, **Then** task appears in database, TaskCreated event is published, audit-consumer logs creation
2. **Given** recurring task is completed, **When** user marks complete, **Then** task marked complete, TaskCompleted event published, next instance generated within 5 minutes, reminder scheduled if applicable
3. **Given** multiple users exist, **When** user1 and user2 perform operations, **Then** events contain correct user_id, workers respect user_id, users never see each other's tasks
4. **Given** event consumer fails, **When** consumer recovers, **Then** consumer resumes from last processed event, does not duplicate work, catches up within reasonable time

---

### Edge Cases

- What happens when Kafka broker is temporarily unavailable? (Event publishing should queue locally and retry, not block API)
- How does system handle consumer lag when events accumulate faster than workers can process? (Workers should scale, consumers should not lose messages)
- What happens when Dapr sidecar crashes? (Kubernetes should restart it, application should reconnect automatically)
- How are secrets (database passwords, service tokens) managed securely in local development? (Kubernetes secrets, not hardcoded in YAML)
- What happens when a worker service dies mid-event-processing? (Idempotency + event deduplication should prevent duplicates; message should be reprocessed)

---

## Requirements *(mandatory)*

### Functional Requirements

**Minikube Cluster**:
- **FR-001**: System MUST provide `minikube start` command to provision local Kubernetes cluster with at least 2 CPU and 4GB RAM
- **FR-002**: System MUST support cluster teardown via `minikube delete` for clean state reset
- **FR-003**: System MUST enable ingress addon for external access to services

**Kafka Deployment**:
- **FR-004**: System MUST install Strimzi Operator in `kafka` namespace to manage Kafka lifecycle
- **FR-005**: System MUST deploy Kafka cluster with 3 brokers for high availability
- **FR-006**: System MUST create 3 Kafka topics: `task-events`, `reminders`, `task-updates` with partition count=3, replication factor=3
- **FR-007**: System MUST persist Kafka data via StatefulSet PersistentVolumeClaims for data durability across restarts

**Dapr Installation**:
- **FR-008**: System MUST install Dapr control plane in `dapr-system` namespace with daprd, placement, sentry services
- **FR-009**: System MUST enable Dapr sidecar injection via admission webhook annotations (dapr.io/enabled: true)
- **FR-010**: System MUST support Dapr tracing and observability components for debugging event flow

**Dapr Components**:
- **FR-011**: System MUST create `kafka-pubsub` component configuring Dapr Pub/Sub to Kafka brokers
- **FR-012**: System MUST create `postgres-statestore` component for application state persistence
- **FR-013**: System MUST create `kubernetes-secrets` component for secure credential management
- **FR-014**: System MUST validate all components are RUNNING and ready to serve requests

**Backend Integration**:
- **FR-015**: Backend deployment MUST include Dapr sidecar annotation (dapr.io/enabled: true)
- **FR-016**: Backend MUST publish events via Dapr HTTP API (`POST http://localhost:3500/v1.0/publish/...`) instead of direct Kafka clients
- **FR-017**: Backend event publishing MUST be asynchronous and non-blocking (events published after DB commit, don't delay API response)
- **FR-018**: Backend MUST include user_id in all events for Constitution VII compliance (task ownership enforcement)

**Worker Services**:
- **FR-019**: System MUST deploy 4 independent worker services: recurring-consumer, notification-consumer, audit-consumer, websocket-consumer
- **FR-020**: Each worker MUST run with Dapr sidecar for Kafka subscriptions
- **FR-021**: Each worker MUST subscribe to appropriate Kafka topic (recurring→task-events, notification→reminders, audit→task-events, websocket→task-updates)
- **FR-022**: Workers MUST implement idempotent processing with event deduplication to handle duplicate deliveries
- **FR-023**: Workers MUST respect user_id in events and enforce ownership (Constitution VII)
- **FR-024**: Workers MUST have configurable replicas for horizontal scaling (recurring: 2, notification: 2, audit: 1 for sequential consistency, websocket: 2)

**Health & Observability**:
- **FR-025**: All services MUST expose `/health` endpoint for Kubernetes liveness/readiness probes
- **FR-026**: System MUST collect logs from all services for debugging event flow
- **FR-027**: System MUST support kubectl logs retrieval for each service and worker
- **FR-028**: System MUST provide monitoring dashboard view of service status and event lag

**Backward Compatibility**:
- **FR-029**: Existing REST API endpoints MUST continue working without modification (no breaking changes)
- **FR-030**: Existing task CRUD operations MUST remain compatible with new event architecture
- **FR-031**: Frontend MUST continue communicating with backend without changes
- **FR-032**: Database MUST maintain existing schema (no forced migrations)

---

### Key Entities

**Kubernetes Resources**:
- **Deployment**: Defines replica count, container image, resource limits, health probes, Dapr annotations
- **Service**: Exposes deployment to other services via DNS
- **StatefulSet**: For Kafka brokers (ordered, stable identity, persistent storage)
- **PersistentVolumeClaim**: Storage for Kafka broker data
- **Namespace**: Isolation boundary (kafka, dapr-system, default)

**Dapr Components**:
- **Pub/Sub Component**: Maps Dapr pub/sub API to Kafka brokers; defines topic names, connection details
- **State Store Component**: Configures where Dapr stores application state (PostgreSQL connection string)
- **Secrets Component**: Manages credential storage and retrieval

**Event Schema**:
- **TaskEvent**: Immutable snapshot of task state at time of event; includes event_type, event_id, timestamp, version, user_id, task_id, data
- **ReminderEvent**: Triggered when reminder time arrives; includes user_id, task_id, task_title, reminder_time

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Minikube cluster starts cleanly within 2 minutes, supports all required addons (ingress, storage, metrics)
- **SC-002**: Kafka cluster with 3 brokers, 3 topics deployed successfully, brokers healthy and accepting connections within 5 minutes of Kafka operator deployment
- **SC-003**: Dapr control plane installed and sidecar injection working on 100% of annotated pods within 3 minutes of installation
- **SC-004**: All 4 Dapr components created and report RUNNING status within 2 minutes of YAML application
- **SC-005**: Backend publishes event to Kafka within 50ms of API request (non-blocking via asyncio.create_task)
- **SC-006**: Event appears in Kafka topic within 100ms of publication (Dapr + Kafka latency SLA)
- **SC-007**: Worker consumer receives and processes event within 5 minutes of publication (consumer lag SLA)
- **SC-008**: Recurring task consumer generates next instance within 5 minutes of parent completion (end-to-end latency)
- **SC-009**: All 4 worker services running with correct number of replicas and Dapr sidecars
- **SC-010**: Health checks pass for all services (liveness + readiness probes succeed)
- **SC-011**: Event deduplication works: if same event published twice, consumer processes it only once
- **SC-012**: User isolation enforced: user1's events never trigger changes for user2's tasks
- **SC-013**: Zero breaking changes to existing REST API; frontend continues working without modification
- **SC-014**: Existing task list endpoint works correctly alongside new event infrastructure
- **SC-015**: Complete end-to-end scenario succeeds: create task → publish event → consume event → generate result (e.g., next recurring instance) within 10 seconds

---

## Assumptions

1. **Minikube Environment**: Assumes developer machine has Docker, sufficient RAM (8GB+), disk space (30GB+) for local Kubernetes cluster
2. **Kafka Operator**: Assumes Strimzi Operator is the chosen approach for Kafka management (not manual broker configuration or other operators)
3. **Dapr Version**: Assumes latest stable Dapr release (v1.x) compatible with Kubernetes 1.21+
4. **PostgreSQL Access**: Assumes PostgreSQL database is accessible from Kubernetes cluster (either via Neon connection string or local PostgreSQL)
5. **Event Schema Stability**: Assumes event schema from Spec-006 is finalized and won't change; new versions would require migration logic
6. **Worker Code Availability**: Assumes worker consumer code from Spec-006 is available and compiles without modification
7. **Namespace Isolation**: Assumes `kafka` and `dapr-system` namespaces are dedicated to these systems (not shared with application services)
8. **Local Development Only**: Assumes this spec is for local development; production deployment would use managed services (AWS MSK, Azure Event Hubs, cloud-native Dapr)
9. **Image Availability**: Assumes Docker images (todo-backend:latest, todo-frontend:latest) are available locally or in accessible registry

---

## Dependencies & Constraints

**Dependencies**:
- Spec-006 must be complete (event schemas, worker services, task service modifications all in place)
- Docker must be installed and running
- kubectl CLI must be installed and in PATH
- Helm optional but recommended for package management

**Constraints**:
- Local Kubernetes cluster (Minikube) has resource limits (CPU, RAM) vs production
- Single machine means services are not distributed across nodes (different failure profile than production)
- Kafka persistence uses local storage (not HA-NFS) so data loss if Minikube deleted
- Network simpler (no firewall rules, VPC configuration vs cloud deployments)
- No managed load balancer (Minikube uses NodePort/ClusterIP)

---

## Out of Scope

- **Production Deployment**: This spec is local development only. Production uses cloud-native Kafka (AWS MSK, Confluent Cloud) or managed alternatives
- **Advanced Dapr Features**: Dapr's service invocation, bindings, actors not covered (only Pub/Sub required)
- **Monitoring/Alerting**: Prometheus, Grafana, alerting rules covered elsewhere
- **Secrets Management**: Detailed vault setup, secret rotation policies not covered (assumes Kubernetes secrets sufficient for dev)
- **Network Policies**: Ingress rules, pod-to-pod communication policies not detailed
- **Helm Charts**: While mentioned, detailed Helm configuration not in this spec
- **CI/CD Integration**: GitHub Actions, automated deployments not in scope
- **Load Testing**: Performance testing infrastructure not included
- **Disaster Recovery**: Backup/restore procedures for Kafka data not covered

