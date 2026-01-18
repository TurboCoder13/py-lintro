#!/usr/bin/env bash
set -euo pipefail

# sign-all-tags.sh — (Re)sign Git tags safely
#
# - Detects unsigned (or all, with --resign-all) tags and recreates them
#   as signed annotated tags pointing to the same target object.
# - Supports SSH or GPG signing based on your git config (gpg.format).
# - Dry-run by default; requires --write to make changes.
# - Optionally pushes only the changed tags with --push.
#
# Usage:
#   scripts/local/sign-all-tags.sh [--pattern 'v*'] [--resign-all] [--write] [--push]
#
# Notes:
# - For SSH signing, ensure:
#     git config --global gpg.format ssh
#     git config --global user.signingkey /path/to/public/key.pub
#     git config --global gpg.ssh.allowedSignersFile ~/.ssh/allowed_signers
# - For GPG signing, ensure user.signingkey and gpg-agent are configured.

PATTERN="*"  # tag glob
RESIGN_ALL=0 # 1 = re-sign even if already signed
DO_WRITE=0   # 1 = actually update tags
DO_PUSH=0    # 1 = push updated tags to origin

while [[ $# -gt 0 ]]; do
	case "$1" in
	--pattern)
		PATTERN="${2:-*}"
		shift 2
		;;
	--resign-all)
		RESIGN_ALL=1
		shift
		;;
	--write)
		DO_WRITE=1
		shift
		;;
	--push)
		DO_PUSH=1
		shift
		;;
	-h | --help)
		sed -n '1,80p' "$0"
		exit 0
		;;
	*)
		echo "[err] Unknown arg: $1" >&2
		exit 2
		;;
	esac
done

echo "[info] Fetching tags from origin..."
git fetch --tags --no-tags origin >/dev/null 2>&1 || true

fmt=$(git config --get gpg.format || echo "gpg")
echo "[info] Detected git signing format: ${fmt}"

# Collect tags (portable; works with older macOS bash)
TAGS=$(git tag --list "${PATTERN}" | sort -V)
if [[ -z "${TAGS}" ]]; then
	echo "[info] No tags match pattern '${PATTERN}'. Nothing to do."
	exit 0
fi

updated_tags=""

is_signed() {
	local tag=$1
	# Only annotated tags can be signed. Lightweight tags are never signed.
	if [[ $(git cat-file -t "$tag") != "tag" ]]; then
		return 1
	fi
	# Inspect tag payload for signature blocks (PGP or SSH)
	if git cat-file -p "$tag" | grep -qE -- '-----BEGIN (PGP|SSH) SIGNATURE-----'; then
		return 0
	fi
	return 1
}

get_message() {
	local tag=$1
	# %(contents) returns the tag message without the signature block.
	git for-each-ref "refs/tags/${tag}" --format='%(contents)' 2>/dev/null || true
}

for tag in ${TAGS}; do
	target=$(git rev-list -n1 "$tag")
	type=$(git cat-file -t "$tag") # 'tag' for annotated, else 'commit' for lightweight

	signed=1
	if is_signed "$tag"; then signed=0; fi

	action="skip"
	if ((RESIGN_ALL)); then
		action="resign"
	else
		if ((signed != 0)); then
			action="sign"
		fi
	fi

	msg=$(get_message "$tag")
	if [[ -z "$msg" ]]; then msg="$tag"; fi

	printf "[tag] %-20s type=%-9s signed=%-3s → %s\n" "$tag" "$type" "$([[ $signed -eq 0 ]] && echo yes || echo no)" "$action"

	if [[ "$action" == "skip" ]]; then
		continue
	fi

	if ((DO_WRITE)); then
		# Recreate as signed annotated tag pointing to the same target
		git tag -s -f -m "$msg" "$tag" "$target"
		updated_tags+=" $tag"
	fi
done

if ((DO_WRITE)); then
	if [[ -z "${updated_tags// /}" ]]; then
		echo "[info] No tags updated."
	else
		echo "[info] Updated tag(s):${updated_tags}"
		if ((DO_PUSH)); then
			echo "[info] Pushing updated tags to origin..."
			# Push only those we changed
			git push origin ${updated_tags}
		else
			echo "[hint] To push: git push origin${updated_tags}"
		fi
	fi
else
	echo "[dry-run] Use --write to apply changes, --push to push updated tags."
fi

exit 0
