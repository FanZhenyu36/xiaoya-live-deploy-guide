#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == '--help' ]]; then
  echo 'Usage: bash start-omnivoice.sh [~/omnivoice-wsl]'; exit 0
fi
TARGET="${1:-$HOME/omnivoice-wsl}"
TARGET="${TARGET/#\~/$HOME}"
cd "$TARGET"
[[ -x .venv/bin/python && -f guide-tools/launch_omnivoice.py ]] || {
  echo '[ERROR] Run setup-omnivoice.sh first. Existing installations are not changed automatically.'; exit 1;
}
export PATH="$TARGET/.venv/bin:$PATH"
export PYTHONPATH="$TARGET/flashinfer-source${PYTHONPATH:+:$PYTHONPATH}"
export NO_PROXY="localhost,127.0.0.1,::1,0.0.0.0${NO_PROXY:+,$NO_PROXY}"
export no_proxy="$NO_PROXY"
NVCC="$(find "$TARGET/.venv" -path '*/bin/nvcc' -type f -print -quit)"
[[ -n "$NVCC" ]] || { echo '[ERROR] No nvcc in this venv. See FlashInfer chapter.'; exit 1; }
export CUDA_HOME="$(dirname "$(dirname "$NVCC")")"
export PATH="$CUDA_HOME/bin:$PATH"
export OMNIVOICE_MODEL="$(.venv/bin/python guide-tools/check_model.py --model "${OMNIVOICE_MODEL:-}")"
ARGS=()
if [[ "${OMNI_FLASHINFER:-1}" == '0' ]]; then
  ARGS+=(--no-flashinfer)
elif [[ "${OMNI_CUDA_GRAPH:-1}" == '1' ]]; then
  ARGS+=(--cuda-graph --graph-buckets "${OMNI_GRAPH_BUCKETS:-5,10}")
fi
echo "[INFO] CUDA_HOME=$CUDA_HOME"
"$CUDA_HOME/bin/nvcc" --version
exec .venv/bin/python -u guide-tools/launch_omnivoice.py "${ARGS[@]}"
