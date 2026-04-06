# Research: Local Event Architecture Decisions

**Feature**: Spec-007 Local Event Architecture
**Created**: 2026-03-15
**Purpose**: Document architectural decisions, rationale, and alternatives considered

---

## Decision 1: Kubernetes Distribution for Local Development

**Question**: Which Kubernetes distribution for local development? (Minikube, Kind, Rancher Desktop, Docker Desktop K8s)

**Decision**: **Minikube**

**Rationale**:
- Mature, stable project with extensive documentation
- Full-featured Kubernetes cluster (not k3s subset)
- Excellent addon ecosystem (ingress, storage, metrics)
- Works across macOS, Linux, Windows (WSL2)
- Easy cluster reset/teardown for clean development iterations
- Resource-efficient for development laptops

**Alternatives Considered**:
- **Kind (Kubernetes in Docker)**: Lightweight, faster startup; less feature-complete; fewer addons available
- **Rancher Desktop**: Excellent UI; less standardized config; primarily macOS
- **Docker Desktop K8s**: Integrated with Docker; resource-heavy; Windows support via WSL2

**Trade-offs**:
- Minikube: Slightly slower startup than Kind, but more complete K8s simulation
- Learning curve: Minikube commands standardized; Kind requires understanding Docker container operations

**Validation**:
- Minikube documented in Phase 2.1 with resource requirements (4+ CPU, 8GB RAM)
- Setup script provided (`k8s/minikube/setup.sh`) for reproducibility

---

## Decision 2: Kafka Operator for Kubernetes Deployment

**Question**: How to deploy Kafka to Kubernetes? (Strimzi, Confluent Operator, manual StatefulSet)

**Decision**: **Strimzi Operator**

**Rationale**:
- Industry standard for Kafka on Kubernetes
- Open-source, community-driven (RedHat sponsored)
- CustomResourceDefinition (CRD) for declarative Kafka cluster management
- Built-in support for Kafka topics, users, security
- Automatic broker scaling, rolling updates
- Active security patching and version releases
- No licensing requirements (unlike Confluent)

**Alternatives Considered**:
- **Confluent Operator**: Commercial; feature-rich; overkill for development; licensing complexity
- **Manual StatefulSet**: Full control; complex to manage; error-prone; not recommended for production-grade practice

**Trade-offs**:
- Strimzi: Adds operator pod overhead; CRD learning curve
- Manual: More control; harder to maintain; risk of misconfiguration

**Validation**:
- Strimzi documented in Phase 2.2 with operator installation
- KafkaTopic CRDs defined in Phase 2.3 for declarative topic management

---

## Decision 3: Dapr Sidecar Injection Mode

**Question**: How to inject Dapr sidecars? (admission webhook, manual container, sidecar template)

**Decision**: **Admission Webhook (Automatic Injection)**

**Rationale**:
- Kubernetes-native pattern (same as Istio service mesh)
- Declarative via pod annotation (`dapr.io/enabled: "true"`)
- No code changes required (sidecar added by admission controller)
- Consistent sidecar configuration across all services
- Matches Dapr documentation and community best practices

**Alternatives Considered**:
- **Manual Container Addition**: Full control; error-prone; must update every deployment
- **Sidecar Template**: CRD-based; complex; requires operator knowledge

**Trade-offs**:
- Admission webhook: Adds webhook infrastructure; occasional injection failures if webhook unavailable
- Manual: More explicit; tedious; harder to maintain consistency

**Validation**:
- Webhook configured in Phase 2.4 (Dapr control plane installation)
- Sidecar annotations documented in all deployment specs (Phase 2.6-2.7)

---

## Decision 4: Kafka Topic Partitioning Strategy

**Question**: How many partitions and replication factor for local development topics?

**Decision**: **3 partitions, replication factor 3** (matches production pattern)

**Rationale**:
- 3 partitions: Enables parallelism across consumers; allows horizontal scaling to 3+ consumer instances
- Replication factor 3: High availability even in local Minikube (3 broker cluster); matches production standard
- Ensures development environment mirrors production behavior
- Prevents surprises when migrating to cloud Kafka
- Topic configuration directly translates to production (no change required)

**Alternatives Considered**:
- **1 partition, replication 1**: Simplest; no parallelism; doesn't test production scaling patterns
- **3 partitions, replication 1**: Parallelism but no HA; doesn't match production

**Trade-offs**:
- 3/3 requires 3 brokers (resource overhead); most realistic production simulation
- 1/1 simpler but misleading (false sense of reliability)

**Validation**:
- KafkaTopic specs define 3 partitions, replication factor 3 in Phase 2.3
- Worker consumer groups configured for parallelism (2-3 replicas per consumer)

---

## Decision 5: Dapr Component Configuration Storage

