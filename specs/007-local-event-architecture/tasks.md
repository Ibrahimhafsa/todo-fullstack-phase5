# Tasks: Spec-007 Local Event Architecture

**Input**: Implementation plan from `/specs/007-local-event-architecture/plan.md` and spec from `spec.md`
**Dependencies**: Spec-006 (advanced-features) with event publishing code already complete

**Organization**: Tasks are grouped by infrastructure component phases to enable sequential local Kubernetes deployment of event architecture.

**Test Tasks**: OPTIONAL – not included per user request ("Do not generate code yet")

---

## Format: `[ID] [P?] [Story?] Description`

- **[ID]**: Sequential task ID (T001, T002, etc.) in execution order
- **[P]**: Parallelizable (different files, no blocking dependencies on incomplete tasks)
- **[Story]**: User story label if applicable (e.g., [US1], [US2]); for infrastructure tasks, no story label
- Include exact file paths in descriptions

---

## Phase 1: Setup - Infrastructure Foundation

**Purpose**: Initialize Kubernetes and container environment for local event architecture

**Dependencies**: None - foundation tasks

---

### Phase 1.1: Minikube Cluster Initialization

- [ ] T001 Install Minikube CLI tool and dependencies on local machine
- [ ] T002 Create `k8s/minikube/setup.sh` script to initialize Minikube cluster with 4 CPU, 8GB RAM
- [ ] T003 Create `k8s/minikube/teardown.sh` script to clean up and delete Minikube cluster
- [ ] T004 Create `k8s/minikube/README.md` with setup instructions and prerequisites
- [ ] T005 [P] Execute Minikube setup to provision local Kubernetes cluster
- [ ] T006 Create `k8s/scripts/verify-minikube.sh` to validate cluster health (node status, DNS, test pod deployment)
- [ ] T007 Run verification script and confirm single node Ready with correct resource allocation

**Checkpoint**: Minikube cluster running, single node Ready, Kubernetes API accessible

---

### Phase 1.2: Docker Images and Registry Setup

- [ ] T008 [P] Verify `todo-backend:latest` Docker image available locally or in accessible registry
- [ ] T009 [P] Verify `todo-frontend:latest` Docker image available locally or in accessible registry
- [ ] T010 Configure Minikube Docker environment (set docker.sock path for image access)

**Checkpoint**: Docker images accessible to Minikube cluster

---

## Phase 2: Foundational - Kafka Cluster Deployment

**Purpose**: Deploy Kafka infrastructure via Strimzi Operator (blocking prerequisite for all downstream services)

**⚠️ CRITICAL**: Kafka cluster must be operational before backend or workers can start. No event publishing possible without Kafka.

---

### Phase 2.1: Strimzi Operator Installation

- [ ] T011 Create `k8s/kafka/namespace.yaml` with kafka namespace definition
- [ ] T012 Create `k8s/kafka/strimzi-operator/operator.yaml` with Strimzi operator installation manifests (CRDs, operator deployment, RBAC)
- [ ] T013 Create `k8s/kafka/README.md` with Kafka deployment guide and Strimzi documentation links
- [ ] T014 Apply kafka namespace YAML: `kubectl apply -f k8s/kafka/namespace.yaml`
- [ ] T015 Apply Strimzi operator YAML: `kubectl apply -f k8s/kafka/strimzi-operator/operator.yaml`
- [ ] T016 Create `k8s/scripts/verify-kafka-operator.sh` to check Strimzi operator deployment status
- [ ] T017 Run verification script and confirm strimzi-cluster-operator pod Running in kafka namespace

**Checkpoint**: Strimzi operator deployed, Kafka CRD available

---

### Phase 2.2: Kafka Cluster and Topic Creation

