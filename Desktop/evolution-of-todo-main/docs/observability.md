# Observability Configuration for Event-Driven Todo Platform

This document describes the observability setup for the platform, including structured logging, metrics, and distributed tracing.

## T080: Structured Logging with Correlation IDs

### Implementation

All services use structured logging with the following format:

```python
import logging
import uuid
from contextvars import ContextVar

# Correlation ID context variable
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [correlation_id=%(correlation_id)s] - %(message)s'
)

class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""
    def filter(self, record):
        record.correlation_id = correlation_id_var.get() or 'none'
        return True

# Add filter to all handlers
for handler in logging.root.handlers:
    handler.addFilter(CorrelationIdFilter())
```

### Correlation ID Propagation

1. **HTTP Requests**: Extract from `X-Correlation-ID` header or generate new UUID
2. **Dapr Events**: Extract from event metadata `correlation_id` field
3. **WebSocket**: Include in message metadata

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages for recoverable issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical failures requiring immediate attention

### Example Log Entry

```json
{
  "timestamp": "2026-02-09T10:30:45.123Z",
  "service": "todo-api",
  "level": "INFO",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Task created successfully",
  "task_id": 123,
  "user_id": 456
}
```

---

## T081: Prometheus Metrics

### Metrics Endpoints

All services expose metrics at `/metrics` endpoint in Prometheus format.

### Standard Metrics

#### HTTP Metrics
- `http_requests_total` - Total HTTP requests (counter)
- `http_request_duration_seconds` - HTTP request latency (histogram)
- `http_requests_in_progress` - Current in-progress requests (gauge)

#### Application Metrics
- `tasks_created_total` - Total tasks created (counter)
- `tasks_completed_total` - Total tasks completed (counter)
- `tasks_deleted_total` - Total tasks deleted (counter)
- `websocket_connections_active` - Active WebSocket connections (gauge)
- `events_published_total` - Total events published (counter)
- `events_consumed_total` - Total events consumed (counter)

#### System Metrics
- `process_cpu_seconds_total` - CPU time (counter)
- `process_resident_memory_bytes` - Memory usage (gauge)
- `process_open_fds` - Open file descriptors (gauge)

### Implementation

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

tasks_created_total = Counter('tasks_created_total', 'Total tasks created')
tasks_completed_total = Counter('tasks_completed_total', 'Total tasks completed')

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### Prometheus Configuration

```yaml
# prometheus.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'todo-services'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - default
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: (todo-api|chat-api|recurring-task-service|notification-service|websocket-sync-service|audit-log-service)
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_pod_label_app]
        target_label: service
```

---

## T082: Distributed Tracing with Dapr

### Dapr Tracing Configuration

Dapr automatically instruments all service-to-service calls and Pub/Sub operations.

#### Enable Tracing in Dapr Configuration

```yaml
# k8s/dapr-components/tracing.yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: tracing-config
  namespace: default
spec:
  tracing:
    samplingRate: "1"  # 100% sampling (adjust for production)
    zipkin:
      endpointAddress: "http://zipkin.default.svc.cluster.local:9411/api/v2/spans"
```

#### Deploy Zipkin

```yaml
# k8s/zipkin.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zipkin
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: zipkin
  template:
    metadata:
      labels:
        app: zipkin
    spec:
      containers:
      - name: zipkin
        image: openzipkin/zipkin:latest
        ports:
        - containerPort: 9411
---
apiVersion: v1
kind: Service
metadata:
  name: zipkin
  namespace: default
spec:
  type: LoadBalancer
  ports:
  - port: 9411
    targetPort: 9411
  selector:
    app: zipkin
```

#### Apply Tracing Configuration to Services

Update all service deployments to use tracing configuration:

```yaml
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "todo-api"
  dapr.io/config: "tracing-config"  # Add this line
```

### Trace Context Propagation

Dapr automatically propagates trace context via W3C Trace Context headers:
- `traceparent`: Trace ID, span ID, trace flags
- `tracestate`: Vendor-specific trace information

### Viewing Traces

Access Zipkin UI at: `http://<zipkin-service-ip>:9411`

Traces show:
- Service-to-service calls
- Pub/Sub publish and subscribe operations
- State store operations
- Request latency breakdown
- Error traces

---

## T083: Centralized Logging

### Fluentd Configuration

Deploy Fluentd as DaemonSet to collect logs from all pods:

```yaml
# k8s/fluentd-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      serviceAccountName: fluentd
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1-debian-elasticsearch
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch.default.svc.cluster.local"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
        - name: FLUENT_ELASTICSEARCH_SCHEME
          value: "http"
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

### Cloud Logging Options

#### AWS CloudWatch
```yaml
env:
- name: FLUENT_CLOUDWATCH_REGION
  value: "us-east-1"
- name: FLUENT_CLOUDWATCH_LOG_GROUP
  value: "/aws/eks/todo-app"
```

#### Google Cloud Logging
```yaml
env:
- name: FLUENT_GOOGLE_CLOUD_PROJECT
  value: "your-project-id"
- name: FLUENT_GOOGLE_CLOUD_LOGGING_RESOURCE_TYPE
  value: "k8s_cluster"
```

#### Azure Monitor
```yaml
env:
- name: FLUENT_AZURE_WORKSPACE_ID
  value: "your-workspace-id"
- name: FLUENT_AZURE_SHARED_KEY
  valueFrom:
    secretKeyRef:
      name: azure-logging-secret
      key: shared-key
```

### Log Retention Policies

- **Development**: 7 days
- **Staging**: 30 days
- **Production**: 90 days (compliance requirement)

### Log Aggregation Query Examples

```
# Find all errors in the last hour
level:ERROR AND timestamp:[now-1h TO now]

# Find all requests for a specific user
user_id:123 AND service:todo-api

# Trace a request by correlation ID
correlation_id:"a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Find slow requests (>2 seconds)
duration:>2000 AND service:*
```

---

## Monitoring Dashboard

### Grafana Dashboards

Import pre-built dashboards:
1. **Service Overview**: Request rate, latency, error rate
2. **Dapr Metrics**: Pub/Sub throughput, state store operations
3. **WebSocket Connections**: Active connections, message rate
4. **Task Metrics**: Tasks created/completed/deleted per hour

### Alerting Rules

```yaml
# prometheus-alerts.yaml
groups:
- name: todo-app-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Service {{ $labels.service }} has error rate > 5%"

  - alert: HighLatency
    expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High latency detected"
      description: "Service {{ $labels.service }} p95 latency > 2s"

  - alert: ServiceDown
    expr: up{job="todo-services"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service is down"
      description: "Service {{ $labels.service }} is not responding"
```

---

## Summary

All observability features are now configured:

✅ **T080**: Structured logging with correlation IDs
✅ **T081**: Prometheus metrics endpoints on all services
✅ **T082**: Dapr distributed tracing with Zipkin
✅ **T083**: Centralized logging with Fluentd

### Next Steps

1. Deploy Prometheus and Grafana to Kubernetes
2. Deploy Zipkin for distributed tracing
3. Deploy Fluentd DaemonSet for log collection
4. Configure cloud logging destination
5. Import Grafana dashboards
6. Set up alerting rules
7. Test end-to-end observability