**Question**: Where to define Dapr components? (Kubernetes ConfigMap, CRD, environment variables)

**Decision**: **Kubernetes Component CRDs**

**Rationale**:
- Native Dapr pattern (matches official documentation)
- Declarative YAML; version-controlled with infrastructure
- Separate concerns: infrastructure config (YAML) vs. application code
- Easy to update brokers/credentials without redeploying apps
- Scalable to multiple environments (dev/staging/prod) with different values

**Alternatives Considered**:
- **Environment Variables**: Simpler initially; brittle; doesn't scale to complex configs
- **ConfigMap**: Possible; requires extra mapping layer; less idiomatic

**Trade-offs**:
- CRD: Requires understanding Dapr component spec; more YAML boilerplate
- Env vars: Easier to start; harder to maintain as complexity grows

**Validation**:
- Dapr components defined as Kubernetes resources in Phase 2.5
- Components: kafka-pubsub, postgres-statestore, kubernetes-secrets documented

---

## Decision 6: PostgreSQL Connectivity for State Store

**Question**: How to configure PostgreSQL connection for Dapr state store?

**Decision**: **Connection String via Environment Variable** (from Kubernetes Secret)

**Rationale**:
- PostgreSQL URL: `postgresql://user:password@host:port/database`
- Injected into Dapr component spec from Kubernetes Secret
- Decouples config from code; supports Neon PostgreSQL (already in use from Spec-006)
- Same connection string used by backend and workers
- Secrets stored securely in Kubernetes (not in YAML)

**Alternatives Considered**:
- **Hardcoded in Component YAML**: Security risk; inflexible
- **Pod environment variable**: Less explicit; easier to lose track

**Trade-offs**:
- Secret injection: Requires Secret creation; slightly more setup
- Hardcoded: Easier initially; serious security/flexibility problems

**Validation**:
- postgres-statestore component defined with connection string reference
- Kubernetes Secret created for PostgreSQL credentials (not shown in code; externalized)

---

## Decision 7: Event Publishing API Pattern (Dapr HTTP vs gRPC)

**Question**: How should backend publish events to Dapr? (HTTP, gRPC, SDK client)

**Decision**: **Dapr HTTP API** (non-blocking via asyncio)

**Rationale**:
- HTTP: Language-agnostic, easy to test with curl/tools
- Dapr sidecar listens on localhost:3500 (standard)
- Non-blocking: Published asynchronously after DB commit (asyncio.create_task)
- API latency isolated from event publishing latency (satisfies <50ms SLA)
- No Kafka client library bundled (satisfies Constitution XXVIII - Dapr abstraction)

**Alternatives Considered**:
- **gRPC**: Higher performance; requires gRPC client library; language coupling
- **SDK Client (dapr-python)**: Abstraction; additional dependency; complexity

**Trade-offs**:
- HTTP: Slightly higher latency (sub-millisecond overhead); simpler code; easier testing
- gRPC: Faster; more complexity; version coupling

**Validation**:
- Backend event publishing pattern documented in Phase 2.6
- API pattern: `POST http://localhost:3500/v1.0/publish/kafka-pubsub/topic-name`

---

## Decision 8: Kafka Persistence Strategy for Development

**Question**: Ephemeral or Persistent storage for Kafka brokers in Minikube?

**Decision**: **Ephemeral Storage** (default; can upgrade to persistent for long-running dev sessions)

**Rationale**:
- Ephemeral: Fast setup/teardown; no persistent volume management
- Suitable for short development cycles and testing
- Data loss acceptable in local development
- Can be changed to persistent volumes if needed for long-running sessions

**Alternatives Considered**:
- **Persistent Volumes**: Data survives cluster restart; requires storage class; adds complexity
- **Hybrid**: Ephemeral default; optional persistent for long sessions

**Trade-offs**:
- Ephemeral: Fast; data loss on cluster restart (acceptable for dev)
- Persistent: Slower; requires storage provisioning; closer to production

**Validation**:
- kafka-cluster spec uses ephemeral storage by default
- Comment added to Phase 2.3 explaining persistence upgrade path

---

## Decision 9: Worker Consumer Replica Count

**Question**: How many replicas for each worker service?

**Decision**: **2 replicas for parallel processing; 1 for audit (sequential consistency)**

**Rationale**:
- Recurring, Notification, WebSocket: 2 replicas each (can scale to 3+)
  - Parallelism across partitions
  - High availability (1 replica can be updated)
  - Tests production scaling pattern
- Audit: 1 replica only
  - Sequential consistency requirement (append-only audit log)
  - Multiple replicas could cause ordering issues or duplicates
  - Single replica still has pod restart resilience via Kubernetes

**Alternatives Considered**:
- **All services: 1 replica**: Simpler; no HA; doesn't test scaling
- **All services: 3+ replicas**: Resource overhead; audit ordering risk
- **Dynamic scaling**: Complex; not necessary for local development

