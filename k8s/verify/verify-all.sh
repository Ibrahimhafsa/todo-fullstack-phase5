#!/bin/bash
# Master Verification Script for Spec-007 Local Event Architecture
# Validates all components of the deployment

set -e

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

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNED=0

# Functions
print_header() {
  echo -e "\n${MAGENTA}========================================${NC}"
  echo -e "${MAGENTA}$1${NC}"
  echo -e "${MAGENTA}========================================${NC}\n"
}

print_section() {
  echo -e "\n${CYAN}--- $1 ---${NC}"
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
  ((CHECKS_PASSED++))
}

print_error() {
  echo -e "${RED}✗ $1${NC}"
  ((CHECKS_FAILED++))
}

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
  ((CHECKS_WARNED++))
}

print_info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

# Verification functions
verify_minikube() {
  print_section "Minikube Status"

  if ! command -v minikube &> /dev/null; then
    print_error "Minikube is not installed"
    return 1
  fi

  local status=$(minikube status 2>&1 || true)

  if echo "$status" | grep -q "host: Running"; then
    print_success "Minikube host is running"
  else
    print_error "Minikube host is not running"
    return 1
  fi

  if echo "$status" | grep -q "kubelet: Running"; then
    print_success "Kubelet is running"
  else
    print_error "Kubelet is not running"
    return 1
  fi

  if echo "$status" | grep -q "kubectl: Correctly Configured"; then
    print_success "Kubectl is correctly configured"
  else
    print_warning "Kubectl may not be correctly configured"
  fi
}

verify_kubernetes() {
  print_section "Kubernetes Cluster"

  # Check cluster info
  if kubectl cluster-info &> /dev/null; then
    print_success "Kubernetes cluster is accessible"
  else
    print_error "Cannot access Kubernetes cluster"
    return 1
  fi

  # Check node status
  local nodes=$(kubectl get nodes -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)
  if [ -z "$nodes" ]; then
    print_error "No nodes found in cluster"
    return 1
  fi

  local ready_nodes=$(kubectl get nodes --no-headers 2>/dev/null | grep -c "Ready" || echo "0")
  if [ "$ready_nodes" -gt 0 ]; then
    print_success "Found $ready_nodes ready node(s)"
  else
    print_error "No ready nodes found"
    return 1
  fi
}

verify_namespaces() {
  print_section "Kubernetes Namespaces"

  for ns in default kafka dapr-system; do
    if kubectl get namespace "$ns" &> /dev/null; then
      print_success "Namespace '$ns' exists"
    else
      print_warning "Namespace '$ns' not found"
    fi
  done
}

verify_kafka() {
  print_section "Kafka Deployment"

  # Check Strimzi operator
  local strimzi_pods=$(kubectl get pods -n kafka -l app.kubernetes.io/name=strimzi-cluster-operator 2>/dev/null | grep -c "Running" || echo "0")
  if [ "$strimzi_pods" -gt 0 ]; then
    print_success "Strimzi operator is running"
  else
    print_warning "Strimzi operator not found or not running"
  fi

  # Check Kafka cluster
  local kafka_status=$(kubectl get kafka -n kafka -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "")
  if [ "$kafka_status" = "True" ]; then
    print_success "Kafka cluster is ready"
  else
    print_warning "Kafka cluster is not ready (may still be starting)"
  fi

  # Check brokers
  local kafka_brokers=$(kubectl get pods -n kafka -l strimzi.io/kind=Kafka -o jsonpath='{.items[*].metadata.name}' 2>/dev/null | wc -w)
  if [ "$kafka_brokers" -gt 0 ]; then
    print_success "Found $kafka_brokers Kafka broker(s)"
  else
    print_warning "No Kafka brokers found"
  fi

  # Check topics
  print_info "Kafka topics:"
  kubectl get kafkatopics -n kafka 2>/dev/null | awk 'NR>1 {print "  - " $1 " (" $2 " partitions)"}' || print_warning "Could not retrieve Kafka topics"
}

