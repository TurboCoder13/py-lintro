#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Load security profile endpoints from centralized configuration

set -euo pipefail

readonly CONFIG_FILE=".github/data/security-config.yml"

usage() {
    cat << EOF
Usage: $0 PROFILE_NAME

Load endpoints for a security profile from .github/data/security-config.yml

Arguments:
    PROFILE_NAME    Security profile to load (e.g., python_workflow, basic, etc.)

Output:
    endpoints=SPACE_SEPARATED_ENDPOINTS (GitHub Actions format)

Examples:
    $0 basic
    $0 python_workflow
    $0 docker_workflow

EOF
}

load_profile_with_yq() {
    local profile="$1"
    local config_file="$2"
    
    # Check if profile exists
    if ! yq eval ".profiles | has(\"$profile\")" "$config_file" >/dev/null 2>&1 || [[ "$(yq eval ".profiles | has(\"$profile\")" "$config_file" 2>/dev/null)" != "true" ]]; then
        echo "❌ Security profile \"$profile\" not found in configuration" >&2
        exit 1
    fi
    
    # Get endpoint groups for this profile
    local endpoint_groups
    endpoint_groups=$(yq eval ".profiles.${profile}.endpoints[]" "$config_file" 2>/dev/null)
    
    if [[ -z "$endpoint_groups" ]]; then
        echo "❌ No endpoint groups defined for profile \"$profile\"" >&2
        exit 1
    fi
    
    # Collect all endpoints from the groups
    local all_endpoints=()
    while IFS= read -r group; do
        if [[ -n "$group" ]]; then
            # Check if endpoint group exists
            if ! yq eval ".endpoints | has(\"$group\")" "$config_file" >/dev/null 2>&1 || [[ "$(yq eval ".endpoints | has(\"$group\")" "$config_file" 2>/dev/null)" != "true" ]]; then
                echo "❌ Endpoint group \"$group\" not found in configuration" >&2
                exit 1
            fi
            
            # shellcheck disable=SC2207
            local group_endpoints=($(yq eval ".endpoints.${group}[]" "$config_file" 2>/dev/null))
            all_endpoints+=("${group_endpoints[@]}")
        fi
    done <<< "$endpoint_groups"
    
    # Remove duplicates and output in GitHub Actions format
    local endpoints_list
    endpoints_list=$(printf "%s " "${all_endpoints[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' ' | sed 's/ $//')
    echo "endpoints=$endpoints_list"
}

load_profile_with_python() {
    local profile="$1"
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    uv run python "$script_dir/load-security-profile.py" "$profile"
}

main() {
    local profile="${1:-}"
    
    if [[ -z "$profile" ]]; then
        usage
        exit 1
    fi
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "❌ Security configuration file not found: $CONFIG_FILE" >&2
        echo "The centralized security configuration is required." >&2
        exit 1
    fi
    
    # Use Python script if uv and PyYAML available, otherwise yq, otherwise fail
    if command -v uv >/dev/null 2>&1 && uv run python -c "import yaml" >/dev/null 2>&1; then
        load_profile_with_python "$profile"
    elif command -v yq >/dev/null 2>&1; then
        load_profile_with_yq "$profile" "$CONFIG_FILE"
    else
        echo "❌ No YAML parser available (uv with PyYAML or yq required)" >&2
        echo "Install uv with PyYAML or yq to use centralized security configuration." >&2
        exit 1
    fi
}

main "$@"
