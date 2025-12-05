# Project Governance

This document defines the decision-making and roles for the `py-lintro` project. It aims
to provide clarity, continuity, and accountability to contributors and users.

## Roles

- Maintainers
  - Own overall project direction and releases
  - Review and approve pull requests
  - Manage repository settings and automation
- Contributors
  - Propose changes via pull requests
  - Participate in reviews and discussions
- Security Contacts
  - Triage security reports and coordinate fixes
  - Listed in `SECURITY.md`

## Decision Process

- Pull Requests
  - Each change is proposed via a PR following Conventional Commits
  - At least 1 maintainer review approval is required to merge
  - Squash merges are required; PR title becomes the merge commit
- Consensus Seeking
  - Maintainers seek rough consensus in PR discussions
  - In case of disagreement, a maintainer proposes a path forward; if needed, a simple
    majority of maintainers decides

## Membership

- Becoming a Maintainer
  - Demonstrated sustained contributions (code, reviews, docs)
  - Consistent adherence to project standards and quality
  - Nominated by a maintainer; confirmed by simple majority of maintainers
- Removing Inactive Maintainers
  - If a maintainer is inactive for > 6 months, remaining maintainers may propose moving
    them to emeritus status by simple majority

## Release Management

- Versioning and Releases
  - Semantic versioning via Conventional Commits (squash merges)
  - Automated tagging and release via CI on `main`
- Branch Protection
  - Merges require PR, passing checks, and approval
  - Enforced by Allstar Branch Protection policy

## Security and Compliance

- Responsible Disclosure
  - Follow `SECURITY.md` for reporting vulnerabilities
- Supply Chain and CI
  - Use pinned or reviewed dependencies and CI workflows
  - Periodic automated analysis (Scorecards, CodeQL) supports continuous improvement

## Changes to this Document

- Propose updates via PR
- Requires 2 maintainer approvals to merge
