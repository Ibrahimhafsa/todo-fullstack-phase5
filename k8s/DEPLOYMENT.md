# Spec-007 Local Event Architecture - Deployment Guide

This guide walks you through deploying the complete todo-fullstack application on a local Kubernetes cluster using Minikube, Kafka, and Dapr.

## Prerequisites

Before starting, ensure you have the following installed:

- **Minikube** (v1.30+): Local Kubernetes cluster
  - Installation: https://minikube.sigs.k8s.io/docs/start/

- **Kubectl** (v1.25+): Kubernetes CLI
  - Installation: https://kubernetes.io/docs/tasks/tools/

- **Docker** (20.10+): Container runtime
  - Installation: https://docs.docker.com/get-docker/

- **Helm** (v3.10+): Package manager for Kubernetes
  - Installation: https://helm.sh/docs/intro/install/

Verify installations:
```bash
minikube version
kubectl version --client
docker version
helm version
```

## System Requirements

- **CPU**: 4+ cores (8+ recommended for smooth operation)
- **RAM**: 8GB+ (16GB recommended)
- **Disk**: 30GB+ free space
- **OS**: Linux, macOS, or Windows (WSL2)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Minikube Cluster                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │   Frontend  │  │    Backend   │  │  Dapr Sidecars  │    │
│  │  (Next.js)  │  │   (FastAPI)  │  │ (Event Pub/Sub) │    │
│  └─────────────┘  └──────────────┘  └─────────────────┘    │
│         │               │                     │              │
│         └───────────────┼─────────────────────┘              │
│                         │                                    │
│        ┌────────────────┴────────────────┐                  │
│        │      Dapr Service Mesh          │                  │
│        │    (Event Publishing via        │                  │
│        │      HTTP API to Dapr)          │                  │
│        └────────────────┬────────────────┘                  │
│                         │                                    │
│  ┌──────────────────────┴──────────────────────────┐        │
│  │  Event Consumer Workers (4 services):           │        │
│  │  - Recurring Task Generator                     │        │
│  │  - Notification Service                         │        │
│  │  - Audit Logger                                 │        │
│  │  - WebSocket Broadcaster                        │        │
│  └──────────────────────┬──────────────────────────┘        │
│                         │                                    │
│                    ┌────▼────┐                              │
│                    │  Kafka   │                              │
│                    │ Cluster  │                              │
│                    │ (3 topics)                              │
│                    └──────────┘                              │
│                                                               │
│  ┌──────────────────────────────────────────────────┐       │
│  │        PostgreSQL (External via credentials)     │       │
│  │        Neon or local database                    │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step Deployment

### Option 1: Automated Setup (Recommended)

The fastest way to get everything running:

```bash
# 1. Navigate to the project root
cd /path/to/todo-fullstack-phase5

# 2. Make the setup script executable
chmod +x k8s/setup-all.sh

# 3. Run the automated setup
bash k8s/setup-all.sh
```

The setup script will:
1. Check all prerequisites
2. Initialize Minikube with appropriate resources
3. Install Strimzi Kafka operator
4. Deploy Kafka cluster with 3 brokers
5. Install Dapr control plane
6. Deploy Dapr components (Pub/Sub, State Store, Secrets)
7. Prompt you for credentials (PostgreSQL URL and Better Auth secret)
8. Deploy backend and frontend services
9. Deploy all event consumer workers
10. Verify the complete deployment

**Timeline**: ~10-15 minutes (mostly waiting for services to start)

### Option 2: Manual Step-by-Step Setup

If you prefer more control or need to troubleshoot:

#### Phase 1: Minikube Setup

```bash
# Initialize Minikube cluster (4 CPUs, 8GB RAM, 30GB disk)
bash k8s/minikube/setup.sh

# Verify cluster is running
kubectl cluster-info
kubectl get nodes
```

#### Phase 2: Kafka Infrastructure

