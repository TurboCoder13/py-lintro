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
  # Select a release version (override via UV_VERSION env); default to latest
  UV_VERSION_INPUT="${UV_VERSION:-}"
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "${tmpdir}"' EXIT
  # Detect platform (Linux x86_64 expected in CI)
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"
  case "${arch}" in
    x86_64|amd64) arch_pat="x86_64|amd64" ;;
    aarch64|arm64) arch_pat="aarch64|arm64" ;;
    *) arch_pat="${arch}" ;;
  esac
  # Resolve release JSON (latest if no UV_VERSION provided)
  if [ -n "${UV_VERSION_INPUT}" ]; then
    release_json="$(gh release view "${UV_VERSION_INPUT}" -R astral-sh/uv --json tagName,assets || true)"
  else
    release_json="$(gh release view -R astral-sh/uv --json tagName,assets || true)"
  fi
  tag_name="$(printf '%s' "${release_json}" | jq -r '.tagName // empty')"
  if [ -z "${tag_name}" ]; then
    echo "[setup] Unable to resolve uv release (tag not found)." >&2
    echo "[setup] You can set UV_VERSION to a valid tag (e.g., '0.5.1' or 'v0.5.1')." >&2
    exit 1
  fi
  echo "[setup] Resolved uv release tag: ${tag_name}"
  # Determine a download pattern to match Linux assets (.tar.gz or .tar.xz)
  case "${os}" in
    linux) os_pat="linux" ;;
    darwin) os_pat="darwin|apple|macos" ;;
    *) os_pat="${os}" ;;
  esac
  # Try gz first then xz
  pattern_gz="*${os_pat}*${arch_pat}*.tar.gz"
  pattern_xz="*${os_pat}*${arch_pat}*.tar.xz"
  echo "[setup] Downloading uv asset matching: ${pattern_gz} (fallback: ${pattern_xz})"
  if gh release download "${tag_name}" -R astral-sh/uv -p "${pattern_gz}" -O "${tmpdir}/uv.tgz"; then
    archive_ext="gz"
  elif gh release download "${tag_name}" -R astral-sh/uv -p "${pattern_xz}" -O "${tmpdir}/uv.txz"; then
    archive_ext="xz"
  else
    echo "[setup] Failed to find a matching uv asset for ${os}/${arch} in ${tag_name}" >&2
    printf '%s' "${release_json}" | jq '.assets[].name' -r >&2 || true
    exit 1
  fi
  if [ "${archive_ext}" = "gz" ]; then
    tar -C "${tmpdir}" -xzf "${tmpdir}/uv.tgz" uv
  else
    tar -C "${tmpdir}" -xJf "${tmpdir}/uv.txz" uv
  fi
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

echo "[setup] Ensuring Python ${REQ_PY_VER} via uv"
uv python install "${REQ_PY_VER}"
echo "UV_PYTHON=${REQ_PY_VER}" >> "${GITHUB_ENV:-/dev/null}" || true

echo "[setup] Syncing Python dependencies (dev)..."
uv sync --dev --no-progress

echo "[setup] Installing external tools (hadolint, prettier, ruff, yamllint, darglint)..."
./scripts/utils/install-tools.sh --local

# Ensure local bin is persisted in PATH for downstream steps in GitHub Actions
if [ -n "$GITHUB_PATH" ] && [ -d "$HOME/.local/bin" ]; then
  echo "$HOME/.local/bin" >> "$GITHUB_PATH"
fi

echo "[setup] Environment bootstrap complete."


