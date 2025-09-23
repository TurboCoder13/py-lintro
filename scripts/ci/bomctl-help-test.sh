#!/bin/bash
#
# Test bomctl binary by displaying first 40 lines of help output
#
# Usage: scripts/ci/bomctl-help-test.sh

set -euo pipefail

# Source common utilities for consistent logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
# shellcheck source=../utils/utils.sh
source "${SCRIPT_DIR}/../utils/utils.sh"

main() {
    log_info "Testing bomctl binary installation"
    
    if ! command -v bomctl &> /dev/null; then
        log_error "bomctl not found in PATH"
        return 1
    fi
    
    log_info "Running bomctl --help (first 40 lines)"
    bomctl --help | sed -n '1,40p'
    
    log_success "bomctl binary test completed"
}

main "$@"