- [ ] T018 Create `k8s/kafka/kafka-cluster.yaml` with Kafka cluster definition (3 brokers, ephemeral storage, Zookeeper replicas=1)
- [ ] T019 Create `k8s/kafka/kafka-topics.yaml` with 3 KafkaTopic CRDs:
  - task-events (3 partitions, replication factor 3)
  - reminders (3 partitions, replication factor 3)
  - task-updates (3 partitions, replication factor 3)
- [ ] T020 Apply Kafka cluster YAML: `kubectl apply -f k8s/kafka/kafka-cluster.yaml`
- [ ] T021 Apply KafkaTopic CRDs YAML: `kubectl apply -f k8s/kafka/kafka-topics.yaml`
- [ ] T022 Create `k8s/scripts/verify-kafka.sh` to check Kafka brokers health and topic creation
- [ ] T023 Run verification script and confirm:
  - 3 Kafka brokers Ready
  - 3 topics created with correct partitions and replication factor
  - Kafka bootstrap service accessible at kafka-cluster-kafka-bootstrap.kafka:9092

**Checkpoint**: Kafka cluster operational with 3 topics ready for event publishing

---

## Phase 3: Foundational - Dapr Control Plane Installation

**Purpose**: Deploy Dapr infrastructure for sidecar injection and Pub/Sub abstraction (blocking for backend and workers)

**Note**: Can run in parallel with Phase 2 (Kafka deployment) - both depend only on Phase 1 (Minikube)

---

### Phase 3.1: Dapr System Namespace and Installation

- [ ] T024 Create `k8s/dapr/dapr-system-namespace.yaml` with dapr-system namespace and labels for sidecar injection
- [ ] T025 Create `k8s/dapr/dapr-install.sh` script with Dapr installation command (helm or kubectl)
- [ ] T026 Create `k8s/dapr/rbac/dapr-rbac.yaml` with ServiceAccount, ClusterRole, and ClusterRoleBinding for Dapr
- [ ] T027 Create `k8s/dapr/README.md` with Dapr installation guide and sidecar injection explanation
- [ ] T028 Apply dapr-system namespace YAML: `kubectl apply -f k8s/dapr/dapr-system-namespace.yaml`
- [ ] T029 Execute Dapr installation script (installs Dapr control plane via Helm): `bash k8s/dapr/dapr-install.sh`
- [ ] T030 Apply RBAC YAML: `kubectl apply -f k8s/dapr/rbac/dapr-rbac.yaml`
- [ ] T031 Create `k8s/scripts/verify-dapr.sh` to check Dapr control plane services and sidecar injection webhook
- [ ] T032 Run verification script and confirm:
  - dapr-operator, dapr-sentry, dapr-placement pods Running in dapr-system
  - MutatingWebhookConfiguration for dapr-sidecar-injector exists

**Checkpoint**: Dapr control plane deployed, sidecar injection webhook active

---

### Phase 3.2: Test Dapr Sidecar Injection

- [ ] T033 Deploy test pod with `dapr.io/enabled: "true"` annotation to verify sidecar injection
- [ ] T034 Verify test pod has 2 containers (main app + daprd sidecar)
- [ ] T035 Delete test pod after verification

**Checkpoint**: Dapr sidecar injection confirmed working

---

## Phase 4: Foundational - Dapr Components Configuration

**Purpose**: Configure Dapr building blocks (Pub/Sub, State Store, Secrets) to connect applications to Kafka and PostgreSQL

**⚠️ CRITICAL**: All Dapr components must be RUNNING before backend or workers can communicate with Kafka or PostgreSQL

---

### Phase 4.1: Kafka Pub/Sub Component

- [ ] T036 Create `k8s/dapr/components/kafka-pubsub.yaml` with Dapr Pub/Sub component for Kafka:
  - Type: pubsub.kafka
  - Brokers: kafka-cluster-kafka-bootstrap.kafka:9092
  - Version: 3.3.0
  - Auth: none (local development)
- [ ] T037 Apply kafka-pubsub component: `kubectl apply -f k8s/dapr/components/kafka-pubsub.yaml`

