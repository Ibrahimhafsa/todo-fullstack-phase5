# Kubernetes Deployment for Spec-007 Local Event Architecture

Complete Kubernetes setup for running the todo-fullstack application on Minikube with Kafka event streaming and Dapr service mesh.

## 📋 Quick Start

### Fastest Way to Get Started

```bash
# Make the script executable
chmod +x k8s/setup-all.sh

# Run the automated setup
bash k8s/setup-all.sh
```

This single command will:
- ✅ Check all prerequisites (minikube, kubectl, docker, helm)
- ✅ Initialize Minikube cluster (4 CPU, 8GB RAM, 30GB disk)
- ✅ Install Strimzi Kafka operator
- ✅ Deploy 3-broker Kafka cluster with 3 topics
- ✅ Install Dapr control plane
- ✅ Deploy Dapr components (Pub/Sub, State Store, Secrets)
- ✅ Prompt for PostgreSQL and Better Auth credentials
- ✅ Deploy backend, frontend, and 4 worker services
- ✅ Verify all components are running

**Time**: ~10-15 minutes (mostly waiting for services to start)

## 📁 Directory Structure

```
k8s/
├── README.md                       # This file
├── DEPLOYMENT.md                   # Detailed deployment guide
├── CREDENTIALS.md                  # Credential configuration guide
├── setup-all.sh                    # Master orchestration script
├── .env.example                    # Environment configuration template
│
├── minikube/
│   ├── setup.sh                   # Initialize Minikube cluster
│   └── teardown.sh                # Delete Minikube cluster
│
├── kafka/
│   ├── namespace.yaml             # Kafka namespace
│   ├── install-strimzi.sh         # Strimzi Operator installation
│   ├── kafka-cluster.yaml         # 3-broker Kafka cluster
│   └── kafka-topics.yaml          # 3 Kafka topics (task-events, reminders, task-updates)
│
├── dapr/
│   ├── dapr-system-namespace.yaml # Dapr system namespace
│   ├── install-dapr.sh            # Dapr control plane installation
│   └── components/
│       ├── kafka-pubsub.yaml      # Dapr Pub/Sub component (Kafka backend)
│       ├── postgres-statestore.yaml # Dapr State Store (PostgreSQL)
│       └── kubernetes-secrets.yaml  # Dapr Secrets (Kubernetes secrets)
│
├── backend/
│   └── backend-deployment.yaml    # Backend service + Dapr sidecar
│
├── frontend/
│   └── frontend-deployment.yaml   # Frontend service + Dapr sidecar
│
├── workers/
│   ├── recurring-consumer-deployment.yaml     # Recurring task generator
│   ├── notification-consumer-deployment.yaml  # Notification service
│   ├── audit-consumer-deployment.yaml         # Audit logger
│   └── websocket-consumer-deployment.yaml     # WebSocket broadcaster
│
└── verify/
    ├── verify-all.sh              # Comprehensive verification script
    └── diagnose.sh                # Diagnostic data collector
```

## 🚀 Usage

### Automated Setup (Recommended)

```bash
bash k8s/setup-all.sh
```

The script handles everything in phases:
1. Prerequisites checking
2. Minikube cluster initialization
3. Kafka infrastructure setup
4. Dapr control plane installation
5. Credentials configuration (prompts you)
6. Backend and frontend deployment
7. Event consumer workers deployment

### Manual Setup (If You Prefer)

See **DEPLOYMENT.md** for detailed step-by-step instructions.

### Access Applications

After successful deployment:

```bash
# Frontend (Next.js UI)
kubectl port-forward svc/frontend 3000:3000
# Open: http://localhost:3000

# Backend API (FastAPI)
kubectl port-forward svc/backend 8000:8000
# Open: http://localhost:8000/docs
```

### Verify Deployment

```bash
# Comprehensive verification
bash k8s/verify/verify-all.sh

# Collect diagnostic data
bash k8s/verify/diagnose.sh
```

## 📋 Prerequisites

- **Minikube** v1.30+: Local Kubernetes cluster
- **kubectl** v1.25+: Kubernetes CLI
- **Docker** 20.10+: Container runtime
- **Helm** v3.10+: Package manager for Kubernetes

**System Requirements**:
- CPU: 4+ cores (8+ recommended)
- RAM: 8GB+ (16GB recommended)
- Disk: 30GB+ free space

## 🔐 Credentials

Two secrets are required:

1. **PostgreSQL Connection String**
   - Example: `postgresql://user:password@host.neon.tech:5432/database?sslmode=require`
   - See **CREDENTIALS.md** for options (Neon, Docker, local)

