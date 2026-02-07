# Kubernetes Deployment Quickstart

**Purpose**: Quick reference for deploying Todo Chatbot to Minikube

**Last Updated**: 2026-02-06

## Prerequisites Checklist

- [ ] Minikube installed (`minikube version`)
- [ ] Docker installed (`docker --version`)
- [ ] kubectl installed (`kubectl version --client`)
- [ ] Helm installed (`helm version`)
- [ ] Minimum 4GB RAM, 2 CPU cores available

## 5-Minute Deployment

### Step 1: Start Minikube (1 minute)
```bash
cd "C:\Users\Tech Trends\Desktop\evolution-of-todo-main"
minikube start --cpus=2 --memory=4096
```

**Verify**: `kubectl cluster-info` shows cluster running

---

### Step 2: Configure Docker for Minikube (10 seconds)
```bash
# Windows PowerShell
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# macOS/Linux Bash
eval $(minikube docker-env)
```

**Verify**: `docker ps` shows Minikube containers

---

### Step 3: Build Container Images (2 minutes)
```bash
# Build frontend
docker build -t todo-frontend:latest -f infrastructure/docker/frontend/Dockerfile ./frontend

# Build backend
docker build -t todo-backend:latest -f infrastructure/docker/backend/Dockerfile ./backend
```

**Verify**: `docker images | grep todo-` shows both images

---

### Step 4: Update Secrets (30 seconds)
Edit `infrastructure/kubernetes/base/secrets.yaml` and replace placeholder values with your actual base64-encoded secrets:

```bash
# Get your DATABASE_URL from Neon dashboard
# Get your OPENROUTER_API_KEY from OpenRouter dashboard

# Encode values (example)
echo -n "your-actual-database-url" | base64
echo -n "your-actual-api-key" | base64

# Update secrets.yaml with encoded values
```

---

### Step 5: Deploy to Kubernetes (1 minute)
```bash
# Apply configuration
kubectl apply -f infrastructure/kubernetes/base/configmap.yaml
kubectl apply -f infrastructure/kubernetes/base/secrets.yaml

# Deploy backend
kubectl apply -f infrastructure/kubernetes/base/backend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/base/backend-service.yaml

# Deploy frontend
kubectl apply -f infrastructure/kubernetes/base/frontend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/base/frontend-service.yaml
```

**Verify**: `kubectl get pods` shows both pods Running (may take 30-60 seconds)

---

### Step 6: Access Application (30 seconds)
```bash
# Get frontend URL
minikube service todo-frontend --url

# Open in browser
# Windows: start <url>
# macOS: open <url>
# Linux: xdg-open <url>
```

**Verify**: Todo Chatbot UI loads, you can create tasks via chat

---

## Validation Commands

### Check Pod Status
```bash
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs -l app=todo-backend
kubectl logs -l app=todo-frontend
```

### Check Services
```bash
kubectl get svc
kubectl get endpoints
```

### Test Health Endpoints
```bash
# Backend
kubectl port-forward svc/todo-backend 8000:8000
curl http://localhost:8000/health

# Frontend
kubectl port-forward svc/todo-frontend 3000:3000
curl http://localhost:3000/api/health
```

---

## User Story 2: Scaling (Optional)

### Scale Backend to 3 Replicas
```bash
kubectl scale deployment todo-backend --replicas=3
kubectl get pods -l app=todo-backend
```

### Test Load Distribution
```bash
# Send requests and check logs
for i in {1..10}; do curl http://<backend-url>/health; done
kubectl logs -l app=todo-backend --tail=20
```

### Scale Back Down
```bash
kubectl scale deployment todo-backend --replicas=1
```

---

## Troubleshooting

### Pods Not Starting
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

**Common Issues**:
- Image not found: Rebuild with `eval $(minikube docker-env)` first
- Secrets not configured: Update secrets.yaml with actual values
- Resource constraints: Increase Minikube memory

### Cannot Access Frontend
```bash
# Use port-forward as alternative
kubectl port-forward svc/todo-frontend 3000:3000
# Then open http://localhost:3000
```

### Backend Errors
```bash
# Check logs
kubectl logs -l app=todo-backend --tail=100

# Check environment variables
kubectl exec <backend-pod> -- env | grep -E "DATABASE|OPENROUTER"
```

---

## Cleanup

### Remove Deployment
```bash
kubectl delete -f infrastructure/kubernetes/base/
```

### Stop Minikube
```bash
minikube stop
```

### Delete Cluster
```bash
minikube delete
```

---

## Next Steps

- **User Story 2**: Test horizontal scaling (see above)
- **User Story 3**: Install via Helm chart (see deployment-guide.md)
- **Documentation**: See `infrastructure/docs/` for detailed guides

---

## Success Criteria

✅ Both pods reach Running status within 2 minutes
✅ Frontend UI loads successfully
✅ Backend API responds to health checks
✅ Can create tasks via chat interface
✅ Phase III functionality works in Kubernetes

---

## Files Reference

- **Dockerfiles**: `infrastructure/docker/*/Dockerfile`
- **Kubernetes Manifests**: `infrastructure/kubernetes/base/*.yaml`
- **Documentation**: `infrastructure/docs/*.md`
- **Audit Trails**: `infrastructure/*/generation-audit.md`

---

## Support

For detailed troubleshooting, see:
- `infrastructure/docs/troubleshooting.md`
- `infrastructure/docs/deployment-guide.md`
- `specs/001-kubernetes-deployment/spec.md`