**Checkpoint**: kafka-pubsub component RUNNING

---

### Phase 4.2: PostgreSQL State Store Component

- [ ] T038 Create Kubernetes Secret for PostgreSQL connection credentials: `kubectl create secret generic postgres-credentials --from-literal=connection-string="postgresql://..."`
- [ ] T039 Create `k8s/dapr/components/postgres-statestore.yaml` with Dapr State Store component for PostgreSQL:
  - Type: state.postgresql
  - Connection string from environment variable or secret reference
- [ ] T040 Apply postgres-statestore component: `kubectl apply -f k8s/dapr/components/postgres-statestore.yaml`

**Checkpoint**: postgres-statestore component RUNNING

---

### Phase 4.3: Kubernetes Secrets Component

- [ ] T041 Create `k8s/dapr/components/kubernetes-secrets.yaml` with Dapr Secrets component for Kubernetes:
  - Type: secretstores.kubernetes
  - Namespace: default
- [ ] T042 Apply kubernetes-secrets component: `kubectl apply -f k8s/dapr/components/kubernetes-secrets.yaml`

**Checkpoint**: kubernetes-secrets component RUNNING

---

### Phase 4.4: Verify All Dapr Components

- [ ] T043 Create `k8s/scripts/verify-dapr-components.sh` to check all 3 Dapr components RUNNING
- [ ] T044 Run verification script and confirm:
  - kafka-pubsub component RUNNING
  - postgres-statestore component RUNNING
  - kubernetes-secrets component RUNNING

**Checkpoint**: All Dapr components configured and operational - backend and workers can now communicate with Kafka and PostgreSQL via Dapr

---

## Phase 5: Core Infrastructure - Backend API Deployment with Dapr Sidecar

**Purpose**: Deploy backend FastAPI service with Dapr sidecar for event publishing via Dapr HTTP API

**Note**: Depends on Phase 2 (Kafka) and Phase 4 (Dapr components)

---

### Phase 5.1: Backend Deployment Modification

- [ ] T045 Update existing `k8s/backend/backend-deployment.yaml` to add Dapr sidecar annotations:
  - `dapr.io/enabled: "true"`
  - `dapr.io/app-id: "backend"`
  - `dapr.io/app-port: "8000"`
  - NO code changes to FastAPI container (event publishing code from Spec-006 unchanged)
- [ ] T046 Ensure backend environment variables set correctly (LOG_LEVEL, DATABASE_URL, BETTER_AUTH_SECRET)
- [ ] T047 Review backend deployment for any hardcoded Kafka client references and confirm none exist (must use Dapr HTTP API only)

**Checkpoint**: Backend deployment YAML updated with sidecar annotations

---

### Phase 5.2: Deploy Backend to Kubernetes

- [ ] T048 Apply backend deployment: `kubectl apply -f k8s/backend/backend-deployment.yaml`
- [ ] T049 Create `k8s/scripts/verify-backend.sh` to validate backend deployment:
  - Backend pod running with 2 containers (fastapi + daprd sidecar)
  - Service accessible
  - Sidecar logs show successful startup
- [ ] T050 Run verification script and confirm backend pod Ready with 2 containers
- [ ] T051 Port-forward backend service: `kubectl port-forward svc/backend 8000:8000`
- [ ] T052 Test backend API health: `curl http://localhost:8000/health`

**Checkpoint**: Backend API running with Dapr sidecar, API accessible

---

### Phase 5.3: Test Event Publishing from Backend

- [ ] T053 Create task via backend API: `curl -X POST http://localhost:8000/api/user123/tasks -H "Authorization: Bearer <token>" -d '{"title":"test"}'`
- [ ] T054 Create `k8s/scripts/verify-event-publishing.sh` to check TaskCreated event in Kafka topic:
  - Connect to Kafka broker: `kubectl run kafka-test --image=confluentinc/cp-kafka:7.5.0 -it`
  - List messages in task-events topic
  - Verify event payload contains: event_type, event_id, timestamp, version, user_id, task_id, data