verify_dapr() {
  print_section "Dapr Control Plane"

  # Check Dapr namespace
  if ! kubectl get namespace dapr-system &> /dev/null; then
    print_warning "Dapr system namespace not found"
    return 1
  fi

  # Check Dapr operator
  local dapr_operator=$(kubectl get pods -n dapr-system -l app=dapr-operator 2>/dev/null | grep -c "Running" || echo "0")
  if [ "$dapr_operator" -gt 0 ]; then
    print_success "Dapr operator is running"
  else
    print_warning "Dapr operator not found"
  fi

  # Check Dapr sentry
  local dapr_sentry=$(kubectl get pods -n dapr-system -l app=dapr-sentry 2>/dev/null | grep -c "Running" || echo "0")
  if [ "$dapr_sentry" -gt 0 ]; then
    print_success "Dapr sentry is running"
  else
    print_warning "Dapr sentry not found"
  fi

  # Check Dapr placement
  local dapr_placement=$(kubectl get pods -n dapr-system -l app=dapr-placement-server 2>/dev/null | grep -c "Running" || echo "0")
  if [ "$dapr_placement" -gt 0 ]; then
    print_success "Dapr placement service is running"
  else
    print_warning "Dapr placement service not found"
  fi
}

verify_dapr_components() {
  print_section "Dapr Components"

  print_info "Checking Dapr components in default namespace:"

  # Check kafka-pubsub
  local kafka_pubsub=$(kubectl get components -n default -o jsonpath='{.items[?(@.metadata.name=="kafka-pubsub")].status.state}' 2>/dev/null)
  if [ "$kafka_pubsub" = "RUNNING" ]; then
    print_success "kafka-pubsub component is running"
  elif [ -z "$kafka_pubsub" ]; then
    print_warning "kafka-pubsub component not found"
  else
    print_warning "kafka-pubsub component state: $kafka_pubsub"
  fi

  # Check postgres-statestore
  local postgres=$(kubectl get components -n default -o jsonpath='{.items[?(@.metadata.name=="postgres-statestore")].status.state}' 2>/dev/null)
  if [ "$postgres" = "RUNNING" ]; then
    print_success "postgres-statestore component is running"
  elif [ -z "$postgres" ]; then
    print_warning "postgres-statestore component not found"
  else
    print_warning "postgres-statestore component state: $postgres"
  fi

  # Check kubernetes-secrets
  local k8s_secrets=$(kubectl get components -n default -o jsonpath='{.items[?(@.metadata.name=="kubernetes-secrets")].status.state}' 2>/dev/null)
  if [ "$k8s_secrets" = "RUNNING" ]; then
    print_success "kubernetes-secrets component is running"
  elif [ -z "$k8s_secrets" ]; then
    print_warning "kubernetes-secrets component not found"
  else
    print_warning "kubernetes-secrets component state: $k8s_secrets"
  fi
}

verify_secrets() {
  print_section "Kubernetes Secrets"

  # Check postgres-credentials
  if kubectl get secret postgres-credentials -n default &> /dev/null; then
    print_success "postgres-credentials secret exists"
  else
    print_warning "postgres-credentials secret not found (required for backend)"
  fi

  # Check auth-secrets
  if kubectl get secret auth-secrets -n default &> /dev/null; then
    print_success "auth-secrets secret exists"
  else
    print_warning "auth-secrets secret not found (required for backend)"
  fi
}

