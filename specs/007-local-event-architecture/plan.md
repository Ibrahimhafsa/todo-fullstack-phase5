# Implementation Plan: Local Event Architecture

**Branch**: `007-local-event-architecture` | **Date**: 2026-03-15 | **Spec**: [Spec-007](spec.md)
**Input**: Feature specification from `/specs/007-local-event-architecture/spec.md`

---

## Summary

**Primary Requirement**: Deploy complete todo-fullstack system locally on Kubernetes with Kafka and Dapr providing event-driven runtime, extending Spec-006 architecture without breaking changes.

**Technical Approach**:
- Minikube provides local Kubernetes cluster foundation
- Strimzi Operator manages Kafka lifecycle (3 brokers, 3 topics)
- Dapr control plane enables sidecar injection and Pub/Sub abstraction
- Dapr components configure concrete integrations (Kafka, PostgreSQL, Secrets)
- Backend and workers updated with sidecar annotations for automatic injection
- Event flow: Backend → Dapr HTTP API → Kafka Topics → Worker Consumers

**Key Constraint**: All infrastructure changes must preserve existing REST API and backend code (zero breaking changes).

---

## Technical Context

**Target Platform**: Linux/Kubernetes (local Minikube cluster)
**Orchestration**: Minikube + kubectl
**Message Bus**: Apache Kafka 3.x via Strimzi Operator
**Service Mesh**: Dapr v1.x (sidecar injection mode)
**Container Registry**: Docker (local images)
**Primary Dependencies**:
- Minikube (local Kubernetes)
- Strimzi Operator (Kafka lifecycle management)
- Dapr control plane (sidecar injection, Pub/Sub abstraction)
- Helm (optional, for package management)
- kubectl (Kubernetes CLI)

**Storage**: PostgreSQL (Neon, already in use from Spec-006)
**Testing**: kubectl commands, Dapr CLI, Kafka CLI for verification
**Constraints**:
- Local machine resource limits (8GB+ RAM, 30GB+ disk)
- Single Minikube node (not distributed)
- Local Kafka storage (not HA persistence)
- Development environment only (not production-grade)

**Performance Goals**:
- Minikube startup: < 2 minutes
- Kafka cluster deployment: < 5 minutes
- Dapr installation: < 3 minutes
- Event publish latency: < 50ms (non-blocking)
- Event consumption latency: < 5 minutes
- System scaling: 2 replicas for concurrent services, 1 for audit (sequential)

---

## Constitution Check

**GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.**

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **VII** (Task Ownership) | All queries filter by user_id; 404 for non-owned resources | ✅ PASS | Worker services enforce user_id in events; existing backend unchanged |
| **XXVI** (Event-Driven) | All mutations emit events asynchronously | ✅ PASS | Events published via Dapr HTTP API post-DB-commit; non-blocking via asyncio |
| **XXVII** (Kafka Bus) | 3 topics (task-events, reminders, task-updates) deployed | ✅ PASS | Spec requires task-events, reminders, task-updates topics; KafkaTopic CRD per topic |
| **XXVIII** (Dapr Abstraction) | NO direct Kafka clients in code; must use Dapr HTTP API | ✅ PASS | Backend publishes via `POST http://localhost:3500/v1.0/publish/...`; workers consume via Dapr sidecar |
| **XXX** (Message Versioning) | Event schema includes version field; enables evolution | ✅ PASS | TaskEvent schema from Spec-006 includes "version" field; events immutable snapshots |
| **XXXV** (Backward Compatibility) | Zero breaking changes to REST API; existing clients work | ✅ PASS | No API endpoint modifications; existing task CRUD unchanged; workers additive |

**Gate Result**: ✅ **PASS** – All Constitution principles satisfied. No violations requiring justification.

---

## Project Structure

### Documentation (this feature)

```text
specs/007-local-event-architecture/
├── spec.md              # Feature specification (COMPLETE - 296 lines)
├── plan.md              # This file (implementation plan - 8 phases)
├── research.md          # Phase 0 output (to be created)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── checklists/
│   └── requirements.md  # Quality validation (COMPLETE - 24/24 PASS)
└── contracts/           # Phase 1 output (to be created)
    ├── kubernetes.md    # K8s resource contracts
    ├── dapr.md         # Dapr component contracts
    └── helm.md         # Helm value contracts
```