```bash
# Create Kafka namespace
kubectl apply -f k8s/kafka/namespace.yaml

# Install Strimzi Operator (manages Kafka via Kubernetes)
bash k8s/kafka/install-strimzi.sh

# Wait for Strimzi operator to be ready (1-2 minutes)
kubectl wait --for=condition=Ready pod \
  -l app.kubernetes.io/name=strimzi-cluster-operator \
  -n kafka --timeout=300s

# Deploy Kafka cluster (3 brokers, may take 2-3 minutes)
kubectl apply -f k8s/kafka/kafka-cluster.yaml

# Wait for Kafka cluster to be ready
kubectl wait --for=condition=Ready kafka/kafka-cluster \
  -n kafka --timeout=600s

# Create Kafka topics
kubectl apply -f k8s/kafka/kafka-topics.yaml
```

#### Phase 3: Dapr Setup

```bash
# Create Dapr system namespace
kubectl apply -f k8s/dapr/dapr-system-namespace.yaml

# Install Dapr control plane
bash k8s/dapr/install-dapr.sh

# Wait for Dapr to be ready (1-2 minutes)
kubectl wait --for=condition=Ready pod \
  -l app=dapr-operator \
  -n dapr-system --timeout=300s

# Enable Dapr sidecar injection on default namespace
kubectl label namespace default dapr.io/enabled=true --overwrite

# Deploy Dapr components (Pub/Sub, State Store, Secrets)
kubectl apply -f k8s/dapr/components/
```

#### Phase 4: Configure Credentials

**Important**: You MUST set up secrets before deploying applications.

```bash
# Get your PostgreSQL connection string (Neon or local)
# Example: postgresql://user:password@host.neon.tech:5432/database?sslmode=require

# Create PostgreSQL credentials secret
kubectl create secret generic postgres-credentials \
  --from-literal=connection-string="your-connection-string-here" \
  -n default

# Get or generate your Better Auth secret (minimum 32 characters)
# You can use: openssl rand -base64 32

# Create auth secret
kubectl create secret generic auth-secrets \
  --from-literal=better-auth-secret="your-secret-here" \
  -n default

# Verify secrets were created
kubectl get secrets -n default
```

#### Phase 5: Deploy Backend and Frontend

```bash
# Deploy backend service with Dapr sidecar
kubectl apply -f k8s/backend/backend-deployment.yaml

# Deploy frontend service with Dapr sidecar
kubectl apply -f k8s/frontend/frontend-deployment.yaml

# Wait for backend to be ready
kubectl wait --for=condition=Ready pod \
  -l app=backend \
  -n default --timeout=300s

# Wait for frontend to be ready
kubectl wait --for=condition=Ready pod \
  -l app=frontend \
  -n default --timeout=300s
```

#### Phase 6: Deploy Event Consumer Workers

```bash
# Deploy recurring task consumer
kubectl apply -f k8s/workers/recurring-consumer-deployment.yaml

# Deploy notification consumer
kubectl apply -f k8s/workers/notification-consumer-deployment.yaml

# Deploy audit consumer
kubectl apply -f k8s/workers/audit-consumer-deployment.yaml

# Deploy WebSocket consumer
kubectl apply -f k8s/workers/websocket-consumer-deployment.yaml

# Wait for all workers to be ready
kubectl wait --for=condition=Ready pod \
  -l component=event-consumer \
  -n default --timeout=300s
```

## Accessing the Application

### Frontend (Next.js UI)

```bash
# Forward frontend port to local machine
kubectl port-forward svc/frontend 3000:3000

# Open in browser
open http://localhost:3000
```

### Backend API (FastAPI)

```bash
# Forward backend port to local machine
kubectl port-forward svc/backend 8000:8000

# Access API documentation
open http://localhost:8000/docs

# Test a simple API call
curl http://localhost:3000/health
```

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/backend

# Frontend logs
kubectl logs -f deployment/frontend

# Recurring task consumer logs
kubectl logs -f deployment/recurring-consumer

# Notification consumer logs
kubectl logs -f deployment/notification-consumer

