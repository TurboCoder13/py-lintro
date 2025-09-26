#!/usr/bin/env bash
set -euo pipefail

# deployments-prune.sh
# Prune GitHub deployments using gh CLI.
#
# Supports rule types (repeatable):
#   --keep-n ENV N          Keep the newest N deployments for ENV, delete the rest
#   --keep-ref ENV REF      Keep only deployments for ENV with ref==REF, delete others
#   --keep-id ID            Keep deployment with numeric ID (can be repeated)
#   --repo OWNER/REPO       Target repository (defaults to $GITHUB_REPOSITORY)
#
# Environment:
#   DRY_RUN=1               Print what would happen without calling gh
#   GITHUB_TOKEN            Token for gh (if not already logged in)
#
# Examples:
#   DRY_RUN=1 ./deployments-prune.sh --keep-n github-pages 0 --keep-ref pypi 0.3.2
#   ./deployments-prune.sh --repo TurboCoder13/py-lintro --keep-n production 0

usage() {
  cat <<USAGE
Usage: $0 [--repo OWNER/REPO] [--keep-n ENV N] [--keep-ref ENV REF] [--keep-id ID]...

Options:
  --repo OWNER/REPO      Target repository (default: \$GITHUB_REPOSITORY)
  --keep-n ENV N         Keep newest N deployments for ENV
  --keep-ref ENV REF     Keep only deployments for ENV whose ref equals REF
  --keep-id ID           Keep deployment with numeric ID (repeatable)
  -h, --help             Show this help

Environment:
  DRY_RUN=1              Print planned actions; do not call gh
USAGE
}

REPO="${GITHUB_REPOSITORY:-}"
declare -a KEEP_N_RULES=()
declare -a KEEP_REF_RULES=()
declare -a KEEP_IDS=()

while (( "$#" )); do
  case "${1}" in
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    --keep-n)
      env_name="${2:-}"; n_keep="${3:-}"
      if [[ -z "$env_name" || -z "$n_keep" ]]; then usage; exit 2; fi
      KEEP_N_RULES+=("${env_name}:${n_keep}")
      shift 3
      ;;
    --keep-ref)
      env_name="${2:-}"; ref_keep="${3:-}"
      if [[ -z "$env_name" || -z "$ref_keep" ]]; then usage; exit 2; fi
      KEEP_REF_RULES+=("${env_name}:${ref_keep}")
      shift 3
      ;;
    --keep-id)
      id_keep="${2:-}"
      if [[ -z "$id_keep" ]]; then usage; exit 2; fi
      KEEP_IDS+=("${id_keep}")
      shift 2
      ;;
    -h|--help)
      usage; exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2; usage; exit 2
      ;;
  esac
done

if [[ -z "$REPO" ]]; then
  echo "--repo not provided and GITHUB_REPOSITORY is empty" >&2
  exit 2
fi

DRY_RUN="${DRY_RUN:-0}"

need_bin() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 2; }
}

if [[ "$DRY_RUN" != "1" ]]; then
  need_bin gh
  need_bin jq
fi

echo "Target repo: ${REPO}"

should_keep_id() {
  local id="$1"
  for kid in "${KEEP_IDS[@]:-}"; do
    [[ -z "$kid" ]] && continue
    if [[ "$id" == "$kid" ]]; then
      return 0
    fi
  done
  return 1
}

keep_ref() {
  local env_name="$1" ref_keep="$2"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] Would keep only ref='${ref_keep}' in env='${env_name}', delete others"
    return 0
  fi
  ids_json=$(gh api --paginate -H "Accept: application/vnd.github+json" \
    "repos/${REPO}/deployments" --jq \
    ".[] | select(.environment==\"${env_name}\") | {id,created_at,ref}")
  # shellcheck disable=SC2016
  to_del=$(printf '%s\n' "${ids_json}" | jq -s \
    --arg REF "${ref_keep}" 'sort_by(.created_at) | reverse | map(select(.ref != $REF)) | .[].id')
  for id in ${to_del}; do
    id_clean="${id//\"/}"
    if should_keep_id "$id_clean"; then
      echo "[keep-id] Preserving deployment id=${id_clean}"
      continue
    fi
    gh api -X POST -H "Accept: application/vnd.github.ant-man-preview+json" \
      "repos/${REPO}/deployments/${id_clean}/statuses" -f state=inactive >/dev/null 2>&1 || true
    gh api -X DELETE -H "Accept: application/vnd.github+json" \
      "repos/${REPO}/deployments/${id_clean}" >/dev/null 2>&1 || true
  done
}

keep_n() {
  local env_name="$1" n_keep="$2"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] Would keep newest ${n_keep} in env='${env_name}', delete the rest"
    return 0
  fi
  ids=$(gh api --paginate -H "Accept: application/vnd.github+json" \
    "repos/${REPO}/deployments" --jq \
    ".[] | select(.environment==\"${env_name}\") | {id,created_at}" \
    | jq -s 'sort_by(.created_at) | reverse' | jq -r '.[].id')
  i=0
  for id in ${ids}; do
    i=$((i+1))
    if [[ ${i} -le ${n_keep} ]]; then continue; fi
    if should_keep_id "$id"; then
      echo "[keep-id] Preserving deployment id=${id}"
      continue
    fi
    gh api -X POST -H "Accept: application/vnd.github.ant-man-preview+json" \
      "repos/${REPO}/deployments/${id}/statuses" -f state=inactive >/dev/null 2>&1 || true
    gh api -X DELETE -H "Accept: application/vnd.github+json" \
      "repos/${REPO}/deployments/${id}" >/dev/null 2>&1 || true
  done
}

# Apply keep-ref rules first, then keep-n rules
for rule in "${KEEP_REF_RULES[@]:-}"; do
  [[ -z "$rule" ]] && continue
  env_name="${rule%%:*}"; ref_keep="${rule#*:}"
  echo "Applying keep-ref: env='${env_name}' ref='${ref_keep}'"
  keep_ref "${env_name}" "${ref_keep}"
done

for rule in "${KEEP_N_RULES[@]:-}"; do
  [[ -z "$rule" ]] && continue
  env_name="${rule%%:*}"; n_keep="${rule#*:}"
  echo "Applying keep-n: env='${env_name}' n='${n_keep}'"
  keep_n "${env_name}" "${n_keep}"
done

echo "Done."


