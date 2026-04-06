# Credentials Configuration Guide

This guide explains how to set up the required credentials for Spec-007 Local Event Architecture deployment.

## Required Credentials

Two secrets must be configured before deploying the backend and worker services:

1. **PostgreSQL Connection String** (DATABASE_URL)
   - Used by: Backend, Recurring Consumer, Notification Consumer, Audit Consumer, WebSocket Consumer
   - Stored in Kubernetes secret: `postgres-credentials`

2. **Better Auth Secret** (BETTER_AUTH_SECRET)
   - Used by: Backend, all Worker Services
   - Stored in Kubernetes secret: `auth-secrets`

## PostgreSQL Configuration

### Option A: Neon Serverless PostgreSQL (Cloud)

**Recommended for production-like setup**

1. Create a Neon account at https://neon.tech/

2. Create a new project:
   - Go to Console → New Project
   - Select region (closest to you)
   - Wait for project initialization

3. Get your connection string:
   - Go to Project → Database → Databases
   - Select the `neon_db` database (or create a new one)
   - Copy the connection string under "Connection string"
   - Should look like: `postgresql://user:password@host.neon.tech:5432/database?sslmode=require`

4. Create the Kubernetes secret:
   ```bash
   kubectl create secret generic postgres-credentials \
     --from-literal=connection-string="postgresql://user:password@host.neon.tech:5432/database?sslmode=require" \
     -n default
   ```

### Option B: Local PostgreSQL (Docker)

**Good for local development without cloud dependencies**

1. Run PostgreSQL in Docker:
   ```bash
   docker run --name todo-postgres \
     -e POSTGRES_USER=todouser \
     -e POSTGRES_PASSWORD=todopass123 \
     -e POSTGRES_DB=todo_db \
     -p 5432:5432 \
     -d postgres:15-alpine
   ```

2. Verify connection:
   ```bash
   docker logs todo-postgres
   # Should see: "listening on Unix socket..." message
   ```

3. Create the Kubernetes secret:
   ```bash
   kubectl create secret generic postgres-credentials \
     --from-literal=connection-string="postgresql://todouser:todopass123@host.docker.internal:5432/todo_db" \
     -n default
   ```

   **Note for Minikube**: Use host.docker.internal (Docker Desktop) or the actual host IP (Linux)

4. To connect from local machine:
   ```bash
   psql postgresql://todouser:todopass123@localhost:5432/todo_db
   ```

### Option C: PostgreSQL on Minikube

**Most isolated for testing**

1. Deploy PostgreSQL via Helm:
   ```bash
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm repo update

   helm install postgres bitnami/postgresql \
     --set auth.username=todouser \
     --set auth.password=todopass123 \
     --set auth.database=todo_db \
     -n default
   ```

2. Wait for PostgreSQL to be ready:
   ```bash
   kubectl wait --for=condition=Ready pod \
     -l app.kubernetes.io/name=postgresql \
     --timeout=300s
   ```

3. Get the service name:
   ```bash
   kubectl get svc -n default | grep postgres
   # Usually: postgres-postgresql
   ```

4. Create the Kubernetes secret:
   ```bash
   kubectl create secret generic postgres-credentials \
     --from-literal=connection-string="postgresql://todouser:todopass123@postgres-postgresql:5432/todo_db" \
     -n default
   ```

5. To connect from local machine:
   ```bash
   # Port forward to local machine
   kubectl port-forward svc/postgres-postgresql 5432:5432

   # Then connect
   psql postgresql://todouser:todopass123@localhost:5432/todo_db
   ```

## Better Auth Secret

### Generating a Secure Secret

Better Auth requires a minimum 32-character secret key for JWT signing.

**Option 1: Generate with OpenSSL**
```bash
openssl rand -base64 32
```

**Option 2: Generate with Python**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Option 3: Generate with Node.js**
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

**Option 4: Use a predefined secret (for local development only)**
```bash
# For local development only - NOT SECURE for production
BETTER_AUTH_SECRET="demo-secret-key-32-chars-minimum-1234"
```

### Creating the Secret

```bash
# Using the secret you generated
kubectl create secret generic auth-secrets \
  --from-literal=better-auth-secret="your-generated-secret-here" \
  -n default
```

## Creating Secrets - Step by Step

### Method 1: Using the Setup Script (Recommended)

```bash
bash k8s/setup-all.sh
```

The script will prompt you to:
1. Enter your PostgreSQL connection string
2. Enter your Better Auth secret

### Method 2: Manual Creation

1. Create PostgreSQL secret:
   ```bash
   kubectl create secret generic postgres-credentials \
     --from-literal=connection-string="your-connection-string-here" \
     -n default
   ```

2. Create Auth secret:
   ```bash
   kubectl create secret generic auth-secrets \
     --from-literal=better-auth-secret="your-secret-here" \
     -n default
   ```

3. Verify creation:
   ```bash
   kubectl get secrets -n default
   kubectl describe secret postgres-credentials
   kubectl describe secret auth-secrets
   ```

### Method 3: From Environment Variables

```bash
# Set environment variables with your values
export DATABASE_URL="your-connection-string"
export BETTER_AUTH_SECRET="your-secret"

# Create secrets from environment
kubectl create secret generic postgres-credentials \
  --from-literal=connection-string="$DATABASE_URL" \
  -n default

kubectl create secret generic auth-secrets \
  --from-literal=better-auth-secret="$BETTER_AUTH_SECRET" \
  -n default
```

### Method 4: From .env File

