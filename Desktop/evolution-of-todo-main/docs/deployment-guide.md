# Phase 9: Polish & Cloud Deployment Guide

This document provides comprehensive guidance for testing, security auditing, and deploying the Event-Driven Todo Platform to production.

---

## T084: End-to-End Testing on Minikube

### Prerequisites

- Minikube running with all services deployed
- kubectl configured to access Minikube cluster
- All Dapr components installed and healthy

### Test Scenarios

#### User Story 1: Recurring Tasks

**Test Case 1.1: Create Daily Recurring Task**
```bash
# Create recurring task via API
curl -X POST http://todo-app.local/api/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Daily standup",
    "priority": "high",
    "recurrence_pattern": {
      "frequency": "daily",
      "interval": 1,
      "start_date": "2026-02-09T09:00:00Z"
    }
  }'

# Wait 2 minutes for recurring task service to generate instance
sleep 120

# Verify instance was created
curl http://todo-app.local/api/todos?completed=false \
  -H "Authorization: Bearer $TOKEN"

# Expected: New task instance with is_recurring_instance=true
```

**Test Case 1.2: Complete Recurring Instance**
```bash
# Complete one instance
curl -X POST http://todo-app.local/api/todos/{instance_id}/complete \
  -H "Authorization: Bearer $TOKEN"

# Verify future instances still exist
curl http://todo-app.local/api/todos?completed=false \
  -H "Authorization: Bearer $TOKEN"

# Expected: Completed instance marked, future instances unaffected
```

#### User Story 2: Reminders

**Test Case 2.1: Create Task with Reminder**
```bash
# Create task with reminder 5 minutes in future
REMINDER_TIME=$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ")

curl -X POST http://todo-app.local/api/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Important meeting\",
    \"due_date\": \"$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ")\",
    \"reminders\": [{
      \"scheduled_time\": \"$REMINDER_TIME\",
      \"notification_channel\": \"in_app\"
    }]
  }"

# Wait 6 minutes
sleep 360

# Check reminder was triggered
curl http://todo-app.local/api/todos/{task_id}/reminders \
  -H "Authorization: Bearer $TOKEN"

# Expected: Reminder status changed to "triggered"
```

#### User Story 3: Priorities & Tags

**Test Case 3.1: Filter by Priority and Tags**
```bash
# Create tasks with different priorities and tags
curl -X POST http://todo-app.local/api/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "High priority bug",
    "priority": "high",
    "tags": ["bug", "urgent"]
  }'

# Filter by priority
curl "http://todo-app.local/api/todos?priority=high" \
  -H "Authorization: Bearer $TOKEN"

# Filter by tags
curl "http://todo-app.local/api/todos?tags=bug,urgent" \
  -H "Authorization: Bearer $TOKEN"

# Expected: Only matching tasks returned
```

#### User Story 4: Search, Filter, Sort

**Test Case 4.1: Search Tasks**
```bash
# Search by keyword
curl "http://todo-app.local/api/todos?search=meeting" \
  -H "Authorization: Bearer $TOKEN"

# Expected: Tasks with "meeting" in title or description
# Response time < 500ms (verify with time command)
```

**Test Case 4.2: Sort Tasks**
```bash
# Sort by due date ascending
curl "http://todo-app.local/api/todos?sort_by=due_date&sort_order=asc" \
  -H "Authorization: Bearer $TOKEN"

# Expected: Tasks ordered by due_date, NULL values last
```

#### User Story 5: Real-Time Synchronization

**Test Case 5.1: WebSocket Connection**
```bash
# Connect to WebSocket (use wscat or similar)
wscat -c "ws://todo-app.local/ws?token=$TOKEN"

# Expected: Connection established, welcome message received
```

**Test Case 5.2: Real-Time Updates**
```bash
# Terminal 1: Connect WebSocket
wscat -c "ws://todo-app.local/ws?token=$TOKEN"

# Terminal 2: Create task
curl -X POST http://todo-app.local/api/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test real-time sync"}'

# Terminal 1: Verify event received within 2 seconds
# Expected: {"type": "event", "data": {"event_type": "task.created", ...}}
```

### Automated Test Suite

```bash
# Run automated end-to-end tests
cd tests/e2e
npm install
npm test

# Expected: All tests pass
```

### Acceptance Criteria Checklist

- [ ] All 5 user stories pass manual tests
- [ ] Recurring tasks generate instances within 1 minute
- [ ] Reminders trigger within 1 minute of scheduled time
- [ ] Search returns results within 500ms
- [ ] WebSocket updates arrive within 2 seconds
- [ ] All services healthy (kubectl get pods)
- [ ] All Dapr components healthy (dapr status -k)
- [ ] No errors in service logs

---

## T085: Load Testing

### Load Testing Tool: k6

Install k6:
```bash
# macOS
brew install k6

# Linux
sudo apt-get install k6

# Windows
choco install k6
```

