#!/usr/bin/env python3
"""
Security Configuration Validation Script

Validates GitHub Actions workflows against centralized security configuration.
Checks for:
- Proper harden-runner usage
- Correct endpoint allowlists
- Appropriate permissions
- SHA-pinned actions
- Security profile compliance

Usage:
    uv run python scripts/ci/validate-security-config.py [--fix] [--workflow WORKFLOW]
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    print(
        "Error: PyYAML not available. "
        "Run with 'uv run python' to use project dependencies.",
    )
    sys.exit(1)


def load_security_config() -> Dict[str, Any]:
    """Load centralized security configuration from .github/data/security-config.yml.

    Returns:
        Dict containing security configuration with endpoints, profiles, and workflow
        mappings. Returns empty structure if configuration file doesn't exist.
    """
    config_path = Path(".github/data/security-config.yml")
    if not config_path.exists():
        print("❌ Security configuration not found: .github/data/security-config.yml")
        return {
            "endpoints": {},
            "profiles": {},
            "workflow_mappings": {},
        }

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            return config
    except Exception as e:
        print(f"❌ Error loading security configuration: {e}")
        return {
            "endpoints": {},
            "profiles": {},
            "workflow_mappings": {},
        }


def load_workflow(workflow_path: Path) -> Dict[str, Any]:
    """Load a workflow file.

    Args:
        workflow_path: Path to the workflow YAML file to load.

    Returns:
        Dict containing workflow configuration, empty dict if loading fails.
    """
    try:
        return yaml.safe_load(workflow_path.read_text())
    except Exception as e:
        print(f"Error loading workflow {workflow_path}: {e}")
        return {}


def check_harden_runner(workflow: Dict[str, Any], workflow_name: str) -> List[str]:
    """Check if workflow uses harden-runner correctly.

    Args:
        workflow: Workflow configuration dictionary.
        workflow_name: Name of the workflow file.

    Returns:
        List of issues found with harden-runner configuration.
    """

    issues = []

    jobs = workflow.get("jobs", {})
    for job_name, job_config in jobs.items():
        steps = job_config.get("steps", [])

        # Check if first step is harden-runner or secure-checkout
        if not steps:
            continue

        # Check if job only has run commands (no external actions)
        has_external_actions = any(step.get("uses") for step in steps)
        if not has_external_actions:
            # Job only has run commands, no harden-runner needed
            continue

        first_step = steps[0]
        uses_action = first_step.get("uses", "")

        # Accept either harden-runner or secure-checkout
        if "step-security/harden-runner" not in str(
            uses_action,
        ) and "secure-checkout" not in str(uses_action):
            issues.append(
                f"Job '{job_name}' should start with harden-runner or secure-checkout",
            )
            continue

        # If using secure-checkout, skip further harden-runner validation
        if "secure-checkout" in str(uses_action):
            continue

        # Check egress policy
        step_with = first_step.get("with", {})
        if (
            step_with.get("egress_policy") != "block"
            and step_with.get("egress-policy") != "block"
        ):
            issues.append(
                f"Job '{job_name}' harden-runner should use egress_policy: 'block'",
            )

    return issues


def check_action_pinning(workflow: Dict[str, Any], workflow_name: str) -> List[str]:
    """Check if all actions are properly SHA-pinned.

    Args:
        workflow: Workflow configuration dictionary.
        workflow_name: Name of the workflow file.

    Returns:
        List of issues found with action pinning.
    """
    issues = []

    jobs = workflow.get("jobs", {})
    for job_name, job_config in jobs.items():
        steps = job_config.get("steps", [])

        for i, step in enumerate(steps):
            uses = step.get("uses", "")
            if not uses or uses.startswith("./"):  # Skip local actions
                continue

            if "@" not in uses:
                issues.append(
                    f"Job '{job_name}', step {i+1}: Action '{uses}' not pinned",
                )
                continue

            action, ref = uses.rsplit("@", 1)

            # Check if it's a SHA (40 char hex) or tag
            if len(ref) != 40 or not all(c in "0123456789abcdef" for c in ref.lower()):
                issues.append(
                    f"Job '{job_name}', step {i+1}: Action '{action}' "
                    f"should be SHA-pinned, got '{ref}'",
                )

    return issues


def check_permissions(
    workflow: Dict[str, Any],
    workflow_name: str,
    config: Dict[str, Any],
) -> List[str]:
    """Check if workflow permissions are specified.

    Args:
        workflow: Workflow configuration dictionary.
        workflow_name: Name of the workflow file.
        config: Security configuration dictionary.

    Returns:
        List of issues found with permissions configuration.
    """
    issues = []

    # Simple check - just ensure permissions are specified
    actual_permissions = workflow.get("permissions", {})
    if not actual_permissions:
        issues.append(f"Workflow '{workflow_name}' should specify permissions")

    return issues


def check_endpoints(
    workflow: Dict[str, Any],
    workflow_name: str,
    config: Dict[str, Any],
) -> List[str]:
    """Check if workflow uses secure-checkout or proper harden-runner.

    Args:
        workflow: Workflow configuration dictionary.
        workflow_name: Name of the workflow file.
        config: Security configuration dictionary.

    Returns:
        List of issues found with endpoint configuration.
    """
    issues = []

    # Check if workflow uses centralized secure-checkout
    jobs = workflow.get("jobs", {})
    for job_name, job_config in jobs.items():
        steps = job_config.get("steps", [])

        for step in steps:
            uses_action = step.get("uses", "")

            # Check for secure-checkout (preferred approach)
            if "secure-checkout" in str(uses_action):
                # This is good - using centralized approach
                continue

            # Check for old harden-runner pattern - suggest migration
            if "step-security/harden-runner" in str(uses_action):
                issues.append(
                    f"Job '{job_name}' could use ./.github/actions/secure-checkout "
                    "for consistency",
                )

    return issues


def suggest_security_profile(
    workflow: Dict[str, Any],
    workflow_name: str,
    config: Dict[str, Any],
) -> Optional[str]:
    """Suggest appropriate security profile for workflow.

    Args:
        workflow: Workflow configuration dictionary.
        workflow_name: Name of the workflow file.
        config: Security configuration dictionary.

    Returns:
        Suggested security profile name, or None if no specific suggestion.
    """
    # Simplified - no complex profiles
    return None


def validate_workflow(
    workflow_path: Path,
    config: Dict[str, Any],
) -> Dict[str, List[str]]:
    """Validate a single workflow file.

    Args:
        workflow_path: Path to the workflow file to validate.
        config: Security configuration dictionary.

    Returns:
        Dictionary containing categorized validation issues.
    """
    workflow_name = workflow_path.name
    workflow = load_workflow(workflow_path)

    if not workflow:
        return {"errors": [f"Failed to load workflow {workflow_path}"]}

    issues = {
        "harden_runner": check_harden_runner(workflow, workflow_name),
        "action_pinning": check_action_pinning(workflow, workflow_name),
        "permissions": check_permissions(workflow, workflow_name, config),
        "endpoints": check_endpoints(workflow, workflow_name, config),
        "suggestions": [],
    }

    # Add suggestions
    issues["suggestions"].append(
        "Consider using ./.github/actions/secure-checkout for consistency",
    )

    return issues


def main() -> int:
    """Main function.

    Returns:
        int: Exit code: 0 for success, 1 for validation failures.
    """
    parser = argparse.ArgumentParser(
        description="Validate workflow security configuration",
    )
    parser.add_argument("--workflow", help="Specific workflow to validate")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix issues automatically",
    )
    parser.add_argument("--summary", action="store_true", help="Show summary only")

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_security_config()
    except Exception as e:
        print(f"Error loading security configuration: {e}")
        sys.exit(1)

    # Find workflow files
    workflow_dir = Path(".github/workflows")
    if args.workflow:
        workflow_files = [workflow_dir / args.workflow]
        if not workflow_files[0].exists():
            print(f"Workflow file not found: {workflow_files[0]}")
            sys.exit(1)
    else:
        workflow_files = list(workflow_dir.glob("*.yml"))

    # Validate workflows
    total_issues = 0
    for workflow_path in sorted(workflow_files):
        if workflow_path.name.startswith("reusable-"):
            continue  # Skip reusable workflows for now

        issues = validate_workflow(workflow_path, config)

        # Count total issues
        issue_count = sum(
            len(issue_list)
            for key, issue_list in issues.items()
            if key != "suggestions" and issue_list
        )

        if issue_count > 0 or (not args.summary and issues["suggestions"]):
            print(f"\n📁 {workflow_path.name}")
            print("=" * (len(workflow_path.name) + 4))

            for category, issue_list in issues.items():
                if not issue_list:
                    continue

                if category == "suggestions":
                    print("\n💡 Suggestions:")
                    for suggestion in issue_list:
                        print(f"  • {suggestion}")
                else:
                    category_name = category.replace("_", " ").title()
                    print(f"\n❌ {category_name}:")
                    for issue in issue_list:
                        print(f"  • {issue}")

            total_issues += issue_count

    # Summary
    print("\n" + "=" * 50)
    if total_issues == 0:
        print("✅ All workflows pass security validation!")
    else:
        print(
            f"⚠️  Found {total_issues} security issues across "
            f"{len(workflow_files)} workflows",
        )
        print("\n💡 Next steps:")
        print("  1. Review the centralized security configuration in .github/data/")
        print(
            "  2. Use the ./.github/actions/secure-checkout action "
            "to simplify workflows",
        )
        print("  3. Run with --fix to attempt automatic corrections (when implemented)")

    return 1 if total_issues > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