### Source Code - Kubernetes Infrastructure (to be created)

```text
k8s/
├── minikube/
│   ├── setup.sh                   # Minikube initialization script
│   ├── teardown.sh                # Minikube cleanup script
│   └── README.md                  # Setup instructions
│
├── kafka/
│   ├── namespace.yaml             # kafka namespace
│   ├── strimzi-operator/          # Strimzi Operator YAML
│   │   └── operator.yaml          # Strimzi CRD installation
│   ├── kafka-cluster.yaml         # Kafka broker cluster (3 brokers)
│   ├── kafka-topics.yaml          # KafkaTopic CRDs (3 topics)
│   └── README.md                  # Kafka deployment guide
│
├── dapr/
│   ├── dapr-system-namespace.yaml # dapr-system namespace
│   ├── dapr-install.sh            # Dapr installation script
│   ├── components/                # Dapr component definitions
│   │   ├── kafka-pubsub.yaml      # Pub/Sub component (Kafka broker addresses)
│   │   ├── postgres-statestore.yaml  # State Store (PostgreSQL connection)
│   │   └── kubernetes-secrets.yaml   # Secrets component
│   ├── rbac/                      # RBAC for Dapr
│   │   └── dapr-rbac.yaml         # Service account + role bindings
│   └── README.md                  # Dapr installation guide
│
├── backend/
│   ├── backend-deployment.yaml    # Updated with Dapr sidecar annotations
│   ├── backend-service.yaml       # Service definition (no changes)
│   └── README.md                  # Deployment verification guide
│
├── workers/
│   ├── recurring-consumer-deployment.yaml    # From Spec-006 (Dapr sidecar added)
│   ├── notification-consumer-deployment.yaml # From Spec-006
│   ├── audit-consumer-deployment.yaml        # From Spec-006
│   ├── websocket-consumer-deployment.yaml    # From Spec-006
│   └── README.md                             # Worker deployment guide
│
├── helm/
│   ├── values.yaml                # Helm values (minikube profile)
│   ├── values-dev.yaml            # Development overrides
│   └── README.md                  # Helm deployment guide (optional)
│
└── scripts/
    ├── verify-minikube.sh         # Verify Minikube cluster ready
    ├── verify-kafka.sh            # Verify Kafka brokers + topics
    ├── verify-dapr.sh             # Verify Dapr installation + components
    ├── verify-backend.sh          # Verify backend running with sidecar
    ├── verify-workers.sh          # Verify all 4 workers deployed
    ├── verify-event-flow.sh       # End-to-end event flow test
    └── test-integration.sh        # Full integration test suite
```

---

## Implementation Phases

### Phase 0: Research & Decision Documentation

**Purpose**: Resolve all unknowns and document architectural decisions.

**Key Questions to Research**:
1. Minikube resource requirements and best practices for local K8s development
2. Strimzi Operator latest stable version and installation process
3. Dapr sidecar injection modes (admission webhook vs manual)
4. Kafka topic configuration (partition count, replication factor) for development
5. Dapr component versioning and backward compatibility
6. Minikube persistence volumes vs. local storage options
7. Best practices for testing Kafka/Dapr locally (testcontainers alternative?)

**Research Output** (`specs/007-local-event-architecture/research.md`):
- Decision: [what was chosen]
- Rationale: [why chosen]
- Alternatives considered: [what else evaluated]

**Deliverables**:
- ✅ research.md (2-3 pages)

**Gate**: All unknowns resolved before Phase 1

---

### Phase 1: Design & Infrastructure Contracts

**Purpose**: Design Kubernetes manifests, Dapr components, and system contracts.

#### 1.1 Data Model (if applicable)

**No new data models required** - Spec-007 is infrastructure-only; all data models exist in Spec-006.

