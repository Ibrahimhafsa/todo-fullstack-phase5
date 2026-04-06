#!/bin/bash
################################################################################
# Strimzi Kafka Operator Installation Script
################################################################################
# This script installs the Strimzi operator in the kafka namespace.
# Strimzi provides Kubernetes-native Kafka management via Custom Resources.
#
# Prerequisites:
#   - Minikube cluster running
#   - kubectl configured
#
# Usage:
#   bash k8s/kafka/install-strimzi.sh
################################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

STRIMZI_VERSION="0.35.0"
NAMESPACE="kafka"

echo -e "${YELLOW}=== Installing Strimzi Kafka Operator ===${NC}"
echo "Version: $STRIMZI_VERSION"
echo "Namespace: $NAMESPACE"
echo ""

# Check kubectl connection
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}✗ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Creating kafka namespace...${NC}"
kubectl apply -f k8s/kafka/namespace.yaml

echo ""
echo -e "${YELLOW}Step 2: Installing Strimzi operator...${NC}"
# Using official Strimzi Helm repository
helm repo add strimzi https://strimzi.io/charts || true
helm repo update

helm install strimzi-operator strimzi/strimzi-kafka-operator \
    --namespace "$NAMESPACE" \
    --version "$STRIMZI_VERSION" \
    --set watchAnyNamespace=false \
    --set operationTimeoutMs=600000

echo ""
echo -e "${YELLOW}Step 3: Waiting for operator deployment...${NC}"
kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/name=strimzi-cluster-operator \
    -n "$NAMESPACE" \
    --timeout=300s

echo ""
echo -e "${GREEN}✓ Strimzi operator installed successfully${NC}"
echo ""
echo "Next steps:"
echo "  1. Review k8s/kafka/kafka-cluster.yaml configuration"
echo "  2. Run: kubectl apply -f k8s/kafka/kafka-cluster.yaml"
echo "  3. Run: kubectl apply -f k8s/kafka/kafka-topics.yaml"