**Trade-offs**:
- 2/1 split: Balances realism and resource efficiency; requires audit-specific handling
- All same: Simpler; less realistic for production patterns

**Validation**:
- Deployment replicas defined in Phase 2.7
- RollingUpdate strategy for parallel; Recreate for audit (Phase 2)

---

## Decision 10: Testing Strategy for Local Event Architecture

**Question**: How to validate event flow end-to-end?

**Decision**: **Bash Verification Scripts** (kubectl, kafka-console-producer/consumer, curl)

**Rationale**:
- No additional dependencies (kubectl, kafka tools already available)
- Easy to understand and modify (transparent shell scripts)
- Integrates with CI/CD pipelines (bash exit codes)
- Covers critical path: Minikube → Kafka → Dapr → Backend → Workers

**Alternatives Considered**:
- **Integration Test Suite (pytest/Jest)**: More powerful; requires test framework; overkill for infrastructure validation
- **Manual Testing**: Error-prone; not reproducible; doesn't document expectations

**Trade-offs**:
- Bash: Simple; great for infrastructure; limited for complex assertions
- Full test suite: More comprehensive; additional dependencies

**Validation**:
- 8 verification scripts created in Phase 2 (one per phase)
- verify-event-flow.sh for end-to-end validation (Phase 2.8)

---

## Decision 11: Helm Charts - Use or Not?

**Question**: Should we use Helm for deployment, or stick with raw YAML?

**Decision**: **Raw YAML (primary); Helm optional for future optimization**

**Rationale**:
- YAML: Explicit, version-controlled, no template abstraction
- Understandable to operators without Helm knowledge
- Easier to debug (actual manifests visible)
- Direct integration with kubectl tools
- Helm optional: Can be added later if needed for multi-environment support

**Alternatives Considered**:
- **Helm from Start**: More professional; template reuse; adds complexity; learning curve
- **Neither (imperative commands)**: Not recommended; no version control; error-prone

**Trade-offs**:
- Raw YAML: More verbose; not DRY; simple and explicit
- Helm: Reusable; parametric; adds abstraction layer

**Validation**:
- YAML files documented in plan.md with path structure
- Optional helm/ directory mentioned in project structure (for future use)

---

## Summary Table

| # | Decision | Choice | Rationale | Trade-off |
|---|----------|--------|-----------|-----------|
| 1 | K8s distribution | Minikube | Mature, feature-complete, excellent docs | Slower than Kind |
| 2 | Kafka operator | Strimzi | Open-source, CRD-based, industry standard | Operator overhead |
| 3 | Sidecar injection | Admission webhook | Kubernetes-native, declarative, consistent | Webhook dependency |
| 4 | Topic partitions | 3/3 (partitions/replication) | Parallelism + HA; mirrors production | More broker overhead |
| 5 | Dapr components | CRD resources | Native, version-controlled, scalable | More YAML boilerplate |
| 6 | PostgreSQL config | Connection string from Secret | Secure, decoupled, supports Neon | Requires Secret setup |
| 7 | Event publish API | HTTP (async) | Simple, testable, non-blocking | Slight latency overhead |
| 8 | Kafka storage | Ephemeral | Fast setup/teardown; acceptable data loss | Data loss on restart |
| 9 | Worker replicas | 2-1 (parallel/audit) | Realistic scaling + sequential consistency | More complex |
| 10 | Testing | Bash scripts | Simple, transparent, dependency-free | Limited assertions |
| 11 | Deployment | Raw YAML | Explicit, version-controlled, simple | More verbose |

---

## Open Questions for Consideration

**Monitoring & Observability**:
- Should we add Prometheus metrics collection? (Out of scope for Spec-007, but good to plan)
- Jaeger distributed tracing for event latency debugging? (Phase 7+ enhancement)

**Security Hardening**:
- RBAC policies for worker services to limit cross-namespace access? (Currently minimal RBAC)
- Network policies to restrict traffic between services? (Out of scope; local dev only)

**Future Enhancements**:
- Helm charts for multi-environment support (dev/staging/prod)? (Optional, Phase 8+)
- Automated cluster provisioning (Terraform/CloudFormation)? (Phase 8+)
- Chaos engineering for failure scenario testing? (Phase 8+)

---

## Validation Status

✅ **All Research Decisions Documented**: 11 core decisions with rationale, alternatives, trade-offs
✅ **Constitution Compliance**: All decisions align with Principles VII, XXVI, XXVII, XXVIII, XXX, XXXV
✅ **Phase 0 Exit Criteria Met**: No NEEDS CLARIFICATION items; all unknowns resolved
✅ **Ready for Phase 1 Design**: Decisions locked in; ready for detailed YAML contract generation

