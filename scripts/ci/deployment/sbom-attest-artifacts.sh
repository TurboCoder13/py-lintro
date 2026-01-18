#!/usr/bin/env bash
set -euo pipefail

# sbom-attest-artifacts.sh
# Optionally attest SBOM artifacts with cosign keyless.

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	echo "Usage: $0 [OUTPUT_DIR]"
	echo ""
	echo "Create best-effort cosign attestations for SBOM artifacts."
	echo "Defaults: OUTPUT_DIR=dist/sbom"
	exit 0
fi

OUTPUT_DIR=${1:-dist/sbom}

if [ ! -d "${OUTPUT_DIR}" ]; then
	echo "SBOM output dir not found: ${OUTPUT_DIR}" >&2
	exit 1
fi

if ! command -v cosign >/dev/null 2>&1; then
	echo "cosign not installed; skipping attest"
	exit 0
fi

export COSIGN_EXPERIMENTAL=1
for f in "${OUTPUT_DIR}"/*; do
	set +e
	cosign attest --predicate <(echo '{"generated_by":"sbom-generate.sh"}') --type custom --yes "$f"
	rc=$?
	set -e
	if [ $rc -ne 0 ]; then
		echo "cosign attest failed for $f (non-fatal)" >&2
	fi
done

echo "cosign attest done for artifacts in ${OUTPUT_DIR}"
