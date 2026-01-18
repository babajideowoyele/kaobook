# Changelog

All notable changes to kaobook will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `.latexmkrc` configuration for standardized builds
- `DEPENDENCIES.md` documenting minimum requirements
- Pre-commit hooks (`.pre-commit-config.yaml`)
- ChkTeX linting in CI pipeline
- PDF artifact uploads in CI
- Visual regression testing framework
- Release automation with release-drafter
- Improved documentation for `kaoci-rolebox.sty` and `kaoci-eur.sty`

### Changed
- CI workflow now uploads compiled PDFs as artifacts
- Improved lint configuration with `.chktexrc`

## [0.9.8] - Previous Release

See [GitHub Releases](https://github.com/fmarotta/kaobook/releases) for historical changes.

---

## Release Process

Releases are automatically drafted when PRs are merged to master. To create a release:

1. Review the draft release on GitHub
2. Edit the version number if needed
3. Publish the release
4. The CHANGELOG will be automatically updated

### PR Labels

Use these labels on PRs to categorize changes:
- `feature` / `enhancement` - New features
- `bug` / `fix` - Bug fixes
- `documentation` / `docs` - Documentation updates
- `testing` / `test` - Test improvements
- `chore` / `maintenance` - Maintenance tasks
- `breaking` - Breaking changes (triggers major version bump)