verify_backend() {
  print_section "Backend Service"

  # Check deployment
  local backend_replicas=$(kubectl get deployment backend -n default -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
  if [ "$backend_replicas" -gt 0 ]; then
    print_success "Backend deployment has $backend_replicas ready replica(s)"
  else
    print_warning "Backend deployment has no ready replicas (may still be starting)"
  fi

  # Check service
  if kubectl get service backend -n default &> /dev/null; then
    print_success "Backend service exists"
    local backend_ip=$(kubectl get service backend -n default -o jsonpath='{.spec.clusterIP}')
    print_info "Backend service IP: $backend_ip:8000"
  else
    print_warning "Backend service not found"
  fi

  # Check Dapr sidecar
  local dapr_sidecars=$(kubectl get pods -n default -l app=backend -o jsonpath='{.items[*].spec.containers[?(@.name=="daprd")].name}' 2>/dev/null | wc -w)
  if [ "$dapr_sidecars" -gt 0 ]; then
    print_success "Backend pod has Dapr sidecar"
  else
    print_warning "Backend pod may not have Dapr sidecar"
  fi
}

verify_frontend() {
  print_section "Frontend Service"

  # Check deployment
  local frontend_replicas=$(kubectl get deployment frontend -n default -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
  if [ "$frontend_replicas" -gt 0 ]; then
    print_success "Frontend deployment has $frontend_replicas ready replica(s)"
  else
    print_warning "Frontend deployment has no ready replicas (may still be starting)"
  fi

  # Check service
  if kubectl get service frontend -n default &> /dev/null; then
    print_success "Frontend service exists"
    local frontend_ip=$(kubectl get service frontend -n default -o jsonpath='{.spec.clusterIP}')
    print_info "Frontend service IP: $frontend_ip:3000"
  else
    print_warning "Frontend service not found"
  fi
}

verify_workers() {
  print_section "Event Consumer Workers"

  local workers=("recurring-consumer" "notification-consumer" "audit-consumer" "websocket-consumer")

  for worker in "${workers[@]}"; do
    local replicas=$(kubectl get deployment "$worker" -n default -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    if [ "$replicas" -gt 0 ]; then
      print_success "Worker '$worker' has $replicas ready replica(s)"
    else
      print_warning "Worker '$worker' has no ready replicas (may still be starting)"
    fi
  done
}

verify_pod_status() {
  print_section "Pod Status Summary"

  print_info "All pods in default namespace:"
  kubectl get pods -n default --no-headers 2>/dev/null | awk '{
    if ($3 ~ /^[0-9]+\/[0-9]+$/) {
      parts = split($3, a, "/")
      if (a[1] == a[2]) {
        status = "✓ Ready"
      } else {
        status = "⚠ Not Ready"
      }
    }
    printf "  %s %s (%s)\n", status, $1, $5
  }'

  print_info "All pods in kafka namespace:"
  kubectl get pods -n kafka --no-headers 2>/dev/null | awk '{
    if ($3 ~ /^[0-9]+\/[0-9]+$/) {
      parts = split($3, a, "/")
      if (a[1] == a[2]) {
        status = "✓ Ready"
      } else {
        status = "⚠ Not Ready"
      }
    }
    printf "  %s %s (%s)\n", status, $1, $5
  }' || print_info "  (Kafka namespace may not exist yet)"

  print_info "All pods in dapr-system namespace:"
  kubectl get pods -n dapr-system --no-headers 2>/dev/null | awk '{
    if ($3 ~ /^[0-9]+\/[0-9]+$/) {
      parts = split($3, a, "/")
      if (a[1] == a[2]) {
        status = "✓ Ready"
      } else {
        status = "⚠ Not Ready"
      }
    }
    printf "  %s %s (%s)\n", status, $1, $5
  }' || print_info "  (Dapr system namespace may not exist yet)"
}

print_summary() {
  print_header "Verification Summary"

  echo "Checks Passed: ${GREEN}$CHECKS_PASSED${NC}"
  echo "Checks Failed: ${RED}$CHECKS_FAILED${NC}"
  echo "Warnings:     ${YELLOW}$CHECKS_WARNED${NC}"

  if [ "$CHECKS_FAILED" -eq 0 ]; then
    print_success "All critical checks passed!"
    echo ""
    print_info "Your Spec-007 Local Event Architecture is ready to use"
  else
    print_error "Some critical checks failed"
    echo ""
    print_info "Please review the errors above and troubleshoot accordingly"
  fi
}

main() {
  print_header "Spec-007 Local Event Architecture Verification"

  verify_minikube || true
  verify_kubernetes || true
  verify_namespaces || true
  verify_kafka || true
  verify_dapr || true
  verify_dapr_components || true
  verify_secrets || true
  verify_backend || true
  verify_frontend || true
  verify_workers || true
  verify_pod_status

  print_summary
}

# Run verification
main