**Kubernetes Resources** (new):
- Namespace: `kafka`
- Namespace: `dapr-system`
- ConfigMap: Dapr component configs
- Secrets: PostgreSQL credentials, Kafka credentials
- ServiceAccount: Dapr components
- Role/RoleBinding: Dapr RBAC

#### 1.2 API Contracts

**Dapr HTTP API** (abstraction layer, not REST):

**Backend → Dapr Pub/Sub**:
```
POST http://localhost:3500/v1.0/publish/{pubsub-name}/{topic}
Content-Type: application/json

{
  "event_type": "TaskCreated",
  "event_id": "uuid",
  "timestamp": "ISO-8601",
  "version": "1.0",
  "user_id": "user123",
  "task_id": 42,
  "data": { task object }
}
```

**Worker ← Dapr Pub/Sub** (sidecar subscription):
```
GET http://localhost:3500/v1.0/subscribe/{pubsub-name}
(sidecar calls worker endpoint: POST /events/{topic})

Worker endpoint receives:
{
  "topic": "task-events",
  "event": { event payload }
}
```

#### 1.3 Kubernetes Resource Contracts

**Minikube Cluster**:
- Single-node cluster
- Default StorageClass
- Ingress addon enabled
- Metrics addon enabled (optional)

**Kafka StatefulSet**:
```yaml
Kind: Kafka
metadata:
  name: kafka-cluster
  namespace: kafka
spec:
  kafka:
    replicas: 3
    config:
      log.retention.hours: 24
      auto.create.topics.enable: "false"
  storage:
    type: ephemeral  # or persistent for data durability
  zookeeper:
    replicas: 1
```

**KafkaTopic CRDs** (3 topics):
```yaml
Kind: KafkaTopic
metadata:
  name: task-events
spec:
  partitions: 3
  replication:
    factor: 3
---
# reminders topic
---
# task-updates topic
```

**Dapr Component** (kafka-pubsub):
```yaml
Kind: Component
metadata:
  name: kafka-pubsub
  namespace: dapr-system
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "kafka-cluster-kafka-bootstrap.kafka:9092"
  - name: version
    value: "3.3.0"
```

**Backend Deployment** (with sidecar annotation):
```yaml
kind: Deployment
metadata:
  name: backend
spec:
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "backend"
        dapr.io/app-port: "8000"
    spec:
      containers:
      - name: fastapi
        image: todo-backend:latest
        ports:
        - containerPort: 8000
        # NO Dapr client library needed - sidecar injected automatically
```

#### 1.4 Quickstart Guide

**File**: `specs/007-local-event-architecture/quickstart.md`

**Contents**:
1. **Prerequisites**: Docker, kubectl, Helm (optional)
2. **Step 1**: `minikube start --cpus 4 --memory 8192`
3. **Step 2**: Strimzi Operator installation (helm or kubectl)
4. **Step 3**: Kafka cluster deployment and topic creation
5. **Step 4**: Dapr installation (`dapr init -k`)
6. **Step 5**: Dapr components configuration (apply YAML files)
7. **Step 6**: Backend deployment with sidecar annotation
8. **Step 7**: Worker deployments (4 consumers)
9. **Step 8**: Verification script (`verify-event-flow.sh`)

**Deliverables**:
- ✅ data-model.md (minimal, infrastructure-only)
- ✅ quickstart.md (step-by-step setup)
- ✅ contracts/ directory with YAML schema contracts

---

### Phase 2: Critical Path Implementation

**Purpose**: Implement infrastructure in dependency order (P1 → P2).

#### Phase 2.1: Minikube Cluster Setup

**Objective**: Local Kubernetes cluster operational.

**Tasks**:
1. Create `k8s/minikube/setup.sh` - Minikube initialization
   - Start with 4 CPU, 8GB RAM, enable ingress addon
   - Verify cluster health (1 node ready)

2. Create `k8s/scripts/verify-minikube.sh` - Cluster verification
   - Check node status
   - Verify DNS resolution
   - Test basic pod deployment

**Kubernetes Resources**:
- None (Minikube provides default resources)

**Files to Create**:
- k8s/minikube/setup.sh
- k8s/minikube/teardown.sh
- k8s/scripts/verify-minikube.sh

