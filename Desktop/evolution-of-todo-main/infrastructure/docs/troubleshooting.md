# Kubernetes Deployment Troubleshooting Guide

**Purpose**: Common issues and solutions for Kubernetes deployment

**Last Updated**: 2026-02-06

## Table of Contents

1. [Minikube Issues](#minikube-issues)
2. [Docker Build Issues](#docker-build-issues)
3. [Pod Startup Issues](#pod-startup-issues)
4. [Service Connectivity Issues](#service-connectivity-issues)
5. [Resource Issues](#resource-issues)
6. [Helm Issues](#helm-issues)
7. [AI Generation Issues](#ai-generation-issues)

---

## Minikube Issues

### Issue: Minikube Won't Start

**Symptoms**:
```
❌ Exiting due to PROVIDER_DOCKER_NOT_RUNNING
```

**Solution**:
1. Ensure Docker Desktop is running
2. Try different driver:
   ```bash
   minikube start --driver=virtualbox
   # or
   minikube start --driver=hyperv
   ```
3. Delete and recreate cluster:
   ```bash
   minikube delete
   minikube start --cpus=2 --memory=4096
   ```

---

### Issue: Insufficient Resources

**Symptoms**:
```
❌ Requested memory allocation (4096MB) is less than the recommended minimum
```

**Solution**:
1. Increase memory allocation:
   ```bash
   minikube start --memory=8192
   ```
2. Close other applications to free up resources
3. Check system resources:
   ```bash
   # Windows
   Get-Process | Sort-Object -Property WS -Descending | Select-Object -First 10

   # macOS/Linux
   top
   ```

---

### Issue: Minikube Cluster Not Accessible

**Symptoms**:
```
Unable to connect to the server: dial tcp: lookup minikube on ...: no such host
```

**Solution**:
1. Verify cluster is running:
   ```bash
   minikube status
   ```
2. Restart cluster:
   ```bash
   minikube stop
   minikube start
   ```
3. Check kubectl context:
   ```bash
   kubectl config current-context
   kubectl config use-context minikube
   ```

---

## Docker Build Issues

### Issue: Docker Build Fails

**Symptoms**:
```
ERROR: failed to solve: failed to fetch ...
```

**Solution**:
1. Check Docker daemon is running:
   ```bash
   docker ps
   ```
2. Verify Dockerfile syntax:
   ```bash
   docker build --no-cache -t test -f Dockerfile .
   ```
3. Check network connectivity:
   ```bash
   ping google.com
   ```
4. Clear Docker cache:
   ```bash
   docker system prune -a
   ```

---

### Issue: Image Not Found in Minikube

**Symptoms**:
```
ErrImagePull: Failed to pull image "todo-frontend:latest"
```

**Solution**:
1. Ensure Docker environment is configured for Minikube:
   ```bash
   eval $(minikube docker-env)
   ```
2. Rebuild image in Minikube context:
   ```bash
   docker build -t todo-frontend:latest -f infrastructure/docker/frontend/Dockerfile ./frontend
   ```
3. Verify image exists:
   ```bash
   docker images | grep todo-frontend
   ```
4. Set imagePullPolicy to Never in deployment:
   ```yaml
   imagePullPolicy: Never
   ```

---

## Pod Startup Issues

### Issue: Pod Stuck in Pending

**Symptoms**:
```
NAME                            READY   STATUS    RESTARTS   AGE
todo-backend-xxx                0/1     Pending   0          5m
```

**Solution**:
1. Check pod events:
   ```bash
   kubectl describe pod <pod-name>
   ```
2. Check node resources:
   ```bash
   kubectl top nodes
   ```
3. Check for resource constraints:
   ```bash
   kubectl get events --sort-by='.lastTimestamp'
   ```
4. Reduce resource requests in deployment manifest

---

### Issue: Pod CrashLoopBackOff

**Symptoms**:
```
NAME                            READY   STATUS             RESTARTS   AGE
todo-backend-xxx                0/1     CrashLoopBackOff   5          5m
```

**Solution**:
1. Check pod logs:
   ```bash
   kubectl logs <pod-name>
   kubectl logs <pod-name> --previous
   ```
2. Check environment variables:
   ```bash
   kubectl exec <pod-name> -- env
   ```
3. Verify ConfigMap and Secret are applied:
   ```bash
   kubectl get configmap
   kubectl get secret
   ```
4. Check application startup requirements (database connection, etc.)

---

### Issue: ImagePullBackOff

**Symptoms**:
```
NAME                            READY   STATUS             RESTARTS   AGE
todo-backend-xxx                0/1     ImagePullBackOff   0          2m
```

**Solution**:
1. Verify image exists in Minikube:
   ```bash
   eval $(minikube docker-env)
   docker images | grep todo-backend
   ```
2. Set imagePullPolicy to Never:
   ```yaml
   spec:
     containers:
     - name: todo-backend
       image: todo-backend:latest
       imagePullPolicy: Never
   ```
3. Rebuild image if missing

---

### Issue: Liveness/Readiness Probe Failures

**Symptoms**:
```
Liveness probe failed: HTTP probe failed with statuscode: 500
```

**Solution**:
1. Check health endpoint:
   ```bash
   kubectl port-forward <pod-name> 8000:8000
   curl http://localhost:8000/health
   ```
2. Increase initialDelaySeconds:
   ```yaml
   livenessProbe:
     initialDelaySeconds: 60  # Increase from 30
   ```
3. Check application logs for startup errors
4. Verify all dependencies are available (database, external APIs)

---

## Service Connectivity Issues

### Issue: Service Has No Endpoints

**Symptoms**:
```
NAME           TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
todo-backend   ClusterIP   10.96.123.45    <none>        8000/TCP   5m

kubectl get endpoints
NAME           ENDPOINTS   AGE
todo-backend   <none>      5m
```

**Solution**:
1. Check pod labels match service selector:
   ```bash
   kubectl get pods --show-labels
   kubectl describe service todo-backend
   ```
2. Verify pods are Running:
   ```bash
   kubectl get pods -l app=todo-backend
   ```
3. Check service definition:
   ```yaml
   selector:
     app: todo-backend  # Must match pod labels
   ```

---

### Issue: Cannot Access Frontend

**Symptoms**:
```
minikube service todo-frontend --url
# Returns URL but browser shows connection refused
```

**Solution**:
1. Check service type:
   ```bash
   kubectl get svc todo-frontend
   ```
2. Use minikube tunnel (for LoadBalancer):
   ```bash
   minikube tunnel
   ```
3. Use port-forward as alternative:
   ```bash
   kubectl port-forward svc/todo-frontend 3000:3000
   ```
4. Check pod logs for startup errors

---

### Issue: Frontend Cannot Reach Backend

**Symptoms**:
- Frontend loads but API calls fail
- Browser console shows network errors

**Solution**:
1. Verify backend service is accessible:
   ```bash
   kubectl get svc todo-backend
   kubectl get endpoints todo-backend
   ```
2. Check ConfigMap has correct backend URL:
   ```bash
   kubectl get configmap -o yaml
   ```
3. Test backend from within cluster:
   ```bash
   kubectl run test --rm -it --image=curlimages/curl -- sh
   curl http://todo-backend:8000/health
   ```
4. Update frontend environment variable with correct service name

---

## Resource Issues

### Issue: Out of Memory (OOM) Killed

**Symptoms**:
```
State:          Terminated
Reason:         OOMKilled
Exit Code:      137
```

**Solution**:
1. Increase memory limits:
   ```yaml
   resources:
     limits:
       memory: 1Gi  # Increase from 512Mi
   ```
2. Check application memory usage:
   ```bash
   kubectl top pods
   ```
3. Optimize application code to reduce memory usage
4. Increase Minikube memory:
   ```bash
   minikube delete
   minikube start --memory=8192
   ```

---

### Issue: CPU Throttling

**Symptoms**:
- Slow application performance
- High CPU usage in metrics

**Solution**:
1. Increase CPU limits:
   ```yaml
   resources:
     limits:
       cpu: 1000m  # Increase from 500m
   ```
2. Check CPU usage:
   ```bash
   kubectl top pods
   ```
3. Scale horizontally instead of vertically:
   ```bash
   kubectl scale deployment todo-backend --replicas=3
   ```

---

## Helm Issues

### Issue: Helm Install Fails

**Symptoms**:
```
Error: INSTALLATION FAILED: unable to build kubernetes objects
```

**Solution**:
1. Lint chart:
   ```bash
   helm lint infrastructure/helm/todo-chatbot
   ```
2. Dry run to see errors:
   ```bash
   helm install --dry-run --debug todo-chatbot infrastructure/helm/todo-chatbot
   ```
3. Check template syntax:
   ```bash
   helm template todo-chatbot infrastructure/helm/todo-chatbot
   ```
4. Verify values.yaml is valid YAML

---

### Issue: Helm Upgrade Fails

**Symptoms**:
```
Error: UPGRADE FAILED: another operation (install/upgrade/rollback) is in progress
```

**Solution**:
1. Check release status:
   ```bash
   helm status todo-chatbot
   ```
2. Rollback if needed:
   ```bash
   helm rollback todo-chatbot
   ```
3. Force upgrade:
   ```bash
   helm upgrade --force todo-chatbot infrastructure/helm/todo-chatbot
   ```

---

### Issue: Helm Uninstall Leaves Resources

**Symptoms**:
- Resources still exist after `helm uninstall`

**Solution**:
1. Manually delete resources:
   ```bash
   kubectl delete all -l app.kubernetes.io/instance=todo-chatbot
   ```
2. Check for orphaned resources:
   ```bash
   kubectl get all --all-namespaces | grep todo
   ```
3. Delete specific resource types:
   ```bash
   kubectl delete configmap,secret -l app.kubernetes.io/instance=todo-chatbot
   ```

---

## AI Generation Issues

### Issue: AI Tool Not Available

**Symptoms**:
- Docker AI, kubectl-ai, or kagent not installed
- Command not found errors

**Solution**:
1. Use Claude Code as fallback for all generation
2. Provide detailed prompts with all requirements
3. Review generated code carefully
4. Document fallback in audit trail

---

### Issue: Generated Code Has Errors

**Symptoms**:
- Dockerfile build fails
- Kubernetes manifest apply fails
- Syntax errors in generated code

**Solution**:
1. Review error messages carefully
2. Refine AI prompt with more specific requirements
3. Regenerate with improved prompt
4. Document iterations in audit trail
5. Manual fixes only as last resort (document justification)

---

### Issue: Generated Code Doesn't Match Spec

**Symptoms**:
- Missing required features
- Incorrect configuration
- Security issues

**Solution**:
1. Review specification requirements
2. Update prompt to include missing requirements
3. Regenerate code
4. Validate against specification checklist
5. Document any deviations in audit trail

---

## Diagnostic Commands

### Cluster Health
```bash
kubectl cluster-info
kubectl get nodes
kubectl get componentstatuses
```

### Pod Diagnostics
```bash
kubectl get pods --all-namespaces
kubectl describe pod <pod-name>
kubectl logs <pod-name> --tail=100
kubectl logs <pod-name> --previous
kubectl exec <pod-name> -- sh
```

### Service Diagnostics
```bash
kubectl get svc
kubectl get endpoints
kubectl describe svc <service-name>
```

### Resource Usage
```bash
kubectl top nodes
kubectl top pods
kubectl describe node minikube
```

### Events
```bash
kubectl get events --sort-by='.lastTimestamp'
kubectl get events --field-selector type=Warning
```

### Configuration
```bash
kubectl get configmap -o yaml
kubectl get secret -o yaml
kubectl describe deployment <deployment-name>
```

---

## Recovery Procedures

### Complete Reset
```bash
# Delete all resources
kubectl delete all --all

# Or delete by namespace
kubectl delete namespace default

# Restart Minikube
minikube stop
minikube start
```

### Rollback Deployment
```bash
# View rollout history
kubectl rollout history deployment/todo-backend

# Rollback to previous version
kubectl rollout undo deployment/todo-backend

# Rollback to specific revision
kubectl rollout undo deployment/todo-backend --to-revision=2
```

### Force Pod Restart
```bash
# Delete pod (will be recreated)
kubectl delete pod <pod-name>

# Or restart deployment
kubectl rollout restart deployment/todo-backend
```

---

## Getting Help

### Kubernetes Documentation
- Official Docs: https://kubernetes.io/docs/
- Troubleshooting: https://kubernetes.io/docs/tasks/debug/

### Minikube Documentation
- Official Docs: https://minikube.sigs.k8s.io/docs/
- Troubleshooting: https://minikube.sigs.k8s.io/docs/handbook/troubleshooting/

### Community Support
- Kubernetes Slack: https://slack.k8s.io/
- Stack Overflow: Tag `kubernetes` or `minikube`
- GitHub Issues: Minikube, kubectl, Helm repositories

---

## Preventive Measures

### Regular Maintenance
```bash
# Clean up unused resources
kubectl delete pods --field-selector status.phase=Failed
kubectl delete pods --field-selector status.phase=Succeeded

# Prune Docker images
docker system prune -a

# Update Minikube
minikube update-check
```

### Monitoring
```bash
# Watch pod status
kubectl get pods --watch

# Monitor logs
kubectl logs -f <pod-name>

# Check resource usage
watch kubectl top pods
```

### Backup
```bash
# Export all resources
kubectl get all --all-namespaces -o yaml > backup.yaml

# Export specific resources
kubectl get deployment,service,configmap,secret -o yaml > resources.yaml
```

---

## Contact

For Phase IV specific issues, refer to:
- Constitution: `.specify/memory/constitution.md`
- Specification: `specs/001-kubernetes-deployment/spec.md`
- Implementation Plan: `specs/001-kubernetes-deployment/plan.md`
