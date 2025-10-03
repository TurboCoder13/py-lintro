#!/bin/bash

# Shared utilities for workflow scripts
# This file contains common functions and variables used across multiple scripts

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Common exclude directories for lintro
EXCLUDE_DIRS=".git,__pycache__,htmlcov,.pytest_cache,.mypy_cache,dist,build,node_modules,.venv,venv,.tox,coverage-report,lintro-report"

# Common environment variables
GITHUB_SERVER_URL="${GITHUB_SERVER_URL:-https://github.com}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-}"
GITHUB_RUN_ID="${GITHUB_RUN_ID:-}"
GITHUB_SHA="${GITHUB_SHA:-}"

# Function to check if we're in a PR context
is_pr_context() {
    [ "${GITHUB_EVENT_NAME:-}" = "pull_request" ]
}

# Function to log messages with colors
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_verbose() {
    [ "${VERBOSE:-0}" -eq 1 ] && echo -e "${BLUE}[verbose] $1${NC}" || true
}

# Function to generate PR comment file
generate_pr_comment() {
    local title="$1"
    local status="$2"
    local content="$3"
    local output_file="$4"
    
    local comment="## $title

This PR has been analyzed using **lintro** - our unified code quality tool.

### 📊 Status: $status

$content

---
🔗 **[View full build details]($GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID)**

*This analysis was performed automatically by the CI pipeline.*"

    echo "$comment" > "$output_file"
    log_success "PR comment generated and saved to $output_file"
}

# Function to handle coverage percentage
get_coverage_value() {
    local coverage_percentage="${COVERAGE_PERCENTAGE:-0.0}"
    
    # Handle case where coverage might be empty or undefined
    if [ -z "$coverage_percentage" ] || [ "$coverage_percentage" = "0.0" ]; then
        echo "0.0"
    else
        echo "$coverage_percentage"
    fi
}

# Function to determine coverage status
get_coverage_status() {
    local coverage_value="$1"
    local threshold="${2:-80}"
    
    # Portable numeric comparison without requiring bc
    awk -v c="$coverage_value" -v t="$threshold" 'BEGIN{ exit (c>=t)?0:1 }' && echo "✅" || echo "⚠️"
}

# Function to run lintro with common options
run_lintro() {
    local command="$1"
    local format="${2:-grid}"
    local exclude="${3:-$EXCLUDE_DIRS}"
    
    if [ -n "$exclude" ]; then
        uv run lintro "$command" . --exclude "$exclude"
    else
        uv run lintro "$command" .
    fi
}

# Function to check if file exists and log result
check_file_exists() {
    local file="$1"
    local description="$2"
    
    if [ -f "$file" ]; then
        log_success "$description found"
        echo "File size: $(wc -c < "$file") bytes"
        return 0
    else
        log_warning "$description not found"
        return 1
    fi
}

# Function to check if directory exists and log result
check_dir_exists() {
    local dir="$1"
    local description="$2"
    
    if [ -d "$dir" ]; then
        log_success "$description found"
        echo "Files in $dir:"
        ls -la "$dir/"
        return 0
    else
        log_warning "$description not found"
        return 1
    fi
} 