**Verification**:
- Minikube status shows "Running"
- `kubectl get nodes` shows 1 Ready node
- `kubectl run nginx --image=nginx && kubectl wait --for=condition=Ready pod/nginx` succeeds

**Dependencies**: None
**Blockers**: None (depends on Minikube installed locally)

---

#### Phase 2.2: Strimzi Operator Installation

**Objective**: Kafka operator running, ready for cluster deployment.

**Tasks**:
1. Create `k8s/kafka/strimzi-operator/operator.yaml` - Strimzi CRDs + operator deployment
   - Install Strimzi custom resource definitions (Kafka, KafkaTopic, KafkaUser, etc.)
   - Deploy strimzi-cluster-operator in `kafka` namespace

2. Create `k8s/kafka/namespace.yaml` - Kafka namespace
   - Namespace: `kafka`

**Kubernetes Resources**:
- Namespace: kafka
- CustomResourceDefinition: Kafka
- CustomResourceDefinition: KafkaTopic
- Deployment: strimzi-cluster-operator

**Files to Create**:
- k8s/kafka/namespace.yaml
- k8s/kafka/strimzi-operator/operator.yaml
- k8s/kafka/README.md

**Verification**:
- `kubectl get ns kafka` shows kafka namespace
- `kubectl get deployment -n kafka` shows strimzi-cluster-operator RUNNING
- `kubectl api-resources | grep kafka` shows Kafka and KafkaTopic CRDs

**Dependencies**: Phase 2.1 (Minikube cluster)
**Blockers**: None

---

#### Phase 2.3: Kafka Cluster Deployment

**Objective**: Kafka cluster with 3 brokers, 3 topics running and healthy.

**Tasks**:
1. Create `k8s/kafka/kafka-cluster.yaml` - Kafka cluster via Strimzi
   - 3 broker replicas
   - Ephemeral storage (for dev; can use persistent)
   - Single Zookeeper replica (dev environment)

2. Create `k8s/kafka/kafka-topics.yaml` - KafkaTopic CRDs (3 topics)
   - task-events: 3 partitions, replication factor 3
   - reminders: 3 partitions, replication factor 3
   - task-updates: 3 partitions, replication factor 3

3. Create `k8s/scripts/verify-kafka.sh` - Kafka verification
   - Check broker status
   - Verify topic creation
   - Test publish/consume

**Kubernetes Resources**:
- Kafka: kafka-cluster (3 brokers)
- KafkaTopic: task-events
- KafkaTopic: reminders
- KafkaTopic: task-updates
- PersistentVolumeClaim: kafka-storage (if persistent)

**Files to Create**:
- k8s/kafka/kafka-cluster.yaml
- k8s/kafka/kafka-topics.yaml
- k8s/scripts/verify-kafka.sh

**Verification**:
- `kubectl get kafka -n kafka` shows kafka-cluster Ready
- `kubectl get kafkatopic -n kafka` shows 3 topics Ready
- Kafka broker pods (3) running and ready
- Topic creation timestamp recent
- Test message: `kubectl run -it --image=confluentinc/cp-kafka:7.5.0 -- kafka-console-producer.sh --broker-list kafka-cluster-kafka-bootstrap.kafka:9092 --topic task-events`

**Dependencies**: Phase 2.2 (Strimzi operator)
**Blockers**: None

---

#### Phase 2.4: Dapr Control Plane Installation

**Objective**: Dapr running in Kubernetes with sidecar injection enabled.

**Tasks**:
1. Create `k8s/dapr/dapr-install.sh` - Dapr installation script
   - Add Dapr Helm repo
   - Install Dapr in Kubernetes mode with sidecar injection
   - Enable namespace annotation for sidecar injection

2. Create `k8s/dapr/dapr-system-namespace.yaml` - Dapr system namespace
   - Namespace: dapr-system
   - Labels for sidecar injection

3. Create `k8s/dapr/rbac/dapr-rbac.yaml` - RBAC for Dapr
   - ServiceAccount for Dapr
   - ClusterRoleBinding for sidecar injection

