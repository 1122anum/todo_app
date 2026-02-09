#!/bin/bash
# Create Kafka Topics for Event-Driven Todo Platform
# This script creates the required Kafka topics in Redpanda

set -e

echo "=========================================="
echo "Creating Kafka Topics in Redpanda"
echo "=========================================="

# Redpanda connection details
REDPANDA_BROKERS="${REDPANDA_BROKERS:-redpanda.redpanda.svc.cluster.local:9092}"

# Check if rpk is available
if ! command -v rpk &> /dev/null; then
    echo "ERROR: rpk (Redpanda CLI) is not installed."
    echo "Install from: https://docs.redpanda.com/docs/get-started/rpk-install/"
    exit 1
fi

echo "Redpanda brokers: $REDPANDA_BROKERS"
echo ""

# Topic configuration
declare -A TOPICS=(
    ["task-events"]="10:3"           # 10 partitions, 3 replicas
    ["reminders"]="5:3"               # 5 partitions, 3 replicas
    ["task-updates"]="10:3"           # 10 partitions, 3 replicas
)

# Create topics
for topic in "${!TOPICS[@]}"; do
    IFS=':' read -r partitions replicas <<< "${TOPICS[$topic]}"

    echo "Creating topic: $topic"
    echo "  Partitions: $partitions"
    echo "  Replicas: $replicas"

    rpk topic create "$topic" \
        --brokers "$REDPANDA_BROKERS" \
        --partitions "$partitions" \
        --replicas "$replicas" \
        --config retention.ms=604800000 \
        --config cleanup.policy=delete \
        --config compression.type=snappy \
        --config max.message.bytes=1048576 \
        || echo "  (Topic may already exist)"

    echo "✓ Topic $topic ready"
    echo ""
done

# List all topics
echo "=========================================="
echo "All Topics:"
echo "=========================================="
rpk topic list --brokers "$REDPANDA_BROKERS"

echo ""
echo "=========================================="
echo "Topic Creation Complete!"
echo "=========================================="
echo ""
echo "Topics created:"
echo "  - task-events: Task lifecycle events (create, update, delete, complete)"
echo "  - reminders: Reminder notifications"
echo "  - task-updates: Real-time synchronization events"
echo ""
echo "Configuration:"
echo "  - Retention: 7 days (604800000 ms)"
echo "  - Cleanup policy: delete"
echo "  - Compression: snappy"
echo "  - Max message size: 1 MB"
