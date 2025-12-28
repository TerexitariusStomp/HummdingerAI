#!/usr/bin/env bash
set -euo pipefail

# Sync helper to pull latest versions of upstream dependencies so this project stays current.
# - If ELIZAOS_PATH / HUMMINGBOT_PATH / FLASHBOTS_PATH point to git clones, we git pull them.
# - Otherwise we upgrade pip packages (best-effort).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[update] Using venv at .venv if present"
if [[ -d ".venv" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

update_git_repo() {
  local path="$1"
  local name="$2"
  if [[ -d "$path/.git" ]]; then
    echo "[update] Pulling latest for $name at $path"
    git -C "$path" pull --ff-only
  else
    echo "[warn] $name path $path is not a git repo; skipping pull"
  fi
}

if [[ -n "${ELIZAOS_PATH:-}" ]]; then
  update_git_repo "$ELIZAOS_PATH" "ElizaOS"
else
  echo "[update] Upgrading eliza (pip) if installed"
  pip install --upgrade eliza || true
fi

if [[ -n "${HUMMINGBOT_PATH:-}" ]]; then
  update_git_repo "$HUMMINGBOT_PATH" "Hummingbot"
else
  echo "[update] Upgrade Hummingbot package (pip) if available"
  pip install --upgrade hummingbot || true
fi

if [[ -n "${FLASHBOTS_PATH:-}" ]]; then
  update_git_repo "$FLASHBOTS_PATH" "Flashbots"
else
  echo "[update] Upgrade flashbots + eth-account (pip)"
  pip install --upgrade flashbots eth-account || true
fi

echo "[update] Upgrade core Python deps"
pip install --upgrade ccxt streamlit web3 tenacity pydantic python-dotenv requests aiohttp

echo "[done] Upstreams refreshed."