4. Create `k8s/scripts/verify-dapr.sh` - Dapr verification
   - Check control plane services (daprd, placement, sentry)
   - Verify sidecar injection webhook
   - Test with sample pod

**Kubernetes Resources**:
- Namespace: dapr-system
- Deployment: dapr-operator
- Deployment: dapr-placement
- Deployment: dapr-sentry
- MutatingWebhookConfiguration: dapr-sidecar-injector
- ServiceAccount: dapr-operator, dapr-sentry
- ClusterRole/ClusterRoleBinding: Dapr RBAC

**Files to Create**:
- k8s/dapr/dapr-system-namespace.yaml
- k8s/dapr/dapr-install.sh
- k8s/dapr/rbac/dapr-rbac.yaml
- k8s/scripts/verify-dapr.sh

**Verification**:
- `kubectl get pods -n dapr-system` shows 3+ Dapr services Ready
- `kubectl get mwc` shows dapr-sidecar-injector
- `dapr status -k` shows all Dapr services running
- Test pod injection: create pod with `dapr.io/enabled: "true"`, verify sidecar injected

**Dependencies**: Phase 2.1 (Minikube) – Dapr installation independent of Kafka
**Blockers**: None

---

#### Phase 2.5: Dapr Components Configuration

**Objective**: Dapr components created and reporting RUNNING status.

**Tasks**:
1. Create `k8s/dapr/components/kafka-pubsub.yaml` - Kafka Pub/Sub component
   - Type: pubsub.kafka
   - Brokers: kafka-cluster-kafka-bootstrap.kafka:9092
   - Consumer group: backend/workers

2. Create `k8s/dapr/components/postgres-statestore.yaml` - PostgreSQL State Store
   - Type: state.postgresql
   - Connection string from environment variable

3. Create `k8s/dapr/components/kubernetes-secrets.yaml` - Secrets component
   - Type: secretstores.kubernetes
   - Namespace: default

4. Create `k8s/scripts/verify-dapr-components.sh` - Components verification
   - List all components
   - Check status of each component
   - Verify connectivity to Kafka brokers

**Kubernetes Resources**:
- Component: kafka-pubsub
- Component: postgres-statestore
- Component: kubernetes-secrets

**Files to Create**:
- k8s/dapr/components/kafka-pubsub.yaml
- k8s/dapr/components/postgres-statestore.yaml
- k8s/dapr/components/kubernetes-secrets.yaml

**Verification**:
- `kubectl get components -n default` shows 3 components
- `dapr component status` shows all components RUNNING
- `dapr invoke {component} -- method` test connectivity

**Dependencies**: Phase 2.3 (Kafka cluster) + Phase 2.4 (Dapr control plane)
**Blockers**: Kafka brokers must be accessible; PostgreSQL connection string must be valid

---

#### Phase 2.6: Backend Deployment with Dapr Sidecar

**Objective**: Backend API running with Dapr sidecar, event publishing working through Dapr HTTP API.

**Tasks**:
1. Modify `k8s/backend/backend-deployment.yaml` - Add Dapr sidecar annotations
   - Keep existing backend code unchanged (zero breaking changes)
   - Add annotations: dapr.io/enabled: "true", dapr.io/app-id: "backend", dapr.io/app-port: "8000"
   - Ensure environment variables reference Dapr sidecar port (3500)

2. Create `k8s/scripts/verify-backend.sh` - Backend verification
   - Check backend pod running with 2 containers (fastapi + daprd sidecar)
   - Call backend POST /api/user123/tasks to create task
   - Verify TaskCreated event in Kafka task-events topic
   - Check event payload structure

**Kubernetes Resources**:
- Deployment: backend (modified with sidecar annotations)
- Service: backend (no changes)

**Files to Create/Modify**:
- k8s/backend/backend-deployment.yaml (modified)
- k8s/scripts/verify-backend.sh

**Verification**:
- `kubectl get pods | grep backend` shows backend pod with 2 containers
- `kubectl logs -c daprd <backend-pod>` shows sidecar logs (subscriptions ready)
- `curl http://backend:8000/docs` accessible from test pod
- Create task via API: TaskCreated event appears in Kafka within 100ms
- Event JSON includes user_id, task_id, timestamp, version

