# Versioning templates for app repos

SemVer, Conventional Commit PR titles and release-please. Every change lands through a squash-merged PR, and its title becomes the commit on `main`. release-please keeps one release PR open; merging it bumps the version, updates `CHANGELOG.md`, tags `vX.Y.Z` and publishes a GitHub Release.

## Copy these files

| Template | Destination in the app repo |
| --- | --- |
| `release.yml` | `.github/workflows/release.yml` |
| `pr-title.yml` | `.github/workflows/pr-title.yml` |
| `release-please-config.json` | `release-please-config.json` |
| `.release-please-manifest.json` | `.release-please-manifest.json` |

Set the manifest to the app's current `package.json` version. Change `release-type` for non-Node repos (`simple` for static sites, `python` for Python). Add `extra-files` for other version-bearing files, for example `{"type": "json", "path": "app.json", "jsonpath": "$.expo.version"}`.

The callers use `ianmkinney/Ian-tool-belt/.github/workflows/<file>@main`, so Ian-tool-belt must stay public and the workflows must be on its `main` branch.

## Manual steps per repo

These are settings, not files, so a PR cannot make them:

1. **Settings > Actions > General > Workflow permissions:** choose **Read and write permissions** and tick **Allow GitHub Actions to create and approve pull requests**. For an organization, the org-level setting must allow it too.
2. **Settings > General > Pull Requests:** allow **squash merging** only, with the default commit message set to **Pull request title**.
3. Optional: a branch ruleset on `main` that requires a PR and the `pr-title` and CI checks.

## Optional token

PRs opened with the default `GITHUB_TOKEN` (the release-please PR and the weekly `tool-belt/sync` PR) do not trigger CI on their own. That token also cannot change `.github/workflows/*`, so without a token the sync skips workflow files.

- **Workaround with no secret:** close and reopen the PR. Your own `pull_request` event then runs CI.
- **Token:** create a fine-grained PAT scoped to the app repo with **Contents**, **Pull requests** and **Workflows** set to read and write. Store it as the `BELT_SYNC_TOKEN` or `RELEASE_PLEASE_TOKEN` repository secret. Release uses `RELEASE_PLEASE_TOKEN`; the sync prefers `BELT_SYNC_TOKEN` and falls back to `RELEASE_PLEASE_TOKEN`. The callers pass them by name. Never commit the token.

After setup, merge a `feat:` or `fix:` PR so release-please opens its first release PR.

## Show the version: Next.js `/api/version`

`app/api/version/route.ts`:

```ts
import { version } from '../../../package.json';

export const dynamic = 'force-dynamic';

export function GET() {
  const commit =
    process.env.VERCEL_GIT_COMMIT_SHA ??
    process.env.SOURCE_COMMIT ??
    process.env.GIT_SHA ??
    null;
  return Response.json({ version, commit });
}
```

Vercel sets `VERCEL_GIT_COMMIT_SHA`. Coolify provides `SOURCE_COMMIT`; pass it (or `GIT_SHA`) into the build or runtime environment.
