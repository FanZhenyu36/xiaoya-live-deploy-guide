#!/usr/bin/env bash
# Tested-target profile: RTX 5060 Ti / Python 3.12 / CUDA 13.0.
set -euo pipefail
if [[ "${1:-}" == '--help' ]]; then
  echo 'Usage: bash setup-omnivoice.sh [~/omnivoice-wsl]'; exit 0
fi
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET="${1:-$HOME/omnivoice-wsl}"
TARGET="${TARGET/#\~/$HOME}"
SOURCE="$TARGET/flashinfer-source"
REVISION='08be0b4ccbac3e13e374e86fbfead4b4cac343e2'
command -v uv >/dev/null || { echo '[ERROR] Install uv first (see README).'; exit 1; }
command -v git >/dev/null || { echo '[ERROR] Install git and ffmpeg using apt first.'; exit 1; }
command -v ffmpeg >/dev/null || { echo '[ERROR] Install ffmpeg using apt first.'; exit 1; }
mkdir -p "$TARGET"
if [[ ! -d "$SOURCE/.git" ]]; then
  [[ ! -e "$SOURCE" ]] || { echo '[ERROR] Source target exists and is not a Git repository.'; exit 1; }
  git clone --no-checkout https://github.com/k2-fsa/OmniVoice.git "$SOURCE"
  git -C "$SOURCE" checkout --detach "$REVISION"
fi
[[ "$(git -C "$SOURCE" rev-parse HEAD)" == "$REVISION" ]] || {
  echo '[ERROR] Existing source is a different revision. Preserving it; use another target directory.'; exit 1;
}
if [[ -x "$TARGET/.venv/bin/python" && ! -f "$TARGET/.guide-managed-environment" ]]; then
  echo '[ERROR] Existing unmanaged venv preserved. Choose a NEW target, e.g. ~/omnivoice-guide.'; exit 1
fi
if [[ ! -x "$TARGET/.venv/bin/python" ]]; then
  uv venv "$TARGET/.venv" --python 3.12
  touch "$TARGET/.guide-managed-environment"
fi
PYTHON="$TARGET/.venv/bin/python"
uv pip install --python "$PYTHON" 'torch==2.14.1' --index-url https://download.pytorch.org/whl/cu130
uv pip install --python "$PYTHON" -e "$SOURCE" \
  -c "$ROOT/requirements/omnivoice-tested-constraints.txt" \
  'torchaudio==2.11.1'
uv pip install --python "$PYTHON" 'flashinfer-python==0.7.2.post1' \
  'nvidia-cuda-nvcc==13.0.88' 'nvidia-cuda-crt==13.5.37' 'nvidia-nvvm==13.5.37'
uv pip install --python "$PYTHON" 'flashinfer-jit-cache==0.7.2.post1+cu130' \
  --index-url https://flashinfer.ai/whl/cu130
uv pip check --python "$PYTHON"
mkdir -p "$TARGET/guide-tools"
cp "$ROOT/scripts/wsl/check_model.py" "$ROOT/scripts/wsl/download_model.py" \
   "$ROOT/scripts/wsl/launch_omnivoice.py" "$ROOT/scripts/wsl/diagnose.py" "$TARGET/guide-tools/"
echo '[OK] Environment installed. No model was downloaded or started.'
echo '[NEXT] Run guide-tools/check_model.py, then download_model.py only if needed.'