- [ ] T055 Run verification script and confirm TaskCreated event in Kafka task-events topic within 100ms of API call

**Checkpoint**: Backend event publishing working end-to-end through Dapr to Kafka

---

## Phase 6: Core Infrastructure - Worker Services Deployment with Dapr Sidecars

**Purpose**: Deploy 4 independent worker services to consume and process events from Kafka

**Note**: Depends on Phase 2 (Kafka), Phase 4 (Dapr components), and Phase 5 (Dapr sidecar injection verified)

---

### Phase 6.1: Recurring Task Consumer Worker

- [ ] T056 Update existing `k8s/workers/recurring-consumer-deployment.yaml` to add Dapr sidecar annotations:
  - `dapr.io/enabled: "true"`
  - `dapr.io/app-id: "recurring-consumer"`
  - `dapr.io/app-port: "8001"`
  - Replicas: 2 (HA and parallelism)
  - NO code changes to recurring consumer (from Spec-006)
- [ ] T057 Apply recurring consumer deployment: `kubectl apply -f k8s/workers/recurring-consumer-deployment.yaml`

**Checkpoint**: Recurring consumer deployed with 2 replicas

---

### Phase 6.2: Notification Consumer Worker

- [ ] T058 Update existing `k8s/workers/notification-consumer-deployment.yaml` to add Dapr sidecar annotations:
  - `dapr.io/enabled: "true"`
  - `dapr.io/app-id: "notification-consumer"`
  - `dapr.io/app-port: "8002"`
  - Replicas: 2 (HA and parallelism)
  - NO code changes to notification consumer (from Spec-006)
- [ ] T059 Apply notification consumer deployment: `kubectl apply -f k8s/workers/notification-consumer-deployment.yaml`

**Checkpoint**: Notification consumer deployed with 2 replicas

---

### Phase 6.3: Audit Consumer Worker

- [ ] T060 Update existing `k8s/workers/audit-consumer-deployment.yaml` to add Dapr sidecar annotations:
  - `dapr.io/enabled: "true"`
  - `dapr.io/app-id: "audit-consumer"`
  - `dapr.io/app-port: "8003"`
  - Replicas: 1 (sequential consistency for audit logs)
  - Strategy: Recreate (no parallel updates)
  - NO code changes to audit consumer (from Spec-006)
- [ ] T061 Apply audit consumer deployment: `kubectl apply -f k8s/workers/audit-consumer-deployment.yaml`

**Checkpoint**: Audit consumer deployed with 1 replica

---

### Phase 6.4: WebSocket Consumer Worker

- [ ] T062 Update existing `k8s/workers/websocket-consumer-deployment.yaml` to add Dapr sidecar annotations:
  - `dapr.io/enabled: "true"`
  - `dapr.io/app-id: "websocket-consumer"`
  - `dapr.io/app-port: "8004"`
  - Replicas: 2 (HA)
  - Higher resources: 512Mi RAM request, 1Gi limit
  - NO code changes to websocket consumer (from Spec-006)
- [ ] T063 Apply websocket consumer deployment: `kubectl apply -f k8s/workers/websocket-consumer-deployment.yaml`

**Checkpoint**: WebSocket consumer deployed with 2 replicas

---

### Phase 6.5: Verify All Workers Deployed

- [ ] T064 Create `k8s/scripts/verify-workers.sh` to validate all 4 worker deployments:
  - Check all 4 deployments exist
  - Check 5 total pods running (2+2+1+2 = 7, but audit has 1, websocket has 2... total 7 replicas, but user story wants 5 total so audit=1, others=2 each = 2+2+1+2=7, let me recalculate: recurring=2, notification=2, audit=1, websocket=2, total=7)
  - Actually from plan: recurring 2, notification 2, audit 1, websocket 2 = 7 pods total
  - Verify each pod has 2 containers (app + daprd sidecar)
  - Check sidecar subscriptions active
