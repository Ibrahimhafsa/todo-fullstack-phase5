# Docker Deployment Guide

## Prerequisites
- Docker 20.10+ and Docker Compose 1.29+ installed
- Project structure with `backend/` and `frontend/` directories

## Build Commands

### Backend Image
```bash
docker build -t todo-backend:1.0 ./backend
```

### Frontend Image
```bash
docker build -t todo-frontend:1.0 ./frontend
```

### Build Both (Sequential)
```bash
docker build -t todo-backend:1.0 ./backend && \
docker build -t todo-frontend:1.0 ./frontend
```

---

## Run Commands (Individual Containers)

### Backend Container (Port 8000)
```bash
docker run -d \
  --name todo-backend \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@db:5432/tododb" \
  -e JWT_SECRET="your-secret-key-here" \
  todo-backend:1.0
```

### Frontend Container (Port 3000)
```bash
docker run -d \
  --name todo-frontend \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL="http://localhost:8000" \
  todo-frontend:1.0
```

---

## Network Communication (Recommended)

Create a custom Docker network for secure inter-container communication:

```bash
# Create network
docker network create todo-network

# Run backend on custom network
docker run -d \
  --name todo-backend \
  --network todo-network \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@db:5432/tododb" \
  -e JWT_SECRET="your-secret-key-here" \
  todo-backend:1.0

# Run frontend on custom network
docker run -d \
  --name todo-frontend \
  --network todo-network \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL="http://todo-backend:8000" \
  todo-frontend:1.0
```

---

## Docker Compose (Recommended)

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: todo-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/tododb
      - JWT_SECRET=${JWT_SECRET:-your-secret-key}
    depends_on:
      - db
    networks:
      - todo-network
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: todo-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    networks:
      - todo-network
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    container_name: todo-db
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=tododb
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - todo-network
    restart: unless-stopped

volumes:
  db_data:

networks:
  todo-network:
    driver: bridge
```

### Run with Docker Compose
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

---

## Verification

### Health Checks

**Backend Health:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

**Frontend:**
```bash
curl http://localhost:3000
# Expected: HTML response
```

### Container Status
```bash
docker ps
docker container stats
```

### Access Services
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Production Considerations

### Environment Variables
Never hardcode secrets. Use:
- `.env.production` for build-time variables
- Docker secrets (Swarm) or external secret management (K8s)
- Environment variable injection at runtime

### Image Optimization
- Backend: 600-800MB (Python slim + dependencies)
- Frontend: 400-500MB (Node LTS + built Next.js app)

### Scaling
For production multi-instance deployment:
```bash
# Scale backend to 3 replicas (with load balancer)
docker-compose up -d --scale backend=3
```

### Registry Push
```bash
docker tag todo-backend:1.0 registry.example.com/todo-backend:1.0
docker push registry.example.com/todo-backend:1.0
```

---

## Troubleshooting

### Backend container exits
```bash
docker logs todo-backend
# Check DATABASE_URL and JWT_SECRET environment variables
```

### Frontend can't reach backend
```bash
# Verify network connectivity
docker exec todo-frontend curl http://todo-backend:8000/health
```

### Port conflicts
```bash
# Check which process uses port 8000/3000
lsof -i :8000
lsof -i :3000

# Use different ports if needed
docker run -p 8001:8000 todo-backend:1.0
docker run -p 3001:3000 todo-frontend:1.0
```

### Rebuild without cache
```bash
docker build --no-cache -t todo-backend:1.0 ./backend
docker build --no-cache -t todo-frontend:1.0 ./frontend
```
