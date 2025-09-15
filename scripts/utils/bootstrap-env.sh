#!/usr/bin/env bash
set -euo pipefail

# bootstrap-env.sh - Ensure Python env tools and project deps are installed
# - Installs uv if missing (policy-compliant via pip; no curl)
# - Ensures requested Python version is available via uv
# - Syncs Python dependencies (dev)
# - Installs external tools used by Lintro
# - Ensures ~/.local/bin is on PATH for the current workflow

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
Bootstraps CI environment with Python, uv, and external tools.

Usage:
  scripts/utils/bootstrap-env.sh [--help|-h] [PYTHON_VERSION]

Actions:
  - Install uv if missing and add ~/.local/bin to PATH
  - Ensure specified Python via 'uv python install'
  - uv sync --dev --no-progress
  - ./scripts/utils/install-tools.sh --local
  - Persist ~/.local/bin to GITHUB_PATH when available
EOF
  exit 0
fi

REQ_PY_VER="${1:-3.13}"
echo "[setup] Bootstrapping environment (Python ${REQ_PY_VER})..."

# Ensure uv is available with egress-friendly install (GitHub Releases)
if ! command -v uv >/dev/null 2>&1; then
  echo "[setup] 'uv' not found; installing from GitHub Releases (binary)"
  # Prefer GitHub CLI to avoid non-GitHub endpoints under egress block
  if ! command -v gh >/dev/null 2>&1; then
    echo "[setup] gh CLI is required to install 'uv' from GitHub releases" >&2
    exit 1
  fi
  # Map token for gh if provided by Actions
  if [ -z "${GH_TOKEN:-}" ] && [ -n "${GITHUB_TOKEN:-}" ]; then
    export GH_TOKEN="${GITHUB_TOKEN}"
  fi
  # Minimal CI-focused implementation: Linux x86_64 latest (or UV_VERSION)
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "${tmpdir}"' EXIT
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"
  if [ "${os}" != "linux" ] || ! echo "${arch}" | grep -Eq '^(x86_64|amd64)$'; then
    echo "[setup] Unsupported platform ${os}/${arch} for automatic uv bootstrap." >&2
    echo "[setup] Please pre-install 'uv' or set UV_VERSION and extend triples if needed." >&2
    exit 1
  fi
  tag_name="${UV_VERSION:-$(gh release view -R astral-sh/uv --json tagName --jq '.tagName' 2>/dev/null || true)}"
  if [ -z "${tag_name}" ]; then
    echo "[setup] Unable to resolve uv release tag (try setting UV_VERSION)." >&2
    exit 1
  fi
  echo "[setup] Resolved uv release tag: ${tag_name}"
  primary="uv-x86_64-unknown-linux-gnu.tar.gz"
  fallback="uv-x86_64-unknown-linux-musl.tar.gz"
  if gh release download "${tag_name}" -R astral-sh/uv -p "${primary}" -O "${tmpdir}/uv.tgz"; then
    :
  elif gh release download "${tag_name}" -R astral-sh/uv -p "${fallback}" -O "${tmpdir}/uv.tgz"; then
    :
  else
    echo "[setup] Failed to download uv asset (${primary} or ${fallback}) for ${tag_name}" >&2
    gh release view "${tag_name}" -R astral-sh/uv --json assets --jq '.assets[].name' || true
    exit 1
  fi
  tar -C "${tmpdir}" -xzf "${tmpdir}/uv.tgz" uv
  # Install to user bin when not root; fall back to /usr/local/bin
  if install -m 0755 "${tmpdir}/uv" "$HOME/.local/bin/uv" 2>/dev/null; then
    :
  else
    sudo install -m 0755 "${tmpdir}/uv" /usr/local/bin/uv
  fi
  if [ -n "${GITHUB_PATH:-}" ] && [ -d "$HOME/.local/bin" ]; then
    echo "$HOME/.local/bin" >> "$GITHUB_PATH"
  fi
  if ! command -v uv >/dev/null 2>&1; then
    echo "[setup] Failed to provision 'uv' from GitHub releases" >&2
    exit 1
  fi
fi

if [ "${BOOTSTRAP_SKIP_SYNC:-0}" -ne 1 ]; then
  echo "[setup] Ensuring Python ${REQ_PY_VER} via uv"
  uv python install "${REQ_PY_VER}"
  echo "UV_PYTHON=${REQ_PY_VER}" >> "${GITHUB_ENV:-/dev/null}" || true

  echo "[setup] Syncing Python dependencies (dev)..."
  uv sync --dev --no-progress
else
  echo "[setup] Skipping uv python install and sync (BOOTSTRAP_SKIP_SYNC=1)"
fi

if [ "${BOOTSTRAP_SKIP_INSTALL_TOOLS:-0}" -ne 1 ]; then
  echo "[setup] Installing external tools (hadolint, prettier, ruff, yamllint, darglint)..."
  ./scripts/utils/install-tools.sh --local
else
  echo "[setup] Skipping external tools install (BOOTSTRAP_SKIP_INSTALL_TOOLS=1)"
fi

# Ensure local bin is persisted in PATH for downstream steps in GitHub Actions
if [ -n "$GITHUB_PATH" ] && [ -d "$HOME/.local/bin" ]; then
  echo "$HOME/.local/bin" >> "$GITHUB_PATH"
fi

echo "[setup] Environment bootstrap complete."


