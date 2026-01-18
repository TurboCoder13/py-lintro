#!/usr/bin/env bash
set -euo pipefail

# sbom-rename-artifacts.sh
# Rename SBOM artifacts to include tag and short SHA for traceability.

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	echo "Usage: $0 [OUTPUT_DIR]"
	echo ""
	echo "Rename SBOM files to include tag and short SHA prefix."
	echo "Defaults: OUTPUT_DIR=dist/sbom"
	exit 0
fi

TAG="${GITHUB_REF_NAME:-${TAG:-unknown}}"
SHA_SHORT="${GITHUB_SHA:-${SHA:-unknown}}"
SHA_SHORT="${SHA_SHORT:0:12}"

OUTPUT_DIR=${1:-dist/sbom}

if [ ! -d "${OUTPUT_DIR}" ]; then
	echo "SBOM output dir not found: ${OUTPUT_DIR}" >&2
	exit 1
fi

shopt -s nullglob
for f in "${OUTPUT_DIR}/py-lintro-sbom."*; do
	base=$(basename "$f")
	mv "$f" "${OUTPUT_DIR}/${TAG}-${SHA_SHORT}-${base}"
done

echo "Renamed SBOM artifacts in ${OUTPUT_DIR} with ${TAG}-${SHA_SHORT}- prefix"
