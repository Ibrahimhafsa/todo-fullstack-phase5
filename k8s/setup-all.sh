#!/bin/bash
# Master Orchestration Script for Spec-007 Local Event Architecture
# This script orchestrates the complete setup of the local Kubernetes environment
# with Minikube, Kafka, Dapr, and all microservices

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MINIKUBE_CPUS=${MINIKUBE_CPUS:-4}
MINIKUBE_MEMORY=${MINIKUBE_MEMORY:-8192}
MINIKUBE_DISK=${MINIKUBE_DISK:-30000}
NAMESPACE_KAFKA="kafka"
NAMESPACE_DAPR="dapr-system"
NAMESPACE_DEFAULT="default"

# State tracking
SETUP_STATE_FILE="${HOME}/.spec007-setup-state"

# Functions
print_header() {
  echo -e "\n${MAGENTA}========================================${NC}"
  echo -e "${MAGENTA}$1${NC}"
  echo -e "${MAGENTA}========================================${NC}\n"
}

print_step() {
  echo -e "${CYAN}→ $1${NC}"
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
  echo -e "${RED}✗ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

check_prerequisite() {
  local cmd=$1
  local name=${2:-$cmd}

  if ! command -v "$cmd" &> /dev/null; then
    print_error "$name is not installed"
    return 1
  fi
  print_success "$name is installed"
  return 0
}

check_all_prerequisites() {
  print_header "Checking Prerequisites"

  local all_ok=true

  check_prerequisite "minikube" "Minikube" || all_ok=false
  check_prerequisite "kubectl" "Kubectl" || all_ok=false
  check_prerequisite "docker" "Docker" || all_ok=false
  check_prerequisite "helm" "Helm" || all_ok=false

  if [ "$all_ok" = false ]; then
    print_error "Please install missing prerequisites"
    print_info "Installation guides:"
    print_info "  Minikube: https://minikube.sigs.k8s.io/docs/start/"
    print_info "  Kubectl: https://kubernetes.io/docs/tasks/tools/"
    print_info "  Docker: https://docs.docker.com/get-docker/"
    print_info "  Helm: https://helm.sh/docs/intro/install/"
    return 1
  fi

  return 0
}

load_setup_state() {
  if [ -f "$SETUP_STATE_FILE" ]; then
    source "$SETUP_STATE_FILE"
  fi
}

save_setup_state() {
  cat > "$SETUP_STATE_FILE" << EOF
COMPLETED_STEPS="$COMPLETED_STEPS"
MINIKUBE_READY=${MINIKUBE_READY:-false}
KAFKA_READY=${KAFKA_READY:-false}
DAPR_READY=${DAPR_READY:-false}
CREDENTIALS_READY=${CREDENTIALS_READY:-false}
BACKEND_READY=${BACKEND_READY:-false}
WORKERS_READY=${WORKERS_READY:-false}
EOF
}

phase_1_minikube() {
  print_header "Phase 1: Minikube Cluster Setup"

  if [ "$MINIKUBE_READY" = "true" ]; then
    print_info "Skipping Phase 1 (already completed)"
    return 0
  fi

  print_step "Initializing Minikube cluster..."
  bash "$SCRIPT_DIR/minikube/setup.sh" \
    --cpus "$MINIKUBE_CPUS" \
    --memory "$MINIKUBE_MEMORY" \
    --disk "$MINIKUBE_DISK"

  print_step "Waiting for Minikube to be ready (this may take a few minutes)..."
  kubectl wait --for=condition=Ready node --all --timeout=300s || {
    print_error "Minikube failed to reach ready state"
    return 1
  }

  print_success "Minikube cluster is ready"
  MINIKUBE_READY=true
  save_setup_state
}

phase_2_kafka() {
  print_header "Phase 2: Kafka Infrastructure Setup"

  if [ "$KAFKA_READY" = "true" ]; then
    print_info "Skipping Phase 2 (already completed)"
    return 0
  fi

  print_step "Creating Kafka namespace..."
  kubectl apply -f "$SCRIPT_DIR/kafka/namespace.yaml"

  print_step "Installing Strimzi Operator..."
  bash "$SCRIPT_DIR/kafka/install-strimzi.sh"

  print_step "Waiting for Strimzi Operator to be ready..."
  kubectl wait --for=condition=Ready pod \
    -l app.kubernetes.io/name=strimzi-cluster-operator \
    -n kafka --timeout=300s || {
    print_error "Strimzi operator failed to start"
    return 1
  }

  print_step "Deploying Kafka cluster..."
  kubectl apply -f "$SCRIPT_DIR/kafka/kafka-cluster.yaml"

  print_step "Waiting for Kafka brokers to be ready (this may take 2-3 minutes)..."
  kubectl wait --for=condition=Ready kafka/kafka-cluster -n kafka --timeout=600s || {
    print_error "Kafka cluster failed to reach ready state"
    return 1
  }

  print_step "Creating Kafka topics..."
  kubectl apply -f "$SCRIPT_DIR/kafka/kafka-topics.yaml"

  print_success "Kafka infrastructure is ready"
  KAFKA_READY=true
  save_setup_state
}

phase_3_dapr() {
  print_header "Phase 3: Dapr Control Plane Setup"

  if [ "$DAPR_READY" = "true" ]; then
    print_info "Skipping Phase 3 (already completed)"
    return 0
  fi

  print_step "Creating Dapr system namespace..."
  kubectl apply -f "$SCRIPT_DIR/dapr/dapr-system-namespace.yaml"

  print_step "Installing Dapr control plane..."
  bash "$SCRIPT_DIR/dapr/install-dapr.sh"

  print_step "Waiting for Dapr control plane to be ready..."
  kubectl wait --for=condition=Ready pod \
    -l app=dapr-operator \
    -n dapr-system --timeout=300s || {
    print_error "Dapr control plane failed to start"
    return 1
  }

  print_step "Deploying Dapr components..."
  kubectl apply -f "$SCRIPT_DIR/dapr/components/"

  print_step "Enabling sidecar injection on default namespace..."
  kubectl label namespace default dapr.io/enabled=true --overwrite

  print_success "Dapr control plane is ready"
  DAPR_READY=true
  save_setup_state
}

phase_4_credentials() {
  print_header "Phase 4: Credentials and Secrets Configuration"

  if [ "$CREDENTIALS_READY" = "true" ]; then
    print_info "Skipping Phase 4 (already completed)"
    return 0
  fi

  print_warning "IMPORTANT: You must provide credentials before deploying applications"
  print_info "Required secrets:"
  print_info "  1. postgres-credentials (PostgreSQL connection string)"
  print_info "  2. auth-secrets (Better Auth secret)"
  echo ""

  # Check if secrets already exist
  if kubectl get secret postgres-credentials -n default &> /dev/null; then
    print_info "postgres-credentials secret already exists"
  else
    print_step "Creating postgres-credentials secret..."
    read -p "Enter PostgreSQL connection string: " db_url
    if [ -z "$db_url" ]; then
      print_error "PostgreSQL connection string is required"
      return 1
    fi
    kubectl create secret generic postgres-credentials \
      --from-literal=connection-string="$db_url" \
      -n default
    print_success "postgres-credentials secret created"
  fi

  if kubectl get secret auth-secrets -n default &> /dev/null; then
    print_info "auth-secrets secret already exists"
  else
    print_step "Creating auth-secrets secret..."
    read -sp "Enter Better Auth secret: " auth_secret
    echo ""
    if [ -z "$auth_secret" ]; then
      print_error "Better Auth secret is required"
      return 1
    fi
    kubectl create secret generic auth-secrets \
      --from-literal=better-auth-secret="$auth_secret" \
      -n default
    print_success "auth-secrets secret created"
  fi

  print_success "Credentials configured"
  CREDENTIALS_READY=true
  save_setup_state
}

phase_5_backend() {
  print_header "Phase 5: Backend and Frontend Deployment"

  if [ "$BACKEND_READY" = "true" ]; then
    print_info "Skipping Phase 5 (already completed)"
    return 0
  fi

  print_step "Deploying backend service..."
  kubectl apply -f "$SCRIPT_DIR/backend/backend-deployment.yaml"

  print_step "Deploying frontend service..."
  kubectl apply -f "$SCRIPT_DIR/frontend/frontend-deployment.yaml"

  print_step "Waiting for backend to be ready..."
  kubectl wait --for=condition=Ready pod \
    -l app=backend \
    -n default --timeout=300s || {
    print_warning "Backend pod is still starting, continuing..."
  }

  print_step "Waiting for frontend to be ready..."
  kubectl wait --for=condition=Ready pod \
    -l app=frontend \
    -n default --timeout=300s || {
    print_warning "Frontend pod is still starting, continuing..."
  }

  print_success "Backend and frontend deployed"
  BACKEND_READY=true
  save_setup_state
}

phase_6_workers() {
  print_header "Phase 6: Event Consumer Workers Deployment"

  if [ "$WORKERS_READY" = "true" ]; then
    print_info "Skipping Phase 6 (already completed)"
    return 0
  fi

  print_step "Deploying recurring-consumer worker..."
  kubectl apply -f "$SCRIPT_DIR/workers/recurring-consumer-deployment.yaml"

  print_step "Deploying notification-consumer worker..."
  kubectl apply -f "$SCRIPT_DIR/workers/notification-consumer-deployment.yaml"

  print_step "Deploying audit-consumer worker..."
  kubectl apply -f "$SCRIPT_DIR/workers/audit-consumer-deployment.yaml"

  print_step "Deploying websocket-consumer worker..."
  kubectl apply -f "$SCRIPT_DIR/workers/websocket-consumer-deployment.yaml"

  print_step "Waiting for workers to be ready..."
  kubectl wait --for=condition=Ready pod \
    -l component=event-consumer \
    -n default --timeout=300s || {
    print_warning "Some workers are still starting, continuing..."
  }

  print_success "Event consumer workers deployed"
  WORKERS_READY=true
  save_setup_state
}

verify_deployment() {
  print_header "Verifying Complete Deployment"

  print_step "Checking Minikube status..."
  minikube status || return 1

  print_step "Checking Kafka cluster..."
  kubectl get kafka -n kafka || return 1

  print_step "Checking Dapr control plane..."
  kubectl get pods -n dapr-system | grep dapr || return 1

  print_step "Checking all deployments..."
  kubectl get deployments -n default

  print_step "Checking all pods..."
  kubectl get pods -n default

  print_success "Deployment verification complete"
}

print_next_steps() {
  print_header "Setup Complete! 🎉"

  print_info "Your local Kubernetes environment is now ready"
  print_info "Next steps:"
  echo ""
  echo "1. Access the frontend:"
  echo "   kubectl port-forward svc/frontend 3000:3000"
  echo "   Then open: http://localhost:3000"
  echo ""
  echo "2. Access the backend API:"
  echo "   kubectl port-forward svc/backend 8000:8000"
  echo "   Then open: http://localhost:8000/docs"
  echo ""
  echo "3. View logs for a service:"
  echo "   kubectl logs -f deployment/backend"
  echo "   kubectl logs -f deployment/recurring-consumer"
  echo ""
  echo "4. Run verification scripts:"
  echo "   bash k8s/verify/verify-all.sh"
  echo ""
  echo "5. To tear down the cluster:"
  echo "   bash k8s/minikube/teardown.sh"
  echo ""
}

main() {
  print_header "Spec-007 Local Event Architecture Setup"

  print_info "This script will set up a complete local Kubernetes environment"
  print_info "Setup will take 10-15 minutes (mostly waiting for services to start)"
  echo ""

  # Check prerequisites
  if ! check_all_prerequisites; then
    return 1
  fi

  load_setup_state

  # Execute phases in order
  phase_1_minikube || return 1
  phase_2_kafka || return 1
  phase_3_dapr || return 1
  phase_4_credentials || return 1
  phase_5_backend || return 1
  phase_6_workers || return 1

  verify_deployment
  print_next_steps

  print_success "Setup complete!"
}

# Handle script termination
trap 'print_error "Setup interrupted"; exit 1' INT TERM

# Run main function
main
