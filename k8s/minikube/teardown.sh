#!/bin/bash
################################################################################
# Minikube Teardown Script
################################################################################
# This script cleanly deletes the Minikube cluster and resets the environment.
#
# Usage:
#   bash k8s/minikube/teardown.sh
################################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CLUSTER_NAME="minikube"

echo -e "${YELLOW}=== Minikube Teardown ===${NC}"
echo "This will delete the Minikube cluster and all data."
echo ""
read -p "Are you sure? (yes/no): " -r response

if [[ ! "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Deleting Minikube cluster: $CLUSTER_NAME${NC}"

if minikube status -p "$CLUSTER_NAME" &> /dev/null; then
    minikube delete -p "$CLUSTER_NAME"
    echo -e "${GREEN}✓ Cluster deleted${NC}"
else
    echo -e "${YELLOW}⚠ Cluster not found or already deleted${NC}"
fi

echo ""
echo -e "${YELLOW}Resetting kubectl context...${NC}"
# Try to reset context if other clusters exist
if kubectl config get-contexts -o name | grep -q .; then
    FIRST_CONTEXT=$(kubectl config get-contexts -o name | head -1)
    kubectl config use-context "$FIRST_CONTEXT" || true
fi

echo -e "${GREEN}=== Teardown Complete ===${NC}"
