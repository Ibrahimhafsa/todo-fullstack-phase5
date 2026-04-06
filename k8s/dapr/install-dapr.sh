#!/bin/bash
################################################################################
# Dapr Installation Script for Kubernetes
################################################################################
# This script installs Dapr in Kubernetes mode with sidecar injection enabled.
# Dapr provides a Pub/Sub abstraction layer over Kafka and other components.
#
# Prerequisites:
#   - Minikube cluster running with Kafka deployed
#   - kubectl configured
#   - Helm installed
#
# Usage:
#   bash k8s/dapr/install-dapr.sh
################################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DAPR_VERSION="1.11.0"
DAPR_NAMESPACE="dapr-system"

echo -e "${YELLOW}=== Installing Dapr in Kubernetes ===${NC}"
echo "Version: $DAPR_VERSION"
echo "Namespace: $DAPR_NAMESPACE"
echo ""

# Check kubectl connection
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}✗ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Check if Dapr CLI is installed
if ! command -v dapr &> /dev/null; then
    echo -e "${YELLOW}⚠ Dapr CLI not found, installing...${NC}"
    curl -s https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash
fi

echo -e "${YELLOW}Step 1: Creating dapr-system namespace...${NC}"
kubectl apply -f k8s/dapr/dapr-system-namespace.yaml

echo ""
echo -e "${YELLOW}Step 2: Adding Dapr Helm repository...${NC}"
helm repo add dapr https://dapr.github.io/helm-charts || true
helm repo update

echo ""
echo -e "${YELLOW}Step 3: Installing Dapr control plane...${NC}"
helm install dapr dapr/dapr \
    --namespace "$DAPR_NAMESPACE" \
    --version "$DAPR_VERSION" \
    --set global.logLevel=info \
    --set global.serviceAccount.create=true \
    --set dapr_sidecar_injector.enabled=true \
    --set dapr_sidecar_injector.replicaCount=1

echo ""
echo -e "${YELLOW}Step 4: Waiting for Dapr services...${NC}"
kubectl wait --for=condition=ready pod \
    -l app=dapr-sidecar-injector \
    -n "$DAPR_NAMESPACE" \
    --timeout=300s 2>/dev/null || true

echo ""
echo -e "${YELLOW}Step 5: Configuring sidecar injection...${NC}"
kubectl label namespace default dapr.io/enabled=true || true

echo ""
echo -e "${GREEN}✓ Dapr installed successfully${NC}"
echo ""
echo "Next steps:"
echo "  1. Review k8s/dapr/components/ YAML files"
echo "  2. Fill in credential placeholders in the component files"
echo "  3. Run: kubectl apply -f k8s/dapr/components/"
echo ""
echo "To verify Dapr installation:"
echo "  dapr status -k --runtime-version v$DAPR_VERSION"