```bash
# Create a local .env file with your secrets
cat > k8s/.env << EOF
DATABASE_URL=your-connection-string-here
BETTER_AUTH_SECRET=your-secret-here
EOF

# Create secrets from file
kubectl create secret generic postgres-credentials \
  --from-literal=connection-string="$(grep DATABASE_URL k8s/.env | cut -d= -f2-)" \
  -n default

kubectl create secret generic auth-secrets \
  --from-literal=better-auth-secret="$(grep BETTER_AUTH_SECRET k8s/.env | cut -d= -f2-)" \
  -n default

# Clean up the file (it contains sensitive data)
rm k8s/.env
```

## Verifying Secrets

### Check Secret Exists

```bash
# List all secrets
kubectl get secrets -n default

# Expected output should show:
# postgres-credentials
# auth-secrets
```

### Verify Secret Values (⚠️ Caution: Shows sensitive data)

```bash
# View secret (base64 encoded)
kubectl get secret postgres-credentials -n default -o yaml

# View secret in plaintext (decode base64)
kubectl get secret postgres-credentials -n default \
  -o jsonpath='{.data.connection-string}' | base64 -d && echo

kubectl get secret auth-secrets -n default \
  -o jsonpath='{.data.better-auth-secret}' | base64 -d && echo
```

### Test Database Connectivity

1. Connect to backend pod:
   ```bash
   kubectl exec -it deployment/backend -- bash
   ```

2. Test PostgreSQL connection:
   ```bash
   python3 << 'EOF'
   from sqlalchemy import create_engine, text
   import os

   # Get connection string from environment variable
   # (set from the secret by the deployment)
   connection_string = os.getenv('DATABASE_URL')

   if not connection_string:
       print("DATABASE_URL not set")
       exit(1)

   try:
       engine = create_engine(connection_string)
       with engine.connect() as conn:
           result = conn.execute(text("SELECT 1"))
           print("✓ Database connection successful!")
   except Exception as e:
       print(f"✗ Database connection failed: {e}")
   EOF
   ```

## Updating Secrets

### If Secret is Wrong or Needs Update

1. Delete the old secret:
   ```bash
   kubectl delete secret postgres-credentials -n default
   # or
   kubectl delete secret auth-secrets -n default
   ```

2. Create new secret with correct values:
   ```bash
   kubectl create secret generic postgres-credentials \
     --from-literal=connection-string="new-connection-string" \
     -n default
   ```

3. Restart the pods to pick up the new secret:
   ```bash
   # Restart backend
   kubectl rollout restart deployment/backend

   # Restart all workers
   kubectl rollout restart deployment/recurring-consumer
   kubectl rollout restart deployment/notification-consumer
   kubectl rollout restart deployment/audit-consumer
   kubectl rollout restart deployment/websocket-consumer

   # Wait for new pods to be ready
   kubectl get pods -w
   ```

## Troubleshooting

### Secret Not Mounting to Pod

```bash
# Check if secret exists
kubectl get secret postgres-credentials -n default

# Check pod events for errors
kubectl describe pod <pod-name> -n default

# Look for error messages like "can't find secret"
```

### Database Connection Failing

```bash
# Check backend logs for connection errors
kubectl logs -f deployment/backend

# Verify connection string is correct
kubectl get secret postgres-credentials -n default \
  -o jsonpath='{.data.connection-string}' | base64 -d

# Test connectivity from local machine (if not using Minikube isolation)
psql "your-connection-string-here"
```

### Better Auth Not Working

```bash
# Check if secret is set
kubectl get secret auth-secrets -n default

# Check for JWT-related errors in logs
kubectl logs -f deployment/backend | grep -i auth

# Verify secret value is not empty
kubectl get secret auth-secrets -n default \
  -o jsonpath='{.data.better-auth-secret}' | base64 -d | wc -c
# Should be at least 32 characters (the decoded value)
```

## Security Best Practices

1. **Never commit secrets to version control**
   - Add `k8s/.env` to `.gitignore`
   - Never put actual secrets in YAML files

2. **Use strong secrets**
   - PostgreSQL password: 16+ characters, mixed case, numbers, symbols
   - Better Auth secret: Use `openssl rand -base64 32` (minimum 32 bytes)

3. **Restrict secret access**
   - Only service accounts that need access should be able to read secrets
   - Audit secret access in production

4. **Rotate secrets regularly**
   - Update PostgreSQL password every 90 days
   - Generate new Better Auth secret if compromised

5. **Use Kubernetes RBAC**
   - Limit which service accounts can read secrets
   - Audit kubectl access logs

## Environment Variable Mapping

The secrets are mounted as environment variables in the pods:

| Kubernetes Secret | Environment Variable | Used By |
|---|---|---|
| postgres-credentials.connection-string | DATABASE_URL | Backend, All Workers |
| auth-secrets.better-auth-secret | BETTER_AUTH_SECRET | Backend, All Workers |

The deployment YAMLs reference these using:
```yaml
env:
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: postgres-credentials
      key: connection-string
```

## Quick Setup Example

Here's a complete example setup:

```bash
# 1. Generate secrets
DB_URL="postgresql://user:pass@neon.neon.tech:5432/db?sslmode=require"
AUTH_SECRET=$(openssl rand -base64 32)

# 2. Create secrets
kubectl create secret generic postgres-credentials \
  --from-literal=connection-string="$DB_URL" \
  -n default

kubectl create secret generic auth-secrets \
  --from-literal=better-auth-secret="$AUTH_SECRET" \
  -n default

# 3. Verify
kubectl get secrets -n default

# 4. Deploy
bash k8s/setup-all.sh
```

## Support

If you encounter credential-related issues:

1. Verify the secret exists: `kubectl get secrets`
2. Verify pod can access secret: `kubectl describe pod <pod-name>`
3. Check pod logs: `kubectl logs -f deployment/<service>`
4. Verify secret format matches expected format
5. For Neon: Check database exists and connection string is correct
6. For local PostgreSQL: Check container is running and accessible

---

**Version**: 1.0
**Last Updated**: 2024
