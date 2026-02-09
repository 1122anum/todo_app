#!/bin/bash
# Dapr Installation Script for Event-Driven Todo Platform
# This script installs Dapr runtime on Kubernetes cluster

set -e

echo "=========================================="
echo "Installing Dapr Runtime on Kubernetes"
echo "=========================================="

# Check if dapr CLI is installed
if ! command -v dapr &> /dev/null; then
    echo "Error: Dapr CLI is not installed."
    echo "Please install Dapr CLI first: https://docs.dapr.io/getting-started/install-dapr-cli/"
    exit 1
fi

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: kubectl is not configured or cluster is not accessible."
    exit 1
fi

echo "Dapr CLI version:"
dapr version

echo ""
echo "Installing Dapr on Kubernetes cluster..."
dapr init -k

echo ""
echo "Waiting for Dapr components to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=dapr -n dapr-system --timeout=300s

echo ""
echo "Verifying Dapr installation..."
dapr status -k

echo ""
echo "=========================================="
echo "Dapr Runtime Installation Complete!"
echo "=========================================="
echo ""
echo "Dapr components installed:"
echo "  - dapr-operator"
echo "  - dapr-sidecar-injector"
echo "  - dapr-sentry (mTLS)"
echo "  - dapr-placement"
echo ""
echo "Next steps:"
echo "  1. Create Dapr components (Pub/Sub, State Management, Secrets, Bindings)"
echo "  2. Deploy application services with Dapr sidecars"
