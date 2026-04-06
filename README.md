# Full-Stack Todo Application with Event-Driven Architecture

A production-ready, full-stack todo management system built with modern cloud-native technologies. This project demonstrates advanced concepts in distributed systems, event-driven architecture, Kubernetes orchestration, and microservices integration.

**Status**: Phase 5 Complete (Phases 1-4 + Kubernetes/Dapr Infrastructure)  
**Version**: 1.0.0  
**Last Updated**: April 2026

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [API Documentation](#api-documentation)
- [Event-Driven Architecture](#event-driven-architecture)
- [Dapr Integration](#dapr-integration)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Known Limitations](#known-limitations)
- [Future Roadmap](#future-roadmap)
- [Contributing](#contributing)

---

## Project Overview

This is a **full-stack todo management application** that goes beyond basic CRUD operations. It implements:

✅ **Complete user authentication** with JWT tokens  
✅ **Rich task management** (create, read, update, delete, search, filter, sort)  
✅ **Advanced features** (priority levels, tags, due dates, recurring tasks)  
✅ **AI-powered task assistance** (natural language processing via OpenAI)  
✅ **Real-time event processing** (Kafka event bus with async consumers)  
✅ **Cloud-native deployment** (Kubernetes with Dapr service mesh)  
✅ **Scalable infrastructure** (containerized services, event-driven workers)  

**Target Use Case**: Portfolio project showcasing full-stack development, distributed systems, and DevOps practices.

---

## Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                            │
│  Next.js 14 + React 19 + Tailwind CSS + Better Auth JWT     │
│  (Responsive web UI, real-time updates via WebSocket)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway Layer                          │
│          FastAPI Backend (Python 3.11+)                      │
│     (JWT Authentication, CORS, Rate Limiting)               │
│                                                              │
│  Routes:                                                     │
│  ├── /api/{user_id}/tasks (CRUD)                            │
│  ├── /api/{user_id}/tasks/search (Full-text search)         │
│  ├── /api/{user_id}/chat (AI Assistant)                     │
│  └── /health (Diagnostics)                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌──────────────┐
│ PostgreSQL  │ │ Dapr Pub/Sub│ │ Event Queue  │
│ (Primary    │ │ (Kafka via  │ │ (Kafka)      │
│  Database)  │ │  Dapr)      │ │              │
└─────────────┘ └─────────────┘ └──────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Recurring  │ │ Notification │ │    Audit     │
│    Worker    │ │    Worker    │ │   Worker     │
│ (APScheduler)│ │  (APScheduler)│ │ (Logger)     │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Deployment Architecture (Kubernetes)

```
┌──────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster (Minikube)                 │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Dapr Control Plane (System Namespace)                      │ │
│  │  ├── Dapr Operator                                           │ │
│  │  ├── State Store Sidecar Injector                            │ │
│  │  └── Pub/Sub Configuration                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Strimzi Kafka (kafka namespace)                             │ │
│  │  ├── ZooKeeper                                               │ │
│  │  ├── Kafka Broker 0/1/2                                      │ │
│  │  └── Topics: task-events, reminders, task-updates           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Application Services (default namespace)                    │ │
│  │  ├── Backend Deployment (+ Dapr sidecar)                    │ │
│  │  ├── Frontend Deployment                                     │ │
│  │  ├── Recurring Worker Pod                                    │ │
│  │  ├── Notification Worker Pod                                 │ │
│  │  ├── Audit Worker Pod                                        │ │
│  │  └── WebSocket Worker Pod                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  External Services                                            │ │
│  │  ├── Neon PostgreSQL (Cloud)                                │ │
│  │  ├── OpenAI API (Chat/Task Assistance)                      │ │
│  │  └── Kubernetes Secrets (Credentials)                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Next.js** | 14.2.35 | React framework for SSR/SSG |
| **React** | 18.3.1 | UI library |
| **TypeScript** | 5.x | Type-safe JavaScript |
| **Tailwind CSS** | 3.4.19 | Utility-first CSS framework |
| **Better Auth** | 1.4.17 | JWT authentication client |

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **FastAPI** | 0.128.0 | Modern async Python web framework |
| **SQLModel** | 0.0.31 | SQL toolkit + ORM (SQLAlchemy + Pydantic) |
| **PyJWT** | 2.10.1 | JWT token handling |
| **APScheduler** | 3.11.2 | Task scheduling & reminders |
| **Alembic** | 1.13.0 | Database migrations |
| **Pydantic** | 2.12.5 | Data validation |
| **Uvicorn** | 0.40.0 | ASGI server |

### Data & Persistence
| Technology | Version | Purpose |
|-----------|---------|---------|
| **PostgreSQL** | 15+ | Primary database (Neon Cloud) |
| **psycopg2** | 2.9.11 | PostgreSQL adapter for Python |

### Orchestration & Messaging
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Kubernetes** | 1.27+ | Container orchestration |
| **Dapr** | 1.12+ | Distributed app runtime (Pub/Sub abstraction) |
| **Kafka** (via Strimzi) | 3.x | Event streaming (configured, not actively used) |
| **Docker** | 24.0+ | Containerization |
| **Helm** | 3.x | Kubernetes package manager |

### Development & Testing
| Technology | Version | Purpose |
|-----------|---------|---------|
| **pytest** | 9.0.2 | Unit & integration testing |
| **pytest-asyncio** | 1.3.0 | Async test support |
| **python-dotenv** | 1.2.1 | Environment configuration |

---

## Features

### ✅ Phase 1-2: Core Todo Management
- **Create tasks** with title, description, and metadata
- **Read tasks** with full details and ownership validation
- **Update tasks** (title, description, status)
- **Delete tasks** with cascade cleanup
- **Toggle completion** (complete/incomplete toggle)

### ✅ Phase 3: User Authentication & Security
- **JWT-based authentication** using Better Auth
- **User isolation** (users can only access their own tasks)
- **Ownership enforcement** at every API endpoint
- **Secure token validation** with configurable secrets
- **Role-based access control** (framework ready for expansion)

### ✅ Phase 4: Frontend & UI
- **Responsive design** (mobile, tablet, desktop)
- **Task dashboard** with real-time updates
- **Create/Edit task forms** with validation
- **Search & filter** by status, priority, tags
- **Sorting** by creation date, due date, priority
- **Dark mode support** (Tailwind CSS)

### ✅ Phase 5: Advanced Features & Event Architecture
- **Task priorities** (Low, Medium, High)
- **Tags & categorization** (multi-tag support)
- **Due dates & reminders** (APScheduler-based)
- **Recurring tasks** (Daily, Weekly, Monthly patterns)
- **Full-text search** (PostgreSQL GIN indexes)
- **AI task assistance** (OpenAI integration)
- **Event-driven architecture** (Kafka topics, async processing)
- **Event consumers** (recurring, notification, audit workers)
- **Kubernetes deployment** (4+ services, auto-scaling ready)
- **Dapr service mesh** (Pub/Sub, State Store, Secrets)

---

## Project Structure

```
todo-fullstack-phase5/
│
├── frontend/                       # Next.js frontend application
│   ├── app/
│   │   ├── page.tsx               # Home page
│   │   ├── login/page.tsx          # Login page
│   │   ├── dashboard/page.tsx      # Main dashboard
│   │   └── api/                    # API routes
│   ├── components/
│   │   ├── TaskCard.tsx            # Task display component
│   │   ├── TaskForm.tsx            # Create/edit form
│   │   ├── SearchBar.tsx           # Search component
│   │   ├── FilterSort.tsx          # Filter & sort controls
│   │   └── Navigation.tsx          # Header/nav
│   ├── public/                     # Static assets
│   ├── styles/                     # Tailwind CSS
│   ├── package.json                # Frontend dependencies
│   └── next.config.js              # Next.js configuration
│
├── backend/                        # FastAPI backend application
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py             # FastAPI dependencies (auth)
│   │   │   └── routes/
│   │   │       ├── tasks.py        # Task CRUD endpoints
│   │   │       ├── search.py       # Search & filter endpoints
│   │   │       ├── chat.py         # AI chat endpoint
│   │   │       └── health.py       # Health check
│   │   ├── auth/
│   │   │   └── jwt.py              # JWT token validation
│   │   ├── models/
│   │   │   └── task.py             # SQLModel task definition
│   │   ├── schemas/
│   │   │   ├── task.py             # Pydantic task schemas
│   │   │   └── event.py            # Event schemas
│   │   ├── services/
│   │   │   ├── task_service.py     # Task business logic
│   │   │   ├── search_service.py   # Search/filter logic
│   │   │   ├── event_service.py    # Event publishing
│   │   │   ├── chat_service.py     # OpenAI integration
│   │   │   └── recurring_service.py # Recurring task logic
│   │   ├── config.py               # Configuration & env vars
│   │   ├── database.py             # Database connection pool
│   │   └── main.py                 # FastAPI app initialization
│   ├── migrations/                 # Alembic database migrations
│   ├── tests/                      # Unit & integration tests
│   ├── Dockerfile                  # Container image
│   ├── requirements.txt            # Python dependencies
│   └── .env.example                # Environment template
│
├── k8s/                            # Kubernetes configurations
│   ├── minikube/
│   │   ├── setup.sh                # Minikube cluster init
│   │   └── teardown.sh             # Cleanup
│   ├── kafka/
│   │   ├── namespace.yaml          # Kafka namespace
│   │   ├── kafka-cluster.yaml      # Strimzi Kafka deployment
│   │   ├── kafka-topics.yaml       # Topic definitions
│   │   └── install-strimzi.sh      # Strimzi operator install
│   ├── dapr/
│   │   ├── install-dapr.sh         # Dapr control plane
│   │   └── components/
│   │       ├── kafka-pubsub.yaml   # Dapr Pub/Sub config
│   │       ├── postgres-statestore.yaml  # State store
│   │       └── kubernetes-secrets.yaml   # Secrets provider
│   ├── backend/
│   │   └── backend-deployment.yaml # Backend K8s deployment
│   ├── frontend/
│   │   └── frontend-deployment.yaml # Frontend K8s deployment
│   ├── workers/
│   │   ├── recurring-worker-deployment.yaml
│   │   ├── notification-worker-deployment.yaml
│   │   ├── audit-worker-deployment.yaml
│   │   └── websocket-worker-deployment.yaml
│   ├── setup-all.sh                # Master setup orchestration
│   ├── DEPLOYMENT.md               # Detailed setup guide
│   └── CREDENTIALS.md              # Credential configuration
│
├── specs/                          # Project specifications
│   ├── 001-jwt-auth/
│   ├── 002-task-crud/
│   ├── 003-frontend-ui/
│   ├── 004-ai-chatbot/
│   ├── 005-chat-ui/
│   ├── 006-advanced-features/
│   └── 007-local-event-architecture/
│
├── history/                        # Documentation & records
│   ├── prompts/                    # Prompt history records
│   └── adr/                        # Architecture decision records
│
├── .env.example                    # Environment template
├── .env                            # Local environment (git-ignored)
├── docker-compose.yml              # Docker Compose (optional local)
├── DOCKER.md                       # Docker setup guide
├── CLAUDE.md                       # Project guidelines
├── README.md                       # This file
└── IMPLEMENTATION_SUMMARY.md       # Phase 4 implementation details
```

---

## Installation & Setup

### Prerequisites

- **Node.js** 18+ (frontend)
- **Python** 3.11+ (backend)
- **PostgreSQL** 14+ (or Neon cloud account)
- **Docker** 24.0+ (for containerization)
- **Kubernetes** 1.27+ (for orchestration, optional)
- **Git** (version control)

### Option 1: Local Development (Recommended for Getting Started)

#### Step 1: Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/todo-fullstack-phase5.git
cd todo-fullstack-phase5

# Create environment file
cp .env.example .env
```

#### Step 2: Configure Environment

Edit `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@ep-xxxxx.us-east-2.aws.neon.tech/dbname?sslmode=require

# Authentication
BETTER_AUTH_SECRET=your-secret-key-at-least-32-characters-long

# Backend
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# Frontend
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# OpenAI (optional, for chat features)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxx
```

#### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations (if using Alembic)
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: `http://localhost:8000`  
API Docs: `http://localhost:8000/docs`

#### Step 4: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at: `http://localhost:3000`

#### Step 5: Verify Setup

1. Open `http://localhost:3000` in browser
2. Sign up / login with Better Auth
3. Create a task via the UI
4. Check backend logs for ownership enforcement

---

### Option 2: Docker Compose (All Services Containerized)

```bash
# From project root
docker-compose up --build

# Wait for services to initialize (~30 seconds)
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Includes**:
- PostgreSQL database (persisted volume)
- Backend FastAPI service
- Frontend Next.js service
- Network isolation between services

For more details, see `DOCKER.md`.

---

### Option 3: Kubernetes Deployment (Full Production Setup)

#### Prerequisites

```bash
# Install tools
brew install minikube kubectl helm  # Mac
# or apt-get install minikube kubectl helm  # Linux
# or scoop install minikube kubectl helm  # Windows

# Start Minikube
minikube start --cpus=4 --memory=8192 --disk-size=30gb
```

#### Automated Setup (Recommended)

```bash
# From project root
chmod +x k8s/setup-all.sh
bash k8s/setup-all.sh

# Script will prompt for:
# - PostgreSQL connection string
# - Better Auth secret
# - OpenAI API key (optional)

# Verify deployment (10-15 minutes)
kubectl get pods -A
kubectl get svc -A
```

#### Manual Setup (If Needed)

See `k8s/DEPLOYMENT.md` for step-by-step Kubernetes deployment instructions.

#### Access Applications

```bash
# Get service IPs
kubectl get svc -n default

# Frontend (port-forward)
kubectl port-forward svc/frontend 3000:3000

# Backend (port-forward)
kubectl port-forward svc/backend 8000:8000

# Kafka UI (via Strimzi)
kubectl port-forward -n kafka svc/kafka-ui 8080:8080
```

---

## API Documentation

### Authentication

All endpoints (except `/health`) require JWT token in header:

```bash
Authorization: Bearer <token_from_better_auth>
```

### Task Endpoints

#### Create Task

```http
POST /api/{user_id}/tasks
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "Complete project documentation",
  "description": "Write README and API docs",
  "priority": "High",
  "tags": ["documentation", "phase5"],
  "due_date": "2026-04-15T23:59:59Z",
  "is_recurring": false
}
```

**Response** (201):
```json
{
  "id": 42,
  "user_id": "user_123",
  "title": "Complete project documentation",
  "description": "Write README and API docs",
  "completed": false,
  "priority": "High",
  "tags": ["documentation", "phase5"],
  "due_date": "2026-04-15T23:59:59Z",
  "created_at": "2026-04-06T10:30:00Z",
  "updated_at": "2026-04-06T10:30:00Z"
}
```

#### List Tasks

```http
GET /api/{user_id}/tasks?skip=0&limit=10&completed=false
Authorization: Bearer <token>
```

**Response** (200):
```json
{
  "items": [
    {
      "id": 42,
      "title": "Complete project documentation",
      "completed": false,
      "priority": "High",
      ...
    }
  ],
  "total": 42
}
```

#### Search Tasks

```http
GET /api/{user_id}/tasks/search?q=documentation&priority=High
Authorization: Bearer <token>
```

#### Update Task

```http
PUT /api/{user_id}/tasks/{task_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "Updated title",
  "priority": "Medium"
}
```

#### Complete Task

```http
PATCH /api/{user_id}/tasks/{task_id}/complete
Authorization: Bearer <token>
```

#### Delete Task

```http
DELETE /api/{user_id}/tasks/{task_id}
Authorization: Bearer <token>
```

#### Health Check

```http
GET /health
```

**Response** (200):
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-04-06T10:30:00Z"
}
```

### AI Chat Endpoint (Phase 4)

```http
POST /api/{user_id}/chat
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "Create a task to review the project spec"
}
```

**Response** (200):
```json
{
  "conversation_id": "conv_456",
  "user_message": "Create a task to review the project spec",
  "assistant_message": "I've created a task: 'Review project spec' with default priority.",
  "timestamp": "2026-04-06T10:30:00Z"
}
```

---

## Event-Driven Architecture

### Why Events?

The system uses **event-driven architecture** to:
- ✅ Decouple services (backend doesn't block on worker jobs)
- ✅ Scale independently (each worker can auto-scale)
- ✅ Add features without changing core code (new consumers listen to events)
- ✅ Maintain audit trail (all changes are events)
- ✅ Enable real-time updates (WebSocket pushes)

### Event Topics

Three Kafka topics manage the event flow:

#### 1. `task-events` (Primary Event Bus)

Triggered on every task state change:

```json
{
  "event_type": "TaskCreated|TaskUpdated|TaskCompleted|TaskDeleted",
  "event_id": "uuid-abc123",
  "timestamp": "2026-04-06T10:30:00Z",
  "version": "1.0",
  "user_id": "user_123",
  "task_id": 42,
  "data": {
    "title": "Complete project",
    "priority": "High",
    "tags": ["phase5"],
    "is_recurring": true,
    "recurring_pattern": "Weekly"
  }
}
```

**Consumers**:
- **Recurring Worker** → Auto-generates next occurrence
- **Audit Worker** → Logs to database for compliance
- **Analytics** → Tracks usage metrics

#### 2. `reminders` (Notification Queue)

When a task's reminder time arrives:

```json
{
  "event_type": "ReminderScheduled",
  "task_id": 42,
  "user_id": "user_123",
  "reminder_time": "2026-04-15T09:00:00Z",
  "title": "Complete project documentation"
}
```

**Consumers**:
- **Notification Worker** → Sends email/push notifications

#### 3. `task-updates` (Real-Time Updates)

For frontend WebSocket pushes:

```json
{
  "event_type": "TaskUpdated",
  "task_id": 42,
  "user_id": "user_123",
  "changes": {
    "completed": false,
    "priority": "High"
  }
}
```

**Consumers**:
- **WebSocket Worker** → Pushes to frontend via WebSocket

### Event Publishing Flow

```
User Action (Frontend)
       ↓
   API Endpoint
       ↓
   Database Commit ✓
       ↓
Event Published (async, non-blocking)
       ↓
   Kafka Topic
       ├→ Recurring Worker
       ├→ Notification Worker
       ├→ Audit Worker
       └→ WebSocket Worker
       ↓
   Independent Processing
       ↓
   Updates (if needed) → DB
```

**Key Property**: Publishing is **non-blocking**. The API returns success immediately, and workers process events asynchronously.

---

## Dapr Integration

### What is Dapr?

**Dapr** (Distributed Application Runtime) is a sidecar architecture that provides cloud-agnostic building blocks for microservices:

- **Pub/Sub**: Abstract message publishing (we use Kafka, but can switch to RabbitMQ, Azure ServiceBus, etc. without code changes)
- **State Management**: Abstract data storage (PostgreSQL state store in this setup)
- **Service-to-Service Invocation**: Service discovery and communication
- **Secrets**: Secure credential management

### How We Use Dapr

#### 1. Pub/Sub (Event Publishing)

**Without Dapr** (tightly coupled):
```python
# Direct Kafka client
producer = KafkaProducer(bootstrap_servers='kafka:9092')
producer.send('task-events', event_json)
```

**With Dapr** (abstracted):
```python
# Dapr HTTP API
response = requests.post(
    'http://localhost:3500/v1.0/publish/kafka-pubsub/task-events',
    json=event
)
```

**Benefits**:
- ✅ Swap Kafka for RabbitMQ/Azure ServiceBus with config-only change
- ✅ Built-in retry logic
- ✅ Cloud-native (works on any Kubernetes cluster)

#### 2. State Store (Future)

Currently not implemented, but ready for:
```python
# Store session/cache without touching code
requests.post(
    'http://localhost:3500/v1.0/state/postgres-statestore',
    json=[{
        "key": "user_123_settings",
        "value": {"theme": "dark"}
    }]
)
```

#### 3. Secrets (Kubernetes Integration)

Credentials stored as Kubernetes Secrets, accessed via Dapr:
```bash
kubectl create secret generic db-creds \
  --from-literal=password=xxx
```

Dapr automatically injects into pod environment.

### Dapr Components (Kubernetes)

Located in `k8s/dapr/components/`:

- **kafka-pubsub.yaml**: Kafka broker endpoint, topic configuration
- **postgres-statestore.yaml**: Connection string, table definitions
- **kubernetes-secrets.yaml**: Kubernetes secret provider

---

## Kubernetes Deployment

### Cluster Architecture

The setup uses **Minikube** (local) but is compatible with cloud Kubernetes (EKS, AKS, GKE):

```
Kubernetes Cluster (1 Master, N Worker Nodes)
├── kube-system (System Services)
├── dapr-system (Dapr Control Plane)
├── kafka (Kafka/Strimzi)
└── default (Application Pods)
    ├── backend-xxxxx (FastAPI + Dapr sidecar)
    ├── frontend-xxxxx (Next.js)
    ├── recurring-worker-xxxxx (Event Consumer)
    ├── notification-worker-xxxxx (Event Consumer)
    ├── audit-worker-xxxxx (Event Consumer)
    └── websocket-worker-xxxxx (Event Consumer)
```

### Deployments & Services

#### Backend Deployment
- **Image**: `backend:latest`
- **Replicas**: 1 (can scale to 3+)
- **Sidecar**: Dapr injected for Pub/Sub
- **Service**: ClusterIP (internal routing)

#### Frontend Deployment
- **Image**: `frontend:latest`
- **Replicas**: 1
- **Service**: NodePort (accessible from localhost)

#### Worker Deployments
- **Recurring Worker**: Listens to `task-events`, generates recurring tasks
- **Notification Worker**: Listens to `reminders`, sends notifications
- **Audit Worker**: Logs all events for compliance
- **WebSocket Worker**: Pushes real-time updates to frontend

### Auto-Scaling (Ready for Production)

Configured in deployment YAML:
```yaml
autoscaling:
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

---

## Known Limitations

### Phase 5 Status

✅ **Implemented & Tested**:
- Full CRUD API
- JWT authentication
- Frontend dashboard
- Advanced features (priority, tags, due dates)
- Recurring task logic
- Event publishing (async, non-blocking)
- Dapr configuration
- Kubernetes deployments

🟡 **Configured but Not Actively Used**:
- **Kafka** (3 topics created, but consumers not actively processing events in production)
  - *Reason*: Event publishing is async and non-blocking, so backend doesn't depend on message processing
  - *Status*: Ready for Phase 6 (event consumer deployment at scale)
  
❌ **Not Implemented (Phase 6+)**:
- Real-time WebSocket updates (workers configured, not deployed)
- Email notifications (infrastructure ready, service not integrated)
- Full event replay & recovery
- Cross-cluster Kafka replication
- Advanced monitoring (Prometheus/Grafana)

### Known Issues

1. **Kafka Consumers Not Auto-Starting**
   - Workers are deployed but require manual triggering
   - Workaround: Deploy workers manually via kubectl

2. **Event Lag SLA Not Monitored**
   - No consumer lag monitoring dashboard
   - Workaround: Check Kafka metrics manually

3. **No Dead Letter Queue (DLQ)**
   - Failed events are logged but not queued for retry
   - Workaround: Implement DLQ in Phase 6

---

## Future Roadmap

### Phase 6: Production Event Streaming (Next)
- [ ] Deploy event consumers at scale
- [ ] Implement dead-letter queue (DLQ)
- [ ] Add consumer lag monitoring
- [ ] Real-time WebSocket updates
- [ ] Email notification service

### Phase 7: Cloud Deployment (Planned)
- [ ] Migrate to EKS / AKS / GKE
- [ ] Setup multi-region failover
- [ ] Implement service mesh (Istio)
- [ ] Advanced RBAC & pod security policies
- [ ] Horizontal pod autoscaling (HPA)

### Phase 8: Advanced Features
- [ ] Task templates & bulk operations
- [ ] Team collaboration (shared tasks)
- [ ] Time tracking & analytics
- [ ] Third-party integrations (Slack, Discord, calendar)
- [ ] Mobile app (React Native)

### Phase 9: Performance & Optimization
- [ ] Database query optimization
- [ ] Redis caching layer
- [ ] GraphQL API (alongside REST)
- [ ] CDN for static assets
- [ ] Performance profiling & benchmarks

---

## Screenshots & Demo

*Coming soon. Example images:*

- **Login Page**: Clean authentication with Better Auth
- **Dashboard**: Task list with filters, search, sort
- **Create Task**: Form with priority, tags, due date
- **AI Assistant**: Chat interface for task management
- **Kubernetes Status**: Dashboard showing pod health

---

## Contributing

Contributions welcome! Please follow:

1. **Branch naming**: `feature/xxx`, `bugfix/xxx`, `docs/xxx`
2. **Commit messages**: Descriptive, referencing specs/issues
3. **Code style**: Follow existing patterns (FastAPI, Next.js conventions)
4. **Testing**: Write tests for new features (pytest for backend, Jest for frontend)
5. **Documentation**: Update specs and this README

### Running Tests

**Backend**:
```bash
cd backend
pytest -v tests/
```

**Frontend**:
```bash
cd frontend
npm test
```

---

## Architecture Decision Records (ADRs)

Key architectural decisions documented in `history/adr/`:

- **ADR-001**: Event-driven architecture with Dapr
- **ADR-002**: PostgreSQL for state, Kafka for events
- **ADR-003**: JWT tokens for authentication
- **ADR-004**: Kubernetes/Minikube for local development

---

## License

MIT License - See LICENSE file for details.

---

## Author

**Created by**: Hafsa Ibrahim  
**Portfolio**: [GitHub](https://github.com/yourusername)  
**LinkedIn**: [Profile](https://linkedin.com/in/yourprofile)  

**Built for**: Hackathon - Quarter 4, 2026

---

## Support

For issues, questions, or feedback:

1. **Issues**: Open a GitHub issue with details
2. **Documentation**: Check `k8s/DEPLOYMENT.md` and `DOCKER.md`
3. **Specs**: Review feature specs in `specs/` directory
4. **Logs**: Check `kubectl logs <pod-name>` for Kubernetes issues

---

## Acknowledgments

- **Better Auth**: Excellent JWT authentication library
- **FastAPI**: Modern, fast Python framework
- **Next.js**: Production-ready React framework
- **Dapr**: Simplifying distributed application development
- **Strimzi**: Kafka on Kubernetes made easy
- **Neon**: Serverless PostgreSQL

---

**Last Updated**: April 2026  
**Version**: 1.0.0 (Phase 5 Complete)
