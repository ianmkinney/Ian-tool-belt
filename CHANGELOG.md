# Changelog

All notable changes to this project are documented in this file.

Release versions are managed by [release-please](https://github.com/googleapis/release-please) (see `.github/workflows/release.yml`); `belt.json` `version` bumps when the release PR merges.

## [Unreleased]

### Added

- Pin **pre-commit** 4.6.2 (MIT) with a shared `.pre-commit-config.yaml` that runs gitleaks, shellcheck-py, actionlint, zizmor and basic hygiene hooks at the same versions as CI, plus a `templates/pre-commit/` copy path and a `pre-commit.yml` workflow.