**Dependencies**: Phase 2.5 (Dapr components)
**Blockers**: Dapr sidecar injection must work; event publishing code from Spec-006 must be functional

---

#### Phase 2.7: Worker Services Deployment

**Objective**: 4 worker services deployed, consuming from appropriate Kafka topics.

**Tasks**:
1. Modify `k8s/workers/recurring-consumer-deployment.yaml` - Add Dapr sidecar annotations
   - Keep worker code unchanged
   - Add sidecar annotations: dapr.io/enabled: "true", dapr.io/app-id: "recurring-consumer"
   - Verify subscription to task-events topic

2. Modify `k8s/workers/notification-consumer-deployment.yaml` - Add sidecar annotations

3. Modify `k8s/workers/audit-consumer-deployment.yaml` - Add sidecar annotations

4. Modify `k8s/workers/websocket-consumer-deployment.yaml` - Add sidecar annotations

5. Create `k8s/scripts/verify-workers.sh` - Workers verification
   - Check all 4 worker pods running with 2 containers each (app + sidecar)
   - Verify sidecar subscriptions active
   - Check worker logs for event processing

**Kubernetes Resources**:
- Deployment: recurring-consumer (2 replicas, modified)
- Deployment: notification-consumer (2 replicas, modified)
- Deployment: audit-consumer (1 replica, modified)
- Deployment: websocket-consumer (2 replicas, modified)
- Service: 4 services (one per worker)

**Files to Create/Modify**:
- k8s/workers/recurring-consumer-deployment.yaml (modified)
- k8s/workers/notification-consumer-deployment.yaml (modified)
- k8s/workers/audit-consumer-deployment.yaml (modified)
- k8s/workers/websocket-consumer-deployment.yaml (modified)
- k8s/scripts/verify-workers.sh

**Verification**:
- `kubectl get deployments` shows 4 worker deployments
- `kubectl get pods | grep consumer` shows 5 worker pods (2+2+1 replicas)
- Each pod has 2 containers (worker app + daprd sidecar)
- Sidecar logs show subscriptions: `Subscribed to [task-events] using pubsub [kafka-pubsub]`

**Dependencies**: Phase 2.5 (Dapr components + Kafka topics)
**Blockers**: Worker code must be available and compile; Kafka topics must exist

---

#### Phase 2.8: End-to-End Event Flow Verification

**Objective**: Complete event pipeline validated (backend → Kafka → workers).

**Tasks**:
1. Create `k8s/scripts/verify-event-flow.sh` - Full event flow test
   - Create task via backend API
   - Verify TaskCreated event in Kafka
   - Wait for recurring-consumer to generate next instance
   - Verify next instance created
   - Check audit-consumer logged the event
   - Verify no event duplicates

