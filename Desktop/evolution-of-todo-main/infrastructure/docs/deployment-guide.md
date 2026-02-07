# Kubernetes Deployment Guide

**Purpose**: Step-by-step guide for deploying the Todo Chatbot application to local Kubernetes cluster

**Last Updated**: 2026-02-06

## Prerequisites

### Required Software
- **Minikube**: Local Kubernetes cluster (minimum version 1.25)
- **Docker**: Container runtime (minimum version 20.10)
- **kubectl**: Kubernetes CLI (minimum version 1.25)
- **Helm**: Kubernetes package manager (version 3.x)

### System Requirements
- **CPU**: Minimum 2 cores
- **Memory**: Minimum 4GB RAM
- **Disk**: Minimum 20GB free space
- **OS**: Windows 10/11, macOS 10.15+, or Linux

### Verification
```bash
# Check Minikube
minikube version

# Check Docker
docker --version

# Check kubectl
kubectl version --client

# Check Helm
helm version
```

---

## Quick Start (5 Minutes)

### Step 1: Start Minikube
```bash
minikube start --cpus=2 --memory=4096
```

**Expected Output**: Minikube cluster starts successfully

### Step 2: Configure Docker Environment
```bash
# Windows (PowerShell)
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# macOS/Linux (Bash)
eval $(minikube docker-env)
```

**Expected Output**: Docker environment configured to use Minikube's Docker daemon

### Step 3: Build Container Images
```bash
# Build frontend image
docker build -t todo-frontend:latest -f infrastructure/docker/frontend/Dockerfile ./frontend

# Build backend image
docker build -t todo-backend:latest -f infrastructure/docker/backend/Dockerfile ./backend
```

**Expected Output**: Both images build successfully without errors

### Step 4: Deploy to Kubernetes
```bash
# Apply ConfigMap and Secrets
kubectl apply -f infrastructure/kubernetes/base/configmap.yaml
kubectl apply -f infrastructure/kubernetes/base/secrets.yaml

# Deploy backend
kubectl apply -f infrastructure/kubernetes/base/backend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/base/backend-service.yaml

# Deploy frontend
kubectl apply -f infrastructure/kubernetes/base/frontend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/base/frontend-service.yaml
```

**Expected Output**: All resources created successfully

### Step 5: Verify Deployment
```bash
# Check pod status (wait for Running)
kubectl get pods

# Check services
kubectl get services

# Get frontend URL
minikube service todo-frontend --url
```

**Expected Output**: All pods Running, services have endpoints, frontend URL displayed

### Step 6: Access Application
Open the frontend URL in your browser. The Todo Chatbot UI should load successfully.

---

## Detailed Deployment Steps

### Phase 1: Environment Setup

#### 1.1 Install Minikube
**Windows**:
```powershell
choco install minikube
```

**macOS**:
```bash
brew install minikube
```

**Linux**:
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

#### 1.2 Start Minikube Cluster
```bash
minikube start --cpus=2 --memory=4096 --driver=docker
```

**Options**:
- `--cpus`: Number of CPU cores (minimum 2)
- `--memory`: Memory allocation in MB (minimum 4096)
- `--driver`: Virtualization driver (docker, virtualbox, hyperv)

**Troubleshooting**:
- If driver fails, try different driver: `--driver=virtualbox` or `--driver=hyperv`
- If memory error, increase allocation: `--memory=8192`

#### 1.3 Verify Cluster
```bash
kubectl cluster-info
kubectl get nodes
```

**Expected Output**:
```
Kubernetes control plane is running at https://...
minikube   Ready    control-plane   1m   v1.28.0
```

---

### Phase 2: Container Image Build

#### 2.1 Configure Docker Environment
```bash
# Use Minikube's Docker daemon
eval $(minikube docker-env)

# Verify configuration
docker ps
```

**Why**: Building images in Minikube's Docker daemon avoids image push/pull overhead

#### 2.2 Build Frontend Image
```bash
cd frontend
docker build -t todo-frontend:latest -f ../infrastructure/docker/frontend/Dockerfile .
```

**Validation**:
```bash
docker images | grep todo-frontend
```

#### 2.3 Build Backend Image
```bash
cd backend
docker build -t todo-backend:latest -f ../infrastructure/docker/backend/Dockerfile .
```

**Validation**:
```bash
docker images | grep todo-backend
```

#### 2.4 Test Containers Locally (Optional)
```bash
# Test frontend
docker run -p 3000:3000 todo-frontend:latest

# Test backend
docker run -p 8000:8000 todo-backend:latest
```

---

### Phase 3: Kubernetes Deployment

#### 3.1 Create ConfigMap
```bash
kubectl apply -f infrastructure/kubernetes/base/configmap.yaml
kubectl get configmap
```

**Purpose**: Store non-sensitive configuration (backend URL, feature flags)

#### 3.2 Create Secrets
```bash
kubectl apply -f infrastructure/kubernetes/base/secrets.yaml
kubectl get secrets
```

**Purpose**: Store sensitive configuration (database credentials, API keys)

**Security Note**: Secrets should be base64 encoded in the YAML file

#### 3.3 Deploy Backend
```bash
# Create deployment
kubectl apply -f infrastructure/kubernetes/base/backend-deployment.yaml

# Create service
kubectl apply -f infrastructure/kubernetes/base/backend-service.yaml

# Verify
kubectl get pods -l app=todo-backend
kubectl get svc todo-backend
```