- [ ] T065 Run verification script and confirm all 4 deployments Ready with correct pod count and sidecars

**Checkpoint**: All 4 worker services deployed and running with Dapr sidecars

---

## Phase 7: Validation - End-to-End Event Flow

**Purpose**: Verify complete event pipeline from backend through Kafka to workers

**Dependencies**: All Phases 1-6 complete

---

### Phase 7.1: Single User Event Flow Test

- [ ] T066 Create `k8s/scripts/test-single-user-flow.sh` to test basic event flow:
  - Create task via backend API with specific user_id
  - Wait up to 5 seconds
  - Verify TaskCreated event in Kafka task-events topic
  - Verify task appears in backend task list
  - Verify audit-consumer logs the creation event
- [ ] T067 Run single user flow test and confirm all events propagated correctly

**Checkpoint**: Basic event flow working

---

### Phase 7.2: Recurring Task Completion Test

- [ ] T068 Create `k8s/scripts/test-recurring-task.sh` to test recurring task logic:
  - Create recurring task (Daily pattern) via backend API
  - Mark task complete
  - Wait up to 5 minutes
  - Verify TaskCompleted event in Kafka
  - Verify next instance generated by recurring-consumer
  - Verify next instance appears in backend task list with due date +1 day
- [ ] T069 Run recurring task test and confirm next instance generated within 5 minutes

**Checkpoint**: Recurring task generation working

---

### Phase 7.3: Multi-User Isolation Test

- [ ] T070 Create `k8s/scripts/test-user-isolation.sh` to test user isolation:
  - Create task as user1
  - Create task as user2 simultaneously
  - Verify each user only sees their own tasks
  - Verify events contain correct user_id
  - Verify workers respect user_id (no cross-user operations)
- [ ] T071 Run user isolation test and confirm users cannot see each other's tasks/events

**Checkpoint**: User isolation enforced

---

### Phase 7.4: Event Deduplication Test

- [ ] T072 Create `k8s/scripts/test-event-deduplication.sh` to test idempotent processing:
  - Publish same event twice with same event_id
  - Wait for worker processing
  - Verify worker processed event only once (no duplicate result)
  - Verify event deduplication mechanism working
- [ ] T073 Run deduplication test and confirm duplicate events processed only once

**Checkpoint**: Event deduplication working

---

### Phase 7.5: Complete Integration Test

- [ ] T074 Create `k8s/scripts/test-complete-integration.sh` combining all scenarios:
  - Single user task creation
  - Recurring task completion
  - Multi-user simultaneous operations
  - Event deduplication
  - Consumer lag monitoring
- [ ] T075 Create `k8s/test-scenarios/integration-test-data.yaml` with sample test data
- [ ] T076 Run complete integration test and verify all scenarios pass within SLA targets:
  - Event publish latency: < 50ms
  - Event in Kafka: < 100ms
  - Worker processing: < 5 minutes
  - End-to-end scenario: < 10 seconds

**Checkpoint**: Complete event architecture verified and operational

---

## Phase 8: Documentation and Cleanup

**Purpose**: Final documentation and optional cleanup tasks

---

### Phase 8.1: Documentation

- [ ] T077 Create comprehensive `k8s/DEPLOYMENT.md` with:
  - Step-by-step setup guide
  - Verification commands per phase
  - Troubleshooting guide for common issues
  - Architecture diagram (ASCII or linked)
  - Event flow diagram
  - Minikube resource requirements
- [ ] T078 Update `k8s/README.md` with links to all component guides
- [ ] T079 Create `k8s/ARCHITECTURE.md` explaining Dapr abstraction and event flow
- [ ] T080 Create `k8s/SCALING.md` documenting how to scale to different environments (production)

### Phase 8.2: Cleanup and Reset (Optional)