2. Create `k8s/scripts/test-integration.sh` - Full integration test
   - Multi-user scenario: 2 users creating tasks simultaneously
   - Verify user isolation (user1 events don't affect user2)
   - Test recurring task completion → next instance generation
   - Test reminder scheduling
   - Verify consumer lag < 5 minutes

**Files to Create**:
- k8s/scripts/verify-event-flow.sh
- k8s/scripts/test-integration.sh
- k8s/test-scenarios/ (optional test data files)

**Verification**:
- End-to-end latency: task creation → event publish → worker processing < 10 seconds
- Event deduplication: if same event published twice, worker processes only once
- User isolation: 2 concurrent users see correct isolated task lists
- Consumer lag: workers process events within 5 minutes of publication
- No message loss: all published events eventually consumed

**Dependencies**: Phase 2.6 (backend) + Phase 2.7 (workers)
**Blockers**: None (all infrastructure should be operational)

---

## Implementation Order & Dependencies

**Critical Path** (8 sequential phases):

```
Phase 2.1: Minikube
     ↓
Phase 2.2: Strimzi Operator
     ↓
Phase 2.3: Kafka Cluster + Topics
     ↓  ┐
     │  └─ Phase 2.4: Dapr Control Plane  (can run in parallel with 2.3)
     │
     └─→ Phase 2.5: Dapr Components
           ↓
           Phase 2.6: Backend + Sidecar
           ↓
           Phase 2.7: Workers + Sidecars
           ↓
           Phase 2.8: E2E Verification
```

**Parallel Work Opportunities**:
- Phase 2.4 (Dapr install) can start immediately after 2.1 (Minikube)
- Phase 2.4 can run in parallel with 2.2-2.3 (Strimzi + Kafka)
- Phase 2.6-2.7 can start immediately after 2.5

**Estimated Duration** (with 1-2 person team):
- Phase 2.1: 10 minutes
- Phase 2.2: 5 minutes
- Phase 2.3: 10 minutes
- Phase 2.4: 5 minutes
- Phase 2.5: 15 minutes (Dapr components config)
- Phase 2.6: 10 minutes (minimal changes to backend)
- Phase 2.7: 10 minutes (minimal changes to workers)
- Phase 2.8: 20 minutes (comprehensive verification)

**Total**: ~85 minutes (1.5 hours) for complete setup

---

## Quality Gates

**Phase 0 Exit Criteria**:
- ✅ All research.md decisions documented
- ✅ No NEEDS CLARIFICATION items remain
- ✅ Constitution Check: all principles satisfied

**Phase 1 Exit Criteria**:
- ✅ data-model.md complete (even if minimal)
- ✅ quickstart.md with step-by-step instructions
- ✅ YAML contracts in contracts/ directory
- ✅ All design decisions documented

**Phase 2 Exit Criteria** (per subphase):
- ✅ Phase 2.1: Minikube cluster healthy, single node Ready
- ✅ Phase 2.2: Strimzi operator pod running
- ✅ Phase 2.3: 3 Kafka brokers Ready, 3 topics created
- ✅ Phase 2.4: Dapr control plane services Running
- ✅ Phase 2.5: 3 Dapr components RUNNING
- ✅ Phase 2.6: Backend pod with 2 containers, TaskCreated events in Kafka
- ✅ Phase 2.7: 4 worker deployments with 5 total pods (2+2+1)
- ✅ Phase 2.8: End-to-end event flow successful, no duplicates, user isolation enforced

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Minikube resource exhaustion | Cluster crashes, services evicted | Allocate 8GB RAM, 4+ CPU; monitor resource usage |
| Kafka broker startup delays | Timeouts during deployment | Increase readiness probe timeout to 60s; monitor broker logs |
| Dapr sidecar injection failures | Sidecars not attached; events don't publish | Verify webhook rules; check controller logs; validate annotations |
| Network connectivity Kafka↔Dapr | Event publication fails silently | Test kafka-pubsub component connectivity explicitly; verify broker addresses |
| PostgreSQL connection string | State store fails to connect | Validate connection string in Dapr component spec; test DB access from pod |
| Event schema mismatch | Worker deduplication fails; duplicates processed | Verify event schema matches Spec-006 definition; version field present |
| Consumer lag accumulation | Workers fall behind; events queue | Horizontal scaling (increase replicas); monitor Kafka consumer lag metrics |

---

## Out of Scope

- Production Kubernetes cluster setup (this is local Minikube only)
- Helm chart optimization (Helm optional; manual YAML is primary)
- Prometheus/Grafana monitoring stack (observability mentioned but not implemented)
- Advanced Dapr features (service invocation, bindings, actors)
- Load testing infrastructure (performance testing beyond manual scenarios)
- Network policies and service mesh advanced features
- Disaster recovery and backup procedures for Kafka

---

## Next Steps

**After Phase 2 Complete**:
1. Run `/sp.tasks` to generate actionable task list for implementation
2. Each phase can be assigned to team members for parallel execution
3. Verification scripts provide quick validation at each phase boundary
4. Document any deviations or additional discoveries in research.md

**Forward to Production** (beyond Spec-007):
- Migrate from Minikube to managed Kubernetes (EKS, AKS, GKE)
- Replace local Kafka with AWS MSK or Confluent Cloud
- Add Helm charts for production deployment (optional)
- Implement Prometheus/Grafana monitoring
- Advanced Dapr features (service-to-service invocation, etc.)

