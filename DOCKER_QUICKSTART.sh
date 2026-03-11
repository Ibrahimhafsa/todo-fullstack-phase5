#!/bin/bash
# Docker Quick Start - Copy/paste these commands

# =============================================================================
# BUILD IMAGES
# =============================================================================

# Build Backend Image (Python 3.11 slim)
docker build -t todo-backend:1.0 ./backend

# Build Frontend Image (Node 20 LTS multi-stage)
docker build -t todo-frontend:1.0 ./frontend

# =============================================================================
# RUN CONTAINERS (Using Docker Network)
# =============================================================================

# 1. Create isolated network
docker network create todo-network

# 2. Run Backend Container
docker run -d \
  --name todo-backend \
  --network todo-network \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@db:5432/tododb" \
  -e JWT_SECRET="your-jwt-secret-key" \
  todo-backend:1.0

# 3. Run Frontend Container
docker run -d \
  --name todo-frontend \
  --network todo-network \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL="http://todo-backend:8000" \
  todo-frontend:1.0

# =============================================================================
# VERIFICATION
# =============================================================================

# Check containers are running
docker ps

# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000

# View logs
docker logs todo-backend
docker logs todo-frontend

# =============================================================================
# CLEANUP
# =============================================================================

# Stop containers
docker stop todo-backend todo-frontend

# Remove containers
docker rm todo-backend todo-frontend

# Remove network
docker network rm todo-network

# Remove images
docker rmi todo-backend:1.0 todo-frontend:1.0