# Audit consumer logs
kubectl logs -f deployment/audit-consumer

# WebSocket consumer logs
kubectl logs -f deployment/websocket-consumer

# Follow logs with timestamps
kubectl logs -f deployment/backend --timestamps=true
```

## Verification

### Automated Verification

Run the comprehensive verification script:

```bash
# Run all verification checks
bash k8s/verify/verify-all.sh

# This checks:
# - Minikube status
# - Kubernetes cluster health
# - Kafka cluster and topics
# - Dapr control plane and components
# - All secrets configured
# - All deployments and pods
# - All services are accessible
```

### Manual Verification

```bash
# Check Minikube status
minikube status

# Check cluster nodes
kubectl get nodes

# Check all namespaces
kubectl get namespaces

# Check Kafka cluster
kubectl get kafka -n kafka
kubectl get kafkatopics -n kafka

# Check Dapr control plane
kubectl get pods -n dapr-system

# Check Dapr components
kubectl get components

# Check all deployments
kubectl get deployments

# Check all pods
kubectl get pods -o wide

# Check services
kubectl get services

# Check secrets
kubectl get secrets
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Minikube Won't Start

```bash
# Check Minikube status
minikube status

# If it shows "Docker is not running":
# Start Docker Desktop (macOS/Windows) or Docker daemon (Linux)

# Delete and recreate Minikube cluster
minikube delete
minikube start --cpus=4 --memory=8192 --disk-size=30GB
```

#### 2. Pods Not Starting / Stuck in Pending State

```bash
# Check pod events for error details
kubectl describe pod <pod-name>

# Check resource availability
kubectl top nodes
kubectl top pods

# If low on resources:
# - Close other applications
# - Increase Minikube resources:
minikube delete
minikube start --cpus=8 --memory=16384 --disk-size=50GB
```

#### 3. Kafka Brokers Not Ready

```bash
# Check Kafka cluster status
kubectl get kafka -n kafka -o yaml | grep -A 10 "status:"

# Check Kafka broker logs
kubectl logs -f statefulset/kafka-cluster-kafka -n kafka

# If stuck, check Strimzi operator logs
kubectl logs -f deployment/strimzi-cluster-operator -n kafka
```

#### 4. Dapr Sidecar Not Injected

```bash
# Verify sidecar injection is enabled
kubectl get namespace default -o yaml | grep dapr

# If not enabled, enable it:
kubectl label namespace default dapr.io/enabled=true --overwrite

# Restart the pods (deployment will recreate them)
kubectl rollout restart deployment/backend
kubectl rollout restart deployment/frontend
```

#### 5. Backend Cannot Connect to Database

```bash
# Check if secrets are created
kubectl get secrets -n default

# Verify secret values are correct
kubectl get secret postgres-credentials -n default -o yaml

# Check backend logs for connection errors
kubectl logs -f deployment/backend

# If secret is wrong, delete and recreate:
kubectl delete secret postgres-credentials
kubectl create secret generic postgres-credentials \
  --from-literal=connection-string="your-correct-connection-string"

# Restart backend to pick up new secret
kubectl rollout restart deployment/backend
```

#### 6. Event Publishing Not Working

```bash
# Check if Dapr Pub/Sub component is running
kubectl get components -n default

# Check component status
kubectl get components kafka-pubsub -o yaml

# Check if backend can reach Dapr sidecar (should be on port 3500)
kubectl exec -it deployment/backend -- \
  curl http://localhost:3500/v1.0/healthz

# Check backend logs for Dapr-related errors
kubectl logs -f deployment/backend | grep -i dapr
```

#### 7. Port Forwarding Issues

```bash
# Kill existing port-forward processes
pkill -f "kubectl port-forward"

# Try again with a different local port
kubectl port-forward svc/frontend 3001:3000  # Use 3001 instead of 3000
```

## Cleanup

### Stop Everything Without Deleting Minikube

