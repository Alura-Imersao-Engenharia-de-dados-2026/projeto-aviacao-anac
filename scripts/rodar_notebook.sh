#!/usr/bin/env bash
# Executa um notebook do workspace como run one-time em compute serverless.
# Uso: scripts/rodar_notebook.sh <nome-do-notebook>
set -euo pipefail
PROFILE="${DATABRICKS_CONFIG_PROFILE:-alura-imersao}"
export MSYS_NO_PATHCONV=1   # Git Bash no Windows converte /Workspace/... em C:/Program Files/...
NB="${1:?informe o nome do notebook}"
WS="${DATABRICKS_WORKSPACE_PATH:?defina DATABRICKS_WORKSPACE_PATH com a pasta dos notebooks}"
RUN=$(databricks jobs submit --json "{
  \"run_name\": \"voebem-${NB}\",
  \"tasks\": [{
    \"task_key\": \"run\",
    \"notebook_task\": {\"notebook_path\": \"${WS}/${NB}\", \"source\": \"WORKSPACE\"}
  }]
}" --no-wait -p "$PROFILE" -o json | python -c "import sys,json;print(json.load(sys.stdin)['run_id'])")
echo "run_id=${RUN}"
while :; do
  J=$(databricks jobs get-run "${RUN}" -p "$PROFILE" -o json)
  ST=$(echo "$J" | python -c "import sys,json;d=json.load(sys.stdin);s=d.get('status',{});print(s.get('state',''), (s.get('termination_details') or {}).get('code',''))")
  echo "  status: ${ST}"
  case "$ST" in TERMINATED*) break;; esac
  sleep 15
done
databricks jobs get-run "${RUN}" -p "$PROFILE" -o json | python -c "
import sys,json
d=json.load(sys.stdin)
for t in d.get('tasks',[]):
    s=t.get('status',{}) ; td=s.get('termination_details') or {}
    print('task:',t['task_key'],'->',td.get('code'),td.get('message',''))
    print('url:',t.get('run_page_url'))
"
