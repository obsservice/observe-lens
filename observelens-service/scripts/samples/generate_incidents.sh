#!/usr/bin/env bash
#
# Generate sample incident data and import via the ObserveLens incidents API.
#
# Usage:
#   ./generate_incidents.sh [count]              # default: 10 incidents
#   ./generate_incidents.sh 20
#
# Environment variables:
#   BASE_URL    API base URL           (default: http://127.0.0.1:3081)
#   TENANT_ID   x-tenant-id header      (default: 1)
#   USER_ID     x-user-id header        (default: 1)
#   WEBHOOK_INTEGRATION_ID    (default: auto-detect first Webhook integration)
#   ALERTMANAGER_INTEGRATION_ID (default: auto-detect first Alertmanager integration)
#
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:3081}"
TENANT_ID="${TENANT_ID:-1}"
USER_ID="${USER_ID:-1}"
COUNT="${1:-10}"

AUTH_HEADERS=(-H "x-tenant-id: ${TENANT_ID}" -H "x-user-id: ${USER_ID}" -H "Content-Type: application/json")

# -- helpers ----------------------------------------------------------------

rand_int() { echo $((RANDOM % ${2:-100} + ${1:-1})); }

pick() { echo "$1" | awk -v seed="$RANDOM" 'BEGIN{srand(seed)} {a[NR]=$0} END{n=int(rand()*NR)+1; print a[n]}'; }

iso_now() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

iso_past() {
  # $1 = minutes ago
  local mins="$1"
  if date -u -v-"${mins}"M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null; then
    return
  fi
  date -u -d "-${mins} minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null
}

curl_json() {
  local url="$1" body="$2"
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${AUTH_HEADERS[@]}" -d "$body" "${url}")
  echo "$code"
}

# -- detect integrations ----------------------------------------------------

echo "Fetching incident integrations..."
INTEGRATIONS=$(curl -s "${AUTH_HEADERS[@]}" "${BASE_URL}/api/v1/incidents/integrations")

if [ -z "${WEBHOOK_INTEGRATION_ID:-}" ]; then
  WEBHOOK_INTEGRATION_ID=$(echo "$INTEGRATIONS" \
    | python3 -c "import sys,json; data=json.load(sys.stdin); print(next((i['id'] for i in data if i['type']=='Webhook' and i['status']=='Enabled'),''))" 2>/dev/null || echo "")
fi

if [ -z "${ALERTMANAGER_INTEGRATION_ID:-}" ]; then
  ALERTMANAGER_INTEGRATION_ID=$(echo "$INTEGRATIONS" \
    | python3 -c "import sys,json; data=json.load(sys.stdin); print(next((i['id'] for i in data if i['type']=='Alertmanager' and i['status']=='Enabled'),''))" 2>/dev/null || echo "")
fi

echo "  Webhook integration:       ${WEBHOOK_INTEGRATION_ID:-<none>}"
echo "  Alertmanager integration:  ${ALERTMANAGER_INTEGRATION_ID:-<none>}"
echo ""

if [ -z "$WEBHOOK_INTEGRATION_ID" ] && [ -z "$ALERTMANAGER_INTEGRATION_ID" ]; then
  echo "ERROR: No enabled Webhook or Alertmanager integration found."
  echo "       Create one first: POST /api/v1/incidents/integrations"
  exit 1
fi

# -- sample data pools ------------------------------------------------------

SERVICES=("payment-gateway" "order-service" "inventory-api" "user-auth" "shipping-svc" "notification-worker" "search-engine" "billing-engine" "cdn-edge" "kafka-broker")
HOSTS=("prod-k8s-node-01" "prod-k8s-node-02" "prod-k8s-node-03" "db-primary" "db-replica-01" "redis-cache-01" "lb-frontend-01" "lb-frontend-02")
SEVERITIES=("Critical" "Error" "Warn")
ALERTNAMES=("HighErrorRate" "PodCrashLooping" "LatencySpike" "DiskUsageHigh" "MemoryLeak" "ConnectionPoolExhausted" "CPUThrottling" "ReplicaLag")
DESCRIPTIONS=(
  "Error rate exceeded 5% threshold for the last 5 minutes"
  "Pod is restarting repeatedly with OOMKilled errors"
  "P99 latency spike detected on /api/v1/checkout endpoint"
  "Disk usage above 90% on /var/lib/postgresql"
  "Memory consumption growing steadily without release"
  "Database connection pool exhausted, new connections refused"
  "CPU throttling causing request queue buildup"
  "Replication lag exceeding 30 seconds on read replica"
)