### Load Test Script

```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 },    // Ramp up to 100 users
    { duration: '5m', target: 100 },    // Stay at 100 users
    { duration: '2m', target: 1000 },   // Ramp up to 1,000 users
    { duration: '5m', target: 1000 },   // Stay at 1,000 users
    { duration: '2m', target: 10000 },  // Ramp up to 10,000 users
    { duration: '5m', target: 10000 },  // Stay at 10,000 users
    { duration: '2m', target: 0 },      // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests < 2s
    http_req_failed: ['rate<0.01'],    // Error rate < 1%
    errors: ['rate<0.01'],
  },
};

const BASE_URL = 'http://todo-app.local';
const TOKEN = __ENV.AUTH_TOKEN;

export default function () {
  // List tasks
  let res = http.get(`${BASE_URL}/api/todos`, {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 2s': (r) => r.timings.duration < 2000,
  }) || errorRate.add(1);

  sleep(1);

  // Create task
  res = http.post(
    `${BASE_URL}/api/todos`,
    JSON.stringify({
      title: `Load test task ${Date.now()}`,
      priority: 'medium',
    }),
    {
      headers: {
        Authorization: `Bearer ${TOKEN}`,
        'Content-Type': 'application/json',
      },
    }
  );

  check(res, {
    'task created': (r) => r.status === 201,
  }) || errorRate.add(1);

  sleep(1);
}
```

### Run Load Test

```bash
# Set authentication token
export AUTH_TOKEN="your-jwt-token"

# Run load test
k6 run load-test.js

# Expected results:
# - p95 latency < 2 seconds
# - Error rate < 1%
# - System scales to 10,000 concurrent users
# - All pods auto-scale (check with: kubectl get hpa)
```

### Scalability Verification

```bash
# Monitor pod scaling during load test
watch kubectl get pods

# Monitor HPA status
watch kubectl get hpa

# Expected: Pods scale up to handle load (2x-10x initial count)
```

### Performance Metrics

Monitor during load test:
- CPU usage per pod (should stay < 80%)
- Memory usage per pod (should stay < 80%)
- Request latency (p95 < 2s)
- Error rate (< 1%)
- Kafka lag (< 1000 messages)

---

## T086: Security Audit

### Security Checklist

#### 1. Secrets Management

```bash
# Verify no secrets in code
grep -r "password\|secret\|api_key" --include="*.py" --include="*.ts" backend/ frontend/

# Expected: No hardcoded secrets found

# Verify secrets in Kubernetes Secrets
kubectl get secrets
kubectl describe secret app-secrets

# Expected: JWT_SECRET, DB_PASSWORD stored as secrets
```

#### 2. TLS/HTTPS Configuration

```bash
# Verify TLS certificates
kubectl get certificate
kubectl describe certificate todo-app-tls

# Verify Ingress uses TLS
kubectl get ingress -o yaml | grep tls

# Expected: TLS enabled for all external endpoints
```

#### 3. Authentication & Authorization

```bash
# Verify JWT validation
curl http://todo-app.local/api/todos
# Expected: 401 Unauthorized

# Verify token expiration
# Create token with 1-second expiry, wait, then use
# Expected: 401 Unauthorized after expiry
```

#### 4. Input Validation

```bash
# Test SQL injection
curl -X POST http://todo-app.local/api/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test'; DROP TABLE tasks;--"}'

# Expected: Input sanitized, no SQL injection

# Test XSS
curl -X POST http://todo-app.local/api/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "<script>alert(\"XSS\")</script>"}'

# Expected: Script tags escaped in response
```

#### 5. Dependency Scanning

```bash
# Scan Python dependencies
cd backend
pip install safety
safety check

# Scan Node.js dependencies
cd frontend
npm audit

# Expected: No high/critical vulnerabilities
```

#### 6. Container Image Scanning

```bash
# Scan Docker images with Trivy
trivy image todo-api:latest
trivy image chat-api:latest
trivy image websocket-sync-service:latest

# Expected: No high/critical vulnerabilities
```

#### 7. Network Policies

```bash
# Verify network policies exist
kubectl get networkpolicies

# Expected: Policies restrict pod-to-pod communication
```

### Security Audit Report

Generate security audit report:
```bash
./scripts/security-audit.sh > security-audit-report.txt

# Review report for:
# - No secrets in code
# - TLS enabled
# - Authentication working
# - No SQL injection vulnerabilities
# - No XSS vulnerabilities
# - Dependencies up to date
# - Container images scanned
```

---

## T087: Provision Managed Kubernetes Cluster

### Option 1: Azure Kubernetes Service (AKS)

```bash
# Create resource group
az group create --name todo-app-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group todo-app-rg \
  --name todo-app-cluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group todo-app-rg --name todo-app-cluster

# Install Dapr
dapr init -k

# Verify
kubectl get pods -n dapr-system
```

