#!/usr/bin/env bash
# Dispara um update do pipeline e faz polling DO UPDATE (nao do pipeline).
# Uso: scripts/rodar_pipeline.sh <pipeline_id> [--full-refresh]
set -euo pipefail
PROFILE="${DATABRICKS_CONFIG_PROFILE:-alura-imersao}"
export MSYS_NO_PATHCONV=1
PID="${1:?informe o pipeline_id}"; shift || true
UPDATE=$(databricks pipelines start-update "$PID" "$@" -p "$PROFILE" -o json \
  | python -c "import sys,json;print(json.load(sys.stdin)['update_id'])")
echo "update_id=${UPDATE}"
while :; do
  ST=$(databricks pipelines get-update "$PID" "$UPDATE" -p "$PROFILE" -o json \
       | python -c "import sys,json;print(json.load(sys.stdin)['update']['state'])")
  echo "  $(date +%H:%M:%S) state=${ST}"
  case "$ST" in COMPLETED|FAILED|CANCELED) break;; esac
  sleep 20
done
if [ "$ST" != "COMPLETED" ]; then
  databricks pipelines list-pipeline-events "$PID" -p "$PROFILE" -o json | python -c "
import sys,json
for e in json.load(sys.stdin):
    if e.get('level')=='ERROR':
        exc=(e.get('error',{}).get('exceptions') or [{}])[0].get('message','sem corpo')
        print('---', e.get('event_type'))
        print((e.get('message') or '')[:300])
        print(exc[:1200])
" | head -60
fi
