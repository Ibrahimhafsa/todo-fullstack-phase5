#!/bin/bash
################################################################################
# Minikube Setup Script for Spec-007 Local Event Architecture
################################################################################
# This script initializes a local Minikube Kubernetes cluster with appropriate
# resource allocation for running the complete event-driven todo application.
#
# Prerequisites:
#   - minikube installed (https://minikube.sigs.k8s.io/docs/start/)
#   - kubectl installed (https://kubernetes.io/docs/tasks/tools/)
#   - Docker installed and running
#
# Usage:
#   bash k8s/minikube/setup.sh
################################################################################

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="minikube"
CPUS=4
MEMORY=8192
DISK_SIZE=30GB
KUBERNETES_VERSION="latest"

echo -e "${YELLOW}=== Minikube Setup for Spec-007 ===${NC}"
echo "Configuration:"
echo "  Cluster Name: $CLUSTER_NAME"
echo "  CPUs: $CPUS"
echo "  Memory: ${MEMORY}MB"
echo "  Disk Size: $DISK_SIZE"
echo ""

# Check if minikube is installed
if ! command -v minikube &> /dev/null; then
    echo -e "${RED}✗ minikube is not installed${NC}"
    echo "  Install from: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}✗ kubectl is not installed${NC}"
    echo "  Install from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "  Start Docker and try again"
    exit 1
fi

echo -e "${YELLOW}Step 1: Checking existing cluster...${NC}"
if minikube status -p "$CLUSTER_NAME" &> /dev/null; then
    echo -e "${GREEN}✓ Cluster exists, deleting...${NC}"
    minikube delete -p "$CLUSTER_NAME" || true
fi

echo ""
echo -e "${YELLOW}Step 2: Creating Minikube cluster...${NC}"
minikube start \
    --profile="$CLUSTER_NAME" \
    --cpus="$CPUS" \
    --memory="$MEMORY" \
    --disk-size="$DISK_SIZE" \
    --kubernetes-version="$KUBERNETES_VERSION" \
    --driver=docker \
    --container-runtime=docker \
    --wait=all

echo ""
echo -e "${YELLOW}Step 3: Enabling required addons...${NC}"
minikube addons enable -p "$CLUSTER_NAME" ingress || true
minikube addons enable -p "$CLUSTER_NAME" metrics-server || true
minikube addons enable -p "$CLUSTER_NAME" storage-provisioner || true

echo ""
echo -e "${YELLOW}Step 4: Configuring kubectl context...${NC}"
kubectl config use-context "$CLUSTER_NAME"

echo ""
echo -e "${YELLOW}Step 5: Verifying cluster health...${NC}"
if kubectl get nodes -o wide &> /dev/null; then
    echo -e "${GREEN}✓ Cluster is healthy${NC}"
    kubectl get nodes -o wide
else
    echo -e "${RED}✗ Cluster health check failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Minikube Setup Complete ===${NC}"
echo "Next steps:"
echo "  1. Run: bash k8s/kafka/install-strimzi.sh"
echo "  2. Run: bash k8s/dapr/install-dapr.sh"
echo ""
echo "To delete the cluster later, run:"
echo "  minikube delete -p $CLUSTER_NAME"