- [ ] T081 Create `k8s/scripts/cleanup-all.sh` to remove all event infrastructure while preserving backend
- [ ] T082 Create `k8s/scripts/reset-minikube.sh` to fully reset Minikube cluster to clean state
- [ ] T083 Document cluster reset and re-deployment procedures

**Checkpoint**: Documentation complete, infrastructure tested and validated

---

## Dependencies & Execution Order

### Critical Path (Sequential - must follow this order):

```
Phase 1 (Minikube)
    ↓
Phase 2 (Kafka Cluster)
    ↓
Phase 3 (Dapr Control Plane) [can run parallel with Phase 2 after Phase 1 complete]
    ↓
Phase 4 (Dapr Components)
    ↓
Phase 5 (Backend)
    ↓
Phase 6 (Workers)
    ↓
Phase 7 (Validation)
    ↓
Phase 8 (Documentation)
```

### Parallel Opportunities:

- **Phase 1**: Tasks T001-T010 all independent and parallelizable (setup)
- **Phase 2 & 3**: Can run in parallel after Phase 1 complete
  - Phase 2.1 (Strimzi operator): T011-T017
  - Phase 3.1 (Dapr installation): T024-T032 (can run in parallel with Phase 2.1)
  - Phase 2.2 & 3.2 depend on their respective Phase 1 tasks
- **Phase 4**: All three component tasks (T036-T044) can run in parallel
- **Phase 5, 6, 7**: Sequential within each phase; phases must complete in order
- **Phase 8**: Independent documentation tasks

### Recommended Staffing:

- **1 person**: Execute sequentially, ~85 minutes total
- **2 people**: Person A handles Phase 2 (Kafka), Person B handles Phase 3 (Dapr) in parallel
  - Then both work on Phase 4-8 sequentially
  - Total time: ~50 minutes

### Phase Checkpoints (Must Pass Before Proceeding):

| Phase | Checkpoint | Must Pass Before |
|-------|-----------|-----------------|
| 1 | Minikube cluster running | Phase 2-3 |
| 2 | Kafka with 3 topics operational | Phase 4 |
| 3 | Dapr control plane running | Phase 4 |
| 4 | All Dapr components RUNNING | Phase 5-6 |
| 5 | Backend API with sidecar, events in Kafka | Phase 7 |
| 6 | All 4 workers deployed with sidecars | Phase 7 |
| 7 | End-to-end event flow verified | Phase 8 |
| 8 | Documentation complete | Production |

---

## Task Summary

**Total Tasks**: 83 tasks across 8 phases
**Task Breakdown by Phase**:
- Phase 1 (Setup): 10 tasks
- Phase 2 (Kafka): 13 tasks
- Phase 3 (Dapr): 10 tasks
- Phase 4 (Components): 9 tasks
- Phase 5 (Backend): 8 tasks
- Phase 6 (Workers): 9 tasks
- Phase 7 (Validation): 10 tasks
- Phase 8 (Documentation): 4 tasks

**Estimated Duration**:
- Sequential: 85 minutes (1.5 hours)
- With parallelization (2 people): 50 minutes
- With full team: 30 minutes

**MVP Scope** (Phases 1-5 only):
- Minikube cluster running
- Kafka operational with 3 topics
- Dapr control plane and components configured
- Backend publishing events through Dapr to Kafka
- ~40 minutes for MVP (Phases 1-5 only)

**Next: Full Validation** (Phases 6-8):
- Deploy worker services
- Complete end-to-end testing
- Documentation and cleanup

---

## Ready for Implementation

All 83 tasks are specific, actionable, and organized by dependency. Each task has:
- ✅ Clear objective
- ✅ Expected output/success criteria
- ✅ File paths to create/modify
- ✅ Dependencies documented
- ✅ Verification steps where applicable

**Next Step**: Execute Phase 1 tasks to initialize Kubernetes infrastructure
