---
title: Todo Backend Phase 3
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
pinned: false
---

# Task Management API

FastAPI backend for managing user tasks with JWT authentication and ownership enforcement.

## Prerequisites

- Python 3.11+
- Neon PostgreSQL database
- Spec-1 Authentication (Better Auth) completed

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```env
DATABASE_URL=postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require
BETTER_AUTH_SECRET=your-32-character-or-longer-secret-here
```

**Note**: `BETTER_AUTH_SECRET` must match the frontend Better Auth configuration.

### 4. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/{user_id}/tasks` | Create task |
| GET | `/api/{user_id}/tasks` | List user's tasks |
| GET | `/api/{user_id}/tasks/{task_id}` | Get task details |
| PUT | `/api/{user_id}/tasks/{task_id}` | Update task |
| DELETE | `/api/{user_id}/tasks/{task_id}` | Delete task |
| PATCH | `/api/{user_id}/tasks/{task_id}/complete` | Toggle completion |

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py          # FastAPI dependencies
│   │   └── routes/
│   │       └── tasks.py     # Task CRUD endpoints
│   ├── auth/
│   │   └── jwt.py           # JWT verification
│   ├── models/
│   │   └── task.py          # Task SQLModel
│   ├── schemas/
│   │   └── task.py          # Pydantic schemas
│   ├── services/
│   │   └── task_service.py  # Business logic
│   ├── config.py            # Environment config
│   ├── database.py          # Database connection
│   └── main.py              # FastAPI app
├── tests/
├── requirements.txt
└── .env.example
```

## Security

- All routes require valid JWT authentication
- Users can only access their own tasks
- Path user_id is validated against JWT claims
- Non-owned task access returns 404 (not 403) to prevent enumeration