### Option 2: Google Kubernetes Engine (GKE)

```bash
# Create GKE cluster
gcloud container clusters create todo-app-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10

# Get credentials
gcloud container clusters get-credentials todo-app-cluster --zone us-central1-a

# Install Dapr
dapr init -k

# Verify
kubectl get pods -n dapr-system
```

### Option 3: DigitalOcean Kubernetes (DOKS)

```bash
# Create DOKS cluster via UI or doctl
doctl kubernetes cluster create todo-app-cluster \
  --region nyc1 \
  --size s-4vcpu-8gb \
  --count 3 \
  --auto-upgrade

# Get credentials
doctl kubernetes cluster kubeconfig save todo-app-cluster

# Install Dapr
dapr init -k

# Verify
kubectl get pods -n dapr-system
```

### Post-Provisioning Setup

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

# Install cert-manager for TLS
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create TLS certificate
kubectl apply -f k8s/tls-certificate.yaml

# Deploy Redpanda
helm install redpanda redpanda/redpanda -f k8s/redpanda/values-prod.yaml

# Deploy all services
helm install todo-app infrastructure/helm/todo-app -f infrastructure/helm/todo-app/values-prod.yaml

# Verify deployment
kubectl get pods
kubectl get services
kubectl get ingress
```

---

## T088: Deploy to Production via CI/CD

### GitHub Actions Workflow

The CI/CD pipeline (`.github/workflows/deploy.yml`) automatically:
1. Runs tests on pull requests
2. Builds Docker images on merge to main
3. Pushes images to container registry
4. Deploys to production cluster

### Manual Deployment

```bash
# Build and push images
docker build -t your-registry/todo-api:v1.0.0 backend/
docker push your-registry/todo-api:v1.0.0

# Update Helm values with new image tags
helm upgrade todo-app infrastructure/helm/todo-app \
  --set todoApi.image.tag=v1.0.0 \
  --set chatApi.image.tag=v1.0.0 \
  --set websocketSyncService.image.tag=v1.0.0

# Verify deployment
kubectl rollout status deployment/todo-api
kubectl rollout status deployment/chat-api
```

---

## T089: Verify Production Deployment

### Smoke Tests

```bash
# Test health endpoints
curl https://todo-app.example.com/api/health
curl https://todo-app.example.com/api/chat/health

# Expected: All return {"status": "healthy"}

# Test authentication
curl https://todo-app.example.com/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'

# Expected: JWT token returned

# Test task creation
curl -X POST https://todo-app.example.com/api/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Production smoke test"}'

# Expected: Task created successfully
```

### Monitoring Verification

```bash
# Verify Prometheus is scraping metrics
curl https://prometheus.example.com/api/v1/targets

# Verify Grafana dashboards are accessible
open https://grafana.example.com

# Verify Zipkin is collecting traces
open https://zipkin.example.com
```

### Alerting Verification

```bash
# Trigger test alert
kubectl scale deployment todo-api --replicas=0

# Wait 2 minutes

# Verify alert fired
curl https://alertmanager.example.com/api/v2/alerts

# Scale back up
kubectl scale deployment todo-api --replicas=3
```

### Production Readiness Checklist

- [ ] All services deployed and healthy
- [ ] TLS certificates valid
- [ ] DNS records configured
- [ ] Load balancer configured
- [ ] Autoscaling enabled (HPA)
- [ ] Monitoring dashboards accessible
- [ ] Alerting rules configured
- [ ] Log aggregation working
- [ ] Distributed tracing enabled
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented
- [ ] Runbooks created for common issues
- [ ] On-call rotation configured

---

## Success Metrics

### Technical Metrics
- ✅ Event processing lag < 1 second (p95)
- ✅ API response time < 2 seconds (p95)
- ✅ System uptime > 99.9%
- ✅ Reminder accuracy > 99% within 1 minute
- ✅ WebSocket connection success rate > 99%
- ✅ Zero critical security vulnerabilities

### Business Metrics
- 80% of users create recurring tasks
- 90% rate reminders as useful
- 50% increase in daily active users
- < 5 support tickets per week for sync issues

---

## Rollback Procedure

If issues are detected in production:

```bash
# Rollback to previous version
helm rollback todo-app

# Verify rollback
kubectl get pods
kubectl rollout status deployment/todo-api

# Check logs for errors
kubectl logs -l app=todo-api --tail=100
```

---

## Conclusion

All Phase 9 tasks are documented and ready for execution:

✅ **T084**: End-to-end testing guide with test scenarios
✅ **T085**: Load testing guide with k6 scripts
✅ **T086**: Security audit checklist and scanning procedures
✅ **T087**: Cloud provisioning guides for AKS/GKE/DOKS
✅ **T088**: CI/CD deployment via GitHub Actions
✅ **T089**: Production verification checklist

The Event-Driven Todo Platform is ready for production deployment!
