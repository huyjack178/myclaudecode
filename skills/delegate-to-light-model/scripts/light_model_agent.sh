#!/usr/bin/env bash
set -euo pipefail

env_file="$HOME/.config/llm-proxy/light_model.env"
if [[ -f "$env_file" ]]; then
  while IFS='=' read -r name value; do
    [[ -z "$name" || "$name" == \#* ]] && continue
    [[ -z "${!name:-}" ]] && export "$name=$value"
  done < "$env_file"
fi

if [[ -z "${LIGHT_MODEL_PROXY_URL:-}" || -z "${LIGHT_MODEL_PROXY_KEY:-}" ]]; then
  echo "LIGHT_MODEL_PROXY_URL and LIGHT_MODEL_PROXY_KEY must be set (env or $env_file)." >&2
  exit 2
fi

if [[ -n "${LIGHT_MODEL_AGENT_ACTIVE:-}" ]]; then
  echo "Already inside a light-model agent run; refusing to nest." >&2
  exit 3
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: light_model_agent.sh \"<task>\" [extra claude -p flags...]" >&2
  exit 2
fi

task="$1"
shift
model="${LIGHT_MODEL_AGENT_MODEL:-claude-haiku-5-5}"

exec env -u ANTHROPIC_API_KEY \
  LIGHT_MODEL_AGENT_ACTIVE=1 \
  ANTHROPIC_BASE_URL="$LIGHT_MODEL_PROXY_URL" \
  ANTHROPIC_AUTH_TOKEN="$LIGHT_MODEL_PROXY_KEY" \
  ANTHROPIC_MODEL="$model" \
  ANTHROPIC_DEFAULT_OPUS_MODEL="$model" \
  ANTHROPIC_DEFAULT_SONNET_MODEL="$model" \
  ANTHROPIC_DEFAULT_HAIKU_MODEL="$model" \
  CLAUDE_CODE_SUBAGENT_MODEL="$model" \
  CLAUDE_CODE_MAX_CONTEXT_TOKENS="${LIGHT_MODEL_AGENT_CONTEXT_TOKENS:-100000}" \
  claude -p "$task" --permission-mode acceptEdits "$@"