```bash
# Delete all deployments
kubectl delete deployments -n default --all

# Delete all services
kubectl delete services -n default --all

# Keep Minikube cluster running for faster restart next time
```

### Full Cleanup (Delete Everything)

```bash
# Stop and delete Minikube cluster
bash k8s/minikube/teardown.sh

# Or manually:
minikube stop
minikube delete

# Clean up local state
rm -f ~/.spec007-setup-state
```

## File Structure

```
k8s/
├── setup-all.sh                    # Master orchestration script
├── DEPLOYMENT.md                   # This file
├── .env.example                    # Environment configuration template
│
├── minikube/
│   ├── setup.sh                   # Initialize Minikube cluster
│   └── teardown.sh                # Delete Minikube cluster
│
├── kafka/
│   ├── namespace.yaml             # Kafka namespace
│   ├── install-strimzi.sh         # Strimzi Operator installation
│   ├── kafka-cluster.yaml         # Kafka cluster (3 brokers)
│   └── kafka-topics.yaml          # Kafka topics (3 topics)
│
├── dapr/
│   ├── dapr-system-namespace.yaml # Dapr system namespace
│   ├── install-dapr.sh            # Dapr control plane installation
│   └── components/
│       ├── kafka-pubsub.yaml      # Dapr Pub/Sub (Kafka)
│       ├── postgres-statestore.yaml # Dapr State Store (PostgreSQL)
│       └── kubernetes-secrets.yaml  # Dapr Secrets (K8s)
│
├── backend/
│   └── backend-deployment.yaml    # Backend service + Dapr sidecar
│
├── frontend/
│   └── frontend-deployment.yaml   # Frontend service + Dapr sidecar
│
├── workers/
│   ├── recurring-consumer-deployment.yaml
│   ├── notification-consumer-deployment.yaml
│   ├── audit-consumer-deployment.yaml
│   └── websocket-consumer-deployment.yaml
│
└── verify/
    └── verify-all.sh              # Comprehensive verification script
```

## Performance Targets

- **Frontend load time**: < 2 seconds
- **API response time**: < 200ms (p95)
- **Event publishing latency**: 50-100ms (non-blocking)
- **Consumer lag**: < 5 minutes
- **WebSocket connection setup**: < 500ms

## Next Steps

After successful deployment:

1. **Access the frontend**: http://localhost:3000
2. **Create some tasks** using the UI
3. **Monitor events**: Watch task creation trigger event publishing
4. **View logs**: Check consumer workers are processing events
5. **Test event flow**: Create task → Event published → Consumers process
6. **Scale workers**: Increase worker replicas to test parallel processing
7. **Monitor Kafka**: Check topic partitions and consumer groups

## Architecture Principles (Phase 5)

This deployment follows the Constitution principles:

- **Principle VII**: All queries filter by authenticated `user_id` from JWT
- **Principle XXVI**: Fully event-driven with async event publishing
- **Principle XXVII**: Event bus via Kafka (3 topics: task-events, reminders, task-updates)
- **Principle XXVIII**: Dapr Pub/Sub abstraction (no direct Kafka clients)
- **Principle XXX**: Event versioning with JSON schema and version field
- **Principle XXXV**: 100% backward compatibility (existing CRUD endpoints unchanged)

## Support and Troubleshooting

For detailed troubleshooting:

1. Check pod logs: `kubectl logs -f deployment/<service-name>`
2. Describe pod: `kubectl describe pod <pod-name>`
3. Check events: `kubectl get events --sort-by='.lastTimestamp'`
4. Check resource usage: `kubectl top pods`

## Related Documentation

- Kubernetes: https://kubernetes.io/docs/
- Minikube: https://minikube.sigs.k8s.io/docs/
- Kafka: https://kafka.apache.org/documentation/
- Dapr: https://docs.dapr.io/
- Strimzi: https://strimzi.io/docs/

---

**Status**: Spec-007 Phase 2.7 (Local Kubernetes Deployment)
**Version**: 1.0
**Last Updated**: 2024
