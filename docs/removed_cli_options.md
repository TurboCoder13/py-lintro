# Removed CLI Options (2024-06)

This document lists all CLI options/configs that were removed from the Lintro CLI during the 2024-06 refactor. These options were removed because the corresponding tools are not implemented in the codebase.

## Removed Options

- `--hadolint-timeout`: Timeout for hadolint in seconds. (Hadolint integration not present)
- `--semgrep-config`: Semgrep configuration option. (Semgrep integration not present)
- `--terraform-recursive`: Recursively check/format Terraform directories. (Terraform integration not present)
- `--yamllint-config`: Path to yamllint configuration file. (Yamllint integration not present)
- `--yamllint-strict`: Use strict mode for yamllint. (Yamllint integration not present)

If these tools are added in the future, their options can be restored as needed.