# -- generate & import ------------------------------------------------------

echo "Generating ${COUNT} sample incidents..."
echo ""

success=0
fail=0

for i in $(seq 1 "$COUNT"); do
  svc=$(pick "$(printf '%s\n' "${SERVICES[@]}")")
  host=$(pick "$(printf '%s\n' "${HOSTS[@]}")")
  severity=$(pick "$(printf '%s\n' "${SEVERITIES[@]}")")
  alertname=$(pick "$(printf '%s\n' "${ALERTNAMES[@]}")")
  desc=$(pick "$(printf '%s\n' "${DESCRIPTIONS[@]}")")
  mins_ago=$(rand_int 5 1440)
  started=$(iso_past "$mins_ago")

  # Alternate between Webhook and Alertmanager (if both available)
  use_alertmanager=false
  if [ -n "$ALERTMANAGER_INTEGRATION_ID" ] && [ -n "$WEBHOOK_INTEGRATION_ID" ]; then
    [ $((i % 2)) -eq 0 ] && use_alertmanager=true
  elif [ -n "$ALERTMANAGER_INTEGRATION_ID" ]; then
    use_alertmanager=true
  fi

  if [ "$use_alertmanager" = true ]; then
    # Alertmanager webhook format
    am_status=$(pick "firing resolved")
    body=$(python3 -c "
import json, sys
print(json.dumps({
    'receiver': 'alertmanager',
    'status': '${am_status}',
    'alerts': [{
        'status': '${am_status}',
        'labels': {
            'alertname': '${alertname}',
            'severity': '${severity}' if '${severity}' != 'Error' else 'error',
            'service': '${svc}',
            'instance': '${host}'
        },
        'annotations': {
            'summary': '${alertname} on ${svc}',
            'description': '${desc}'
        },
        'startsAt': '${started}'
    }],
    'commonLabels': {'alertname': '${alertname}', 'service': '${svc}'},
    'commonAnnotations': {'summary': '${alertname} on ${svc}'},
    'externalURL': 'http://alertmanager:9093'
}))
")
    url="${BASE_URL}/api/v1/incidents/integrations/Alertmanager/${ALERTMANAGER_INTEGRATION_ID}/webhook"
    label="[AM] ${alertname} / ${svc}"
  else
    # Plain Webhook format
    body=$(python3 -c "
import json
print(json.dumps({
    'title': '${alertname} on ${svc}',
    'description': '${desc}',
    'severity': '${severity}',
    'started_at': '${started}',
    'labels': {'service': '${svc}', 'host': '${host}', 'alertname': '${alertname}'}
}))
")
    url="${BASE_URL}/api/v1/incidents/integrations/Webhook/${WEBHOOK_INTEGRATION_ID}/webhook"
    label="[WH] ${alertname} / ${svc}"
  fi

  code=$(curl_json "$url" "$body")
  if [ "$code" = "201" ]; then
    echo "  [$i/$COUNT] OK   ${label}  (${severity})"
    success=$((success + 1))
  else
    echo "  [$i/$COUNT] FAIL ${label}  (HTTP ${code})"
    fail=$((fail + 1))
  fi
done

echo ""
echo "Done: ${success} created, ${fail} failed out of ${COUNT} total."

# -- verify -----------------------------------------------------------------

echo ""
echo "Current incident count:"
TOTAL=$(curl -s "${AUTH_HEADERS[@]}" "${BASE_URL}/api/v1/incidents?page=1&page_size=1" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])" 2>/dev/null || echo "?")
echo "  total: ${TOTAL}"
