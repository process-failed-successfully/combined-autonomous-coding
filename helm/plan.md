# Helm Chart Plan: Jira Autonomous Agent

This chart enables the autonomous agent to process Jira tickets from a queue, with Kube-native scaling.

## Chart Metadata

- **Name**: `jira-agent`
- **Description**: A Helm chart for running autonomous agents that process Jira tickets from a Redis queue.
- **Dependencies**:
  - `redis`: `~17.0.0` (Use a community chart like `https://github.com/CloudPirates-io/helm-charts/tree/main/charts/redis` or `https://ot-container-kit.github.io/helm-charts` or `https://charts.bitnami.com/bitnami` if acceptable, otherwise a custom Redis deployment).
  - `keda`: (Required in the cluster for autoscaling). Ensure this is disabled by default.

## Components

### 1. Redis Queue

- **Type**: Redis List (`jira_ticket_queue`).
- **Function**: Holds Jira Ticket IDs (e.g., `PROJ-123`).

### 2. Agent Worker Deployment

- **Image**: `combined-autonomous-coding:latest`
- **Replicas**: Managed by KEDA.
- **Environment Variables**:
  - `JIRA_URL`: From `Secret`
  - `JIRA_EMAIL`: From `Secret`
  - `JIRA_TOKEN`: From `Secret`
  - `GIT_TOKEN`: From `Secret`
  - `REDIS_URL`: `redis-master:6379`
- **Command**:
  ```bash
  while true; do
    TICKET_ID=$(redis-cli -h $REDIS_HOST LPOP jira_ticket_queue)
    if [ ! -z "$TICKET_ID" ]; then
      python main.py --jira-ticket $TICKET_ID
    else
      sleep 10
    fi
  done
  ```

### 3. KEDA Scaling (ScaledObject)

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: jira-agent-scaler
spec:
  scaleTargetRef:
    name: jira-agent-worker
  minReplicaCount: 0
  maxReplicaCount: 10
  triggers:
    - type: redis
      metadata:
        address: redis-master:6379
        listName: jira_ticket_queue
        listLength: "1" # Scale 1 pod per ticket in queue
```

### 4. Credential Management

- **Secret**: `jira-agent-secrets`
- **Keys**: `jira-url`, `jira-email`, `jira-token`, `git-token`.

## Method for adding PRs to queue

A Job or a simple script can be used to enqueue tickets:

```bash
redis-cli -h $REDIS_HOST RPUSH jira_ticket_queue PROJ-123
```

Accessible via a `Service` if external producers are needed.

## Security

All sensitive credentials MUST be passed via `secretKeyRef` or `envFrom` referencing the Kubernetes Secret.