2. **Better Auth Secret**
   - Generate: `openssl rand -base64 32`
   - Must be at least 32 characters

The `setup-all.sh` script will prompt you for these values and create Kubernetes secrets automatically.

## 🏗️ Architecture

### Components

```
Minikube Cluster
├── Backend (FastAPI)
│   └── Dapr Sidecar (HTTP on port 3500)
├── Frontend (Next.js)
│   └── Dapr Sidecar
├── Recurring Consumer
│   └── Dapr Sidecar
├── Notification Consumer (2 replicas)
│   └── Dapr Sidecars
├── Audit Consumer
│   └── Dapr Sidecar
└── WebSocket Consumer (2 replicas)
    └── Dapr Sidecars

Event Bus (Kafka)
├── 3 Brokers
├── Task Events topic (3 partitions)
├── Reminders topic (3 partitions)
└── Task Updates topic (3 partitions)

Dapr Service Mesh
├── Pub/Sub Component (Kafka backend)
├── State Store Component (PostgreSQL)
└── Secrets Component (Kubernetes)

External
└── PostgreSQL (Neon or local Docker)
```

### Event Flow

```
User Action
    ↓
Backend API
    ↓
Event Published (Dapr Pub/Sub → Kafka)
    ↓
Distributed to Consumer Workers:
├── Recurring Task Generator
├── Notification Service
├── Audit Logger
└── WebSocket Broadcaster
    ↓
Update Frontend (WebSocket) or Database (Audit)
```

## 📖 Documentation

- **DEPLOYMENT.md**: Complete deployment guide with step-by-step instructions and troubleshooting
- **CREDENTIALS.md**: Detailed credential setup guide for PostgreSQL and Better Auth
- **setup-all.sh**: Self-documenting master orchestration script
- **verify/verify-all.sh**: Comprehensive verification script with explanations
- **verify/diagnose.sh**: Diagnostic data collector for troubleshooting

## 🔧 Common Tasks

### Check Status

```bash
# Minikube cluster
minikube status

# All deployments
kubectl get deployments

# All pods
kubectl get pods

# All services
kubectl get svc
```

### View Logs

```bash
# Backend
kubectl logs -f deployment/backend

# Any worker
kubectl logs -f deployment/recurring-consumer

# Follow logs with timestamps
kubectl logs -f deployment/backend --timestamps=true
```

### Port Forward

```bash
# Frontend on port 3000
kubectl port-forward svc/frontend 3000:3000

# Backend on port 8000
kubectl port-forward svc/backend 8000:8000

# Kafka broker (if needed)
kubectl port-forward -n kafka svc/kafka-cluster-kafka-bootstrap 9092:9092
```

### Scale Workers

```bash
# Scale recurring consumer to 3 replicas
kubectl scale deployment recurring-consumer --replicas=3

# Scale notification consumer
kubectl scale deployment notification-consumer --replicas=3
```

### Restart a Service

```bash
# Restart backend (will recreate pod)
kubectl rollout restart deployment/backend

# Wait for rollout
kubectl rollout status deployment/backend
```

### Update a Secret

```bash
# Delete old secret
kubectl delete secret postgres-credentials

# Create new secret
kubectl create secret generic postgres-credentials \
  --from-literal=connection-string="new-connection-string"

# Restart services to pick up new secret
kubectl rollout restart deployment/backend
kubectl rollout restart deployment/recurring-consumer
```

## 🐛 Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Check pod resources
kubectl top pods
```

### Cannot Connect to Backend

```bash
# Verify pod is running
kubectl get pod -l app=backend

# Check logs for errors
kubectl logs -f deployment/backend

# Verify service exists
kubectl get svc backend

# Test connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  curl http://backend:8000/health
```

### Kafka Issues

```bash
# Check Kafka cluster status
kubectl get kafka -n kafka

# Check brokers
kubectl get pods -n kafka -l strimzi.io/kind=Kafka

# Check topics
kubectl get kafkatopics -n kafka

# Check Strimzi operator logs
kubectl logs -f deployment/strimzi-cluster-operator -n kafka
```

### Dapr Issues

```bash
# Check Dapr control plane
kubectl get pods -n dapr-system

# Check Dapr components
kubectl get components

# Check component status
kubectl describe component kafka-pubsub

# Test Dapr sidecar
kubectl exec -it deployment/backend -- \
  curl http://localhost:3500/v1.0/healthz
