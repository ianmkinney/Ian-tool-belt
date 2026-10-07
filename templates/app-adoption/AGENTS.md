# Agent instructions

This repository follows Ian's tool belt: https://github.com/ianmkinney/Ian-tool-belt

Read and follow, in full:

- [Engineering and pull-request contract](https://github.com/ianmkinney/Ian-tool-belt/blob/main/rules/engineering.md)
- [Working agreement](https://github.com/ianmkinney/Ian-tool-belt/blob/main/rules/working-agreement.md)

Summary:

- **One draft PR per session.** Reuse this session's open PR, or open one draft PR on a new branch. Never merge without authorization.
- **Tests for every change.** Cover changed behavior with automated tests and run the project's checks.
- **Secrets stay out of Git.** Use environment variables or the host's secret store; never commit `.env` values, tokens or credentials.
- **CI green.** After each push, check the latest head, fix failures and report pending or blocked checks honestly.
- **Conventional Commit PR titles.** `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `ci:`, `perf:`, `build:` or `revert:`, with `!` for breaking changes. PRs are squash-merged, so the title becomes the commit.
- **Releases via release-please.** Do not edit versions or `CHANGELOG.md` by hand; a release happens when the release-please PR is merged.
