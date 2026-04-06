#!/bin/bash
# Diagnostic Script for Spec-007 Local Event Architecture
# This script gathers detailed diagnostic information for troubleshooting

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DIAG_DIR="./diagnostics_${TIMESTAMP}"

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

# Create diagnostics directory
mkdir -p "$DIAG_DIR"

# Diagnostics functions
diagnose_system() {
  print_section "System Information"
  {
    echo "=== System Info ==="
    uname -a
    echo ""
    echo "=== Docker Info ==="
    docker version 2>&1 || echo "Docker not available or not running"
    echo ""
    echo "=== Disk Space ==="
    df -h
    echo ""
    echo "=== Memory ==="
    free -h 2>/dev/null || vm_stat 2>/dev/null || echo "Memory info not available"
  } | tee "${DIAG_DIR}/01-system-info.txt"
}

diagnose_minikube() {
  print_section "Minikube Diagnostics"
  {
    echo "=== Minikube Status ==="
    minikube status 2>&1 || echo "Minikube not running or not installed"
    echo ""
    echo "=== Minikube Config ==="
    minikube config view 2>&1 || echo "Could not get Minikube config"
    echo ""
    echo "=== Minikube Logs (last 100 lines) ==="
    minikube logs 2>&1 | tail -100 || echo "Could not get Minikube logs"
  } | tee "${DIAG_DIR}/02-minikube-diagnostics.txt"
}

diagnose_kubernetes() {
  print_section "Kubernetes Cluster Diagnostics"
  {
    echo "=== Cluster Info ==="
    kubectl cluster-info 2>&1 || echo "Could not get cluster info"
    echo ""
    echo "=== Nodes ==="
    kubectl get nodes -o wide 2>&1 || echo "Could not get nodes"
    echo ""
    echo "=== Node Status Details ==="
    kubectl describe nodes 2>&1 || echo "Could not describe nodes"
    echo ""
    echo "=== Resource Usage ==="
    kubectl top nodes 2>&1 || echo "Metrics not available"
    echo ""
    echo "=== Kubelet Logs ==="
    kubectl logs -n kube-system -l component=kubelet --tail=50 2>&1 || echo "Could not get kubelet logs"
  } | tee "${DIAG_DIR}/03-kubernetes-diagnostics.txt"
}

diagnose_namespaces() {
  print_section "Namespace Diagnostics"
  {
    echo "=== All Namespaces ==="
    kubectl get namespaces -o wide 2>&1 || echo "Could not list namespaces"
    echo ""
    echo "=== Default Namespace ==="
    kubectl describe namespace default 2>&1 || echo "Could not describe default namespace"
    echo ""
    echo "=== Kafka Namespace ==="
    kubectl describe namespace kafka 2>&1 || echo "Kafka namespace not found"
    echo ""
    echo "=== Dapr System Namespace ==="
    kubectl describe namespace dapr-system 2>&1 || echo "Dapr system namespace not found"
  } | tee "${DIAG_DIR}/04-namespace-diagnostics.txt"
}