```

For detailed troubleshooting: See **DEPLOYMENT.md** section "Troubleshooting"

## 🧪 Verification

```bash
# Run comprehensive checks
bash k8s/verify/verify-all.sh

# This checks:
# ✓ Minikube status
# ✓ Kubernetes cluster
# ✓ Kafka cluster and topics
# ✓ Dapr control plane and components
# ✓ All secrets configured
# ✓ All deployments and pods
# ✓ Pod health and status
```

## 📊 Monitoring

### Resource Usage

```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods -n default
```

### Pod Events

```bash
# Recent events
kubectl get events -n default --sort-by='.lastTimestamp'

# Watch events in real-time
kubectl get events -n default --watch
```

### Logs

```bash
# All logs from all pods
for pod in $(kubectl get pods -n default -o name); do
  echo "=== $pod ==="
  kubectl logs "$pod" --tail=10
done
```

## 🛑 Stopping and Cleanup

### Stop Without Deleting

```bash
# Keep cluster, delete services
kubectl delete deployments -n default --all
```

### Full Cleanup

```bash
# Delete everything
bash k8s/minikube/teardown.sh

# Or manually
minikube delete
```

## 📚 Architecture Principles

This deployment follows Constitution principles:

- **Principle VII**: All queries filter by authenticated `user_id` from JWT
- **Principle XXVI**: Fully event-driven with async event publishing
- **Principle XXVII**: Event bus via Kafka (task-events, reminders, task-updates topics)
- **Principle XXVIII**: Dapr Pub/Sub abstraction (no direct Kafka clients)
- **Principle XXX**: Event versioning with JSON schema
- **Principle XXXV**: 100% backward compatibility

## 🌍 Next Steps After Deployment

1. Access frontend: http://localhost:3000
2. Create tasks in the UI
3. Watch events flow through the system:
   - Task creation → Event published
   - Consumers receive and process events
   - Audit logs recorded
   - Notifications triggered
   - WebSocket updates broadcast
4. Monitor logs: `kubectl logs -f deployment/<service>`
5. Scale workers: `kubectl scale deployment/<worker> --replicas=3`
6. Test event flow with diagnostic script

## 📞 Support

If you encounter issues:

1. Check **DEPLOYMENT.md** troubleshooting section
2. Run verification script: `bash k8s/verify/verify-all.sh`
3. Collect diagnostics: `bash k8s/verify/diagnose.sh`
4. Review pod logs: `kubectl logs -f deployment/<service>`
5. Check pod events: `kubectl describe pod <pod-name>`

## 📝 Files Reference

| File | Purpose |
|------|---------|
| setup-all.sh | Master orchestration script (main entry point) |
| DEPLOYMENT.md | Detailed deployment guide and troubleshooting |
| CREDENTIALS.md | Credential configuration for PostgreSQL and Auth |
| .env.example | Environment configuration template |
| minikube/setup.sh | Initialize Minikube cluster |
| minikube/teardown.sh | Delete Minikube cluster |
| kafka/install-strimzi.sh | Install Kafka operator |
| kafka/kafka-cluster.yaml | 3-broker Kafka cluster definition |
| kafka/kafka-topics.yaml | Kafka topics definition (3 topics) |
| dapr/install-dapr.sh | Install Dapr control plane |
| dapr/components/*.yaml | Dapr component configurations |
| backend/backend-deployment.yaml | Backend + Dapr sidecar |
| frontend/frontend-deployment.yaml | Frontend + Dapr sidecar |
| workers/*-deployment.yaml | Event consumer worker deployments (4 workers) |
| verify/verify-all.sh | Comprehensive verification script |
| verify/diagnose.sh | Diagnostic data collector |

## ✅ Checklist for First Time Setup

- [ ] Install prerequisites (minikube, kubectl, docker, helm)
- [ ] Copy `.env.example` to `.env` and fill in credentials
- [ ] Run `bash k8s/setup-all.sh`
- [ ] Wait for setup to complete (~10-15 minutes)
- [ ] Run `bash k8s/verify/verify-all.sh`
- [ ] Access frontend at http://localhost:3000
- [ ] Access backend API at http://localhost:8000/docs
- [ ] Create a test task and verify events are processed
- [ ] Check worker logs: `kubectl logs -f deployment/recurring-consumer`

## 📄 License

Part of the todo-fullstack application (Spec-007 Phase 2.7)

---

**Version**: 1.0
**Status**: Spec-007 Phase 2.7 (Local Kubernetes Deployment)
**Last Updated**: 2024
