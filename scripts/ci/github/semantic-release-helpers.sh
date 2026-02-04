#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
semantic-release helper functions:
  fail_no_tag_baseline
  read_current_version
  skip_no_new_version <next> <current>
  update_version_files <version>
  update_tools_digest
  install_external_tools
  merge_release_pr <pr-number>
EOF
	exit 0
fi

fail_no_tag_baseline() {
	echo "No v*-prefixed tag found. Please create a release tag (e.g., v0.4.0) before running." >&2
	exit 2
}

read_current_version() {
	echo "current_version=$(uv run python scripts/utils/extract-version.py | sed 's/^version=//')" >>"$GITHUB_OUTPUT"
}

skip_no_new_version() {
	echo "No new version to release (next='${1}', current='${2}'). Skipping."
}

update_version_files() {
	local version="$1"
	uv run python scripts/utils/update-version.py "$version"
}

install_external_tools() {
	./scripts/utils/install-tools.sh --local
	echo "$HOME/.local/bin" >>"$GITHUB_PATH"
}

merge_release_pr() {
	local pr_number="$1"
	gh pr merge --auto --squash "$pr_number" || true
}

update_tools_digest() {
	local image="ghcr.io/lgtm-hq/lintro-tools:latest"
	local script_dir
	script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

	echo "Fetching latest tools image digest..."
	docker pull "$image"

	local digest
	digest=$(docker inspect --format='{{index .RepoDigests 0}}' "$image" | sed 's/.*@//')

	# Validate digest is non-empty and looks like a proper sha256 digest
	if [[ -z "$digest" ]]; then
		echo "ERROR: Failed to extract digest for image '$image' - digest is empty" >&2
		exit 1
	fi
	if [[ ! "$digest" =~ ^sha256:[a-f0-9]{64}$ ]]; then
		echo "ERROR: Invalid digest format for image '$image': '$digest'" >&2
		echo "       Expected format: sha256:<64-hex-chars>" >&2
		exit 1
	fi

	echo "Tools image digest: $digest"
	"$script_dir/../tools-image-update-digest.sh" "$digest"
}

# Call the specified function with its arguments
"$@"