**Expected**: Backend pod Running, service has endpoints

#### 3.4 Deploy Frontend
```bash
# Create deployment
kubectl apply -f infrastructure/kubernetes/base/frontend-deployment.yaml

# Create service
kubectl apply -f infrastructure/kubernetes/base/frontend-service.yaml

# Verify
kubectl get pods -l app=todo-frontend
kubectl get svc todo-frontend
```

**Expected**: Frontend pod Running, service has endpoints

---

### Phase 4: Validation

#### 4.1 Check Pod Status
```bash
kubectl get pods
kubectl describe pod <pod-name>
```

**Expected**: All pods in Running state, no errors in events

#### 4.2 Check Logs
```bash
# Backend logs
kubectl logs -l app=todo-backend

# Frontend logs
kubectl logs -l app=todo-frontend
```

**Expected**: Healthy startup logs, no errors

#### 4.3 Test Health Endpoints
```bash
# Backend health check
kubectl port-forward svc/todo-backend 8000:8000
curl http://localhost:8000/health

# Frontend health check
kubectl port-forward svc/todo-frontend 3000:3000
curl http://localhost:3000/api/health
```

**Expected**: Both endpoints return 200 OK

#### 4.4 Access Application
```bash
# Get frontend URL
minikube service todo-frontend --url

# Open in browser
# Windows: start <url>
# macOS: open <url>
# Linux: xdg-open <url>
```

**Expected**: Todo Chatbot UI loads, can create tasks via chat

---

## User Story 2: Scaling Backend

### Scale to Multiple Replicas
```bash
# Scale to 3 replicas
kubectl scale deployment todo-backend --replicas=3

# Verify
kubectl get pods -l app=todo-backend
```

**Expected**: 3 backend pods Running

### Test Load Distribution
```bash
# Send multiple requests
for i in {1..10}; do curl http://<backend-url>/health; done

# Check logs to verify distribution
kubectl logs -l app=todo-backend --tail=20
```

**Expected**: Requests distributed across different pods

### Test Pod Failure Recovery
```bash
# Delete one pod
kubectl delete pod <pod-name>

# Verify auto-restart
kubectl get pods -l app=todo-backend
```

**Expected**: Kubernetes automatically creates new pod, maintains 3 replicas

### Scale Back Down
```bash
kubectl scale deployment todo-backend --replicas=1
```

---

## User Story 3: Helm Installation

### Install via Helm
```bash
# Install application
helm install todo-chatbot infrastructure/helm/todo-chatbot

# Check status
helm status todo-chatbot

# List releases
helm list
```

**Expected**: All resources created, release status "deployed"

### Override Configuration
```bash
# Scale backend replicas
helm upgrade todo-chatbot infrastructure/helm/todo-chatbot --set backend.replicas=3

# Change image tags
helm upgrade todo-chatbot infrastructure/helm/todo-chatbot \
  --set frontend.image.tag=v2.0.0 \
  --set backend.image.tag=v2.0.0
```

**Expected**: Configuration changes applied, pods updated

### Uninstall
```bash
# Remove application
helm uninstall todo-chatbot

# Verify cleanup
kubectl get all
```

**Expected**: All resources removed cleanly

---

## Maintenance Operations

### View Logs
```bash
# All pods
kubectl logs -l app=todo-backend --tail=100

# Specific pod
kubectl logs <pod-name> --follow

# Previous container (if crashed)
kubectl logs <pod-name> --previous
```

### Restart Deployment
```bash
kubectl rollout restart deployment todo-backend
kubectl rollout restart deployment todo-frontend
```

### Update Image
```bash
# Rebuild image
docker build -t todo-backend:v2 -f infrastructure/docker/backend/Dockerfile ./backend

# Update deployment
kubectl set image deployment/todo-backend todo-backend=todo-backend:v2

# Check rollout status
kubectl rollout status deployment/todo-backend
```

### Resource Usage
```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods
```

---

## Cleanup

### Remove Kubernetes Resources
```bash
# Delete all resources
kubectl delete -f infrastructure/kubernetes/base/

# Or delete by label
kubectl delete all -l app=todo-chatbot
```

### Stop Minikube
```bash
minikube stop
```

### Delete Minikube Cluster
```bash
minikube delete
```

---

## Performance Tuning

### Resource Limits
Edit deployment manifests to adjust:
```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### Replica Count
```bash
# Increase replicas for high load
kubectl scale deployment todo-backend --replicas=5
```

### Health Check Timing
Adjust probe timing in deployment manifests:
```yaml
livenessProbe:
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
```

---

## Next Steps

- **User Story 2**: Test horizontal scaling (see Scaling Backend section)
- **User Story 3**: Install via Helm chart (see Helm Installation section)
- **Monitoring**: Add Prometheus/Grafana for metrics (Phase V)
- **CI/CD**: Automate deployment pipeline (Phase V)

---

## References

- Minikube Documentation: https://minikube.sigs.k8s.io/docs/
- Kubernetes Documentation: https://kubernetes.io/docs/
- Helm Documentation: https://helm.sh/docs/
- Troubleshooting Guide: `infrastructure/docs/troubleshooting.md`