diagnose_kafka() {
  print_section "Kafka Diagnostics"
  {
    echo "=== Strimzi Operator ==="
    kubectl get deployment -n kafka 2>&1 || echo "Could not get Kafka deployments"
    echo ""
    echo "=== Strimzi Operator Logs (last 50 lines) ==="
    kubectl logs -n kafka -l app.kubernetes.io/name=strimzi-cluster-operator --tail=50 2>&1 || echo "Could not get Strimzi logs"
    echo ""
    echo "=== Kafka Cluster Status ==="
    kubectl get kafka -n kafka -o yaml 2>&1 || echo "Could not get Kafka cluster"
    echo ""
    echo "=== Kafka Brokers ==="
    kubectl get pods -n kafka -l strimzi.io/kind=Kafka 2>&1 || echo "Could not list Kafka brokers"
    echo ""
    echo "=== Kafka Topics ==="
    kubectl get kafkatopics -n kafka 2>&1 || echo "Could not list Kafka topics"
    echo ""
    echo "=== Kafka Broker Logs (last 50 lines from first broker) ==="
    first_broker=$(kubectl get pods -n kafka -l strimzi.io/kind=Kafka -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$first_broker" ]; then
      kubectl logs -n kafka "$first_broker" --tail=50 2>&1 || echo "Could not get broker logs"
    else
      echo "No Kafka brokers found"
    fi
  } | tee "${DIAG_DIR}/05-kafka-diagnostics.txt"
}

diagnose_dapr() {
  print_section "Dapr Diagnostics"
  {
    echo "=== Dapr System Namespace Pods ==="
    kubectl get pods -n dapr-system -o wide 2>&1 || echo "Dapr system not found"
    echo ""
    echo "=== Dapr Control Plane Components ==="
    kubectl get deployments -n dapr-system 2>&1 || echo "Could not get Dapr deployments"
    echo ""
    echo "=== Dapr Operator Logs (last 50 lines) ==="
    kubectl logs -n dapr-system -l app=dapr-operator --tail=50 2>&1 || echo "Could not get Dapr operator logs"
    echo ""
    echo "=== Dapr Sentry Logs (last 50 lines) ==="
    kubectl logs -n dapr-system -l app=dapr-sentry --tail=50 2>&1 || echo "Could not get Dapr sentry logs"
    echo ""
    echo "=== Dapr Components (default namespace) ==="
    kubectl get components -n default 2>&1 || echo "Could not list Dapr components"
    echo ""
    echo "=== Dapr Components Details ==="
    kubectl get components -n default -o yaml 2>&1 || echo "Could not get components details"
  } | tee "${DIAG_DIR}/06-dapr-diagnostics.txt"
}

diagnose_applications() {
  print_section "Application Diagnostics"
  {
    echo "=== Deployments ==="
    kubectl get deployments -n default -o wide 2>&1 || echo "Could not list deployments"
    echo ""
    echo "=== Pods (Wide) ==="
    kubectl get pods -n default -o wide 2>&1 || echo "Could not list pods"
    echo ""
    echo "=== Pod Details ==="
    kubectl describe pods -n default 2>&1 || echo "Could not describe pods"
    echo ""
    echo "=== Services ==="
    kubectl get services -n default -o wide 2>&1 || echo "Could not list services"
    echo ""
    echo "=== Secrets ==="
    kubectl get secrets -n default 2>&1 || echo "Could not list secrets"
    echo ""
    echo "=== ConfigMaps ==="
    kubectl get configmaps -n default 2>&1 || echo "Could not list configmaps"
  } | tee "${DIAG_DIR}/07-applications-diagnostics.txt"
}

diagnose_pod_logs() {
  print_section "Pod Logs"

  # Backend logs
  {
    echo "=== Backend Pod Logs (last 100 lines) ==="
    kubectl logs -n default deployment/backend --tail=100 2>&1 || echo "Could not get backend logs"
  } | tee "${DIAG_DIR}/08-backend-logs.txt"

  # Frontend logs
  {
    echo "=== Frontend Pod Logs (last 100 lines) ==="
    kubectl logs -n default deployment/frontend --tail=100 2>&1 || echo "Could not get frontend logs"
  } | tee "${DIAG_DIR}/09-frontend-logs.txt"

  # Recurring consumer logs
  {
    echo "=== Recurring Consumer Logs (last 100 lines) ==="
    kubectl logs -n default deployment/recurring-consumer --tail=100 2>&1 || echo "Could not get recurring consumer logs"
  } | tee "${DIAG_DIR}/10-recurring-consumer-logs.txt"

  # Notification consumer logs
  {
    echo "=== Notification Consumer Logs (last 100 lines) ==="
    kubectl logs -n default deployment/notification-consumer --tail=100 2>&1 || echo "Could not get notification consumer logs"
  } | tee "${DIAG_DIR}/11-notification-consumer-logs.txt"

  # Audit consumer logs
  {
    echo "=== Audit Consumer Logs (last 100 lines) ==="
    kubectl logs -n default deployment/audit-consumer --tail=100 2>&1 || echo "Could not get audit consumer logs"
  } | tee "${DIAG_DIR}/12-audit-consumer-logs.txt"

  # WebSocket consumer logs
  {
    echo "=== WebSocket Consumer Logs (last 100 lines) ==="
    kubectl logs -n default deployment/websocket-consumer --tail=100 2>&1 || echo "Could not get websocket consumer logs"
  } | tee "${DIAG_DIR}/13-websocket-consumer-logs.txt"
}

diagnose_pod_events() {
  print_section "Pod Events"
  {
    echo "=== All Kubernetes Events (sorted by timestamp) ==="
    kubectl get events -n default --sort-by='.lastTimestamp' 2>&1 || echo "Could not get events"
    echo ""
    echo "=== Recent Events (last 20) ==="
    kubectl get events -n default --sort-by='.lastTimestamp' | tail -20 2>&1 || echo "Could not get recent events"
  } | tee "${DIAG_DIR}/14-events.txt"
}

diagnose_networking() {
  print_section "Network Diagnostics"
  {
    echo "=== Service Endpoints ==="
    kubectl get endpoints -n default 2>&1 || echo "Could not list endpoints"
    echo ""
    echo "=== Network Policies ==="
    kubectl get networkpolicies -n default 2>&1 || echo "No network policies"
    echo ""
    echo "=== DNS Check ==="
    kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup backend.default.svc.cluster.local 2>&1 || echo "DNS check skipped"
  } | tee "${DIAG_DIR}/15-network-diagnostics.txt"
}

diagnose_storage() {
  print_section "Storage Diagnostics"
  {
    echo "=== Storage Classes ==="
    kubectl get storageclass 2>&1 || echo "No storage classes"
    echo ""
    echo "=== Persistent Volumes ==="
    kubectl get pv 2>&1 || echo "No persistent volumes"
    echo ""
    echo "=== Persistent Volume Claims ==="
    kubectl get pvc -A 2>&1 || echo "No persistent volume claims"
  } | tee "${DIAG_DIR}/16-storage-diagnostics.txt"
}

diagnose_resource_usage() {
  print_section "Resource Usage"
  {
    echo "=== Node Resource Usage ==="
    kubectl top nodes 2>&1 || echo "Metrics server not available"
    echo ""
    echo "=== Pod Resource Usage ==="
    kubectl top pods -n default 2>&1 || echo "Could not get pod metrics"
    echo ""
    echo "=== Kafka Pod Resource Usage ==="
    kubectl top pods -n kafka 2>&1 || echo "Could not get Kafka pod metrics"
    echo ""
    echo "=== Dapr Pod Resource Usage ==="
    kubectl top pods -n dapr-system 2>&1 || echo "Could not get Dapr pod metrics"
  } | tee "${DIAG_DIR}/17-resource-usage.txt"
}

diagnose_dapr_sidecars() {
  print_section "Dapr Sidecar Diagnostics"
  {
    echo "=== Backend Sidecar ==="
    backend_pod=$(kubectl get pod -n default -l app=backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$backend_pod" ]; then
      echo "Pod: $backend_pod"
      kubectl exec -n default "$backend_pod" -- curl -s http://localhost:3500/v1.0/healthz 2>&1 || echo "Sidecar health check failed"
    else
      echo "Backend pod not found"
    fi
    echo ""
    echo "=== Recurring Consumer Sidecar ==="
    recurring_pod=$(kubectl get pod -n default -l app=recurring-consumer -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$recurring_pod" ]; then
      echo "Pod: $recurring_pod"
      kubectl exec -n default "$recurring_pod" -- curl -s http://localhost:3500/v1.0/healthz 2>&1 || echo "Sidecar health check failed"
    else
      echo "Recurring consumer pod not found"
    fi
  } | tee "${DIAG_DIR}/18-sidecar-diagnostics.txt"
}

generate_summary() {
  print_section "Generating Summary"
  {
    echo "=== Diagnostic Summary ==="
    echo "Generated: $(date)"
    echo "Diagnostics directory: $DIAG_DIR"
    echo ""
    echo "=== Files Generated ==="
    ls -lh "$DIAG_DIR"
  } | tee "${DIAG_DIR}/00-summary.txt"
}

main() {
  print_header "Spec-007 Local Event Architecture Diagnostic Tool"

  print_info "Collecting diagnostics... This may take a minute"
  print_info "Results will be saved to: $DIAG_DIR"
  echo ""

  diagnose_system
  diagnose_minikube
  diagnose_kubernetes
  diagnose_namespaces
  diagnose_kafka
  diagnose_dapr
  diagnose_applications
  diagnose_pod_logs
  diagnose_pod_events
  diagnose_networking
  diagnose_storage
  diagnose_resource_usage
  diagnose_dapr_sidecars
  generate_summary

  print_header "Diagnostic Complete ✓"

  print_info "Diagnostics saved to: ${GREEN}$DIAG_DIR${NC}"
  echo ""
  print_info "To review the results:"
  echo "  View summary:  less $DIAG_DIR/00-summary.txt"
  echo "  View all files: ls -lh $DIAG_DIR"
  echo "  Search for errors: grep -r 'Error\|error\|failed' $DIAG_DIR"
  echo ""
  print_warning "To share diagnostics, ZIP the directory (contains no secrets):"
  echo "  zip -r diagnostics_${TIMESTAMP}.zip $DIAG_DIR"
  echo ""
}

# Run diagnostics
main
