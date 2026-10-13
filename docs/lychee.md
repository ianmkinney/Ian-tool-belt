# Lychee link checker

[lychee](https://github.com/lycheeverse/lychee) (Apache-2.0 OR MIT) checks Markdown and HTML for broken links. The belt pins **0.24.2**, which is release tag `lychee-v0.24.2` (published 2026-05-01). The GitHub Pages site and the Markdown under `docs/` had no link checker before this. Lychee covers `docs/`, the README, and the other Markdown and HTML the site is built from.

## When to run

The **Link check** workflow (`.github/workflows/lychee.yml`) runs on every push and pull request. Run the same command locally before editing docs or site sources.

## Command

The version comes from the `lychee` `github-release` package in `belt.json` (`lycheeverse/lychee`). CI downloads the official Linux `x86_64-unknown-linux-gnu` archive for tag `lychee-v` plus that pin, checks the sibling `.sha256`, and extracts the `lychee` binary (it sits one directory down in the tarball).

```sh
archive="lychee-x86_64-unknown-linux-gnu.tar.gz"
base="https://github.com/lycheeverse/lychee/releases/download/lychee-v0.24.2"
curl -fsSL -o "$archive" "${base}/${archive}"
curl -fsSL -o "${archive}.sha256" "${base}/${archive}.sha256"
sha256sum -c "${archive}.sha256"
tar -xzf "$archive" --strip-components=1 "lychee-x86_64-unknown-linux-gnu/lychee"
chmod +x lychee
GITHUB_TOKEN="$(gh auth token)" ./lychee --config lychee.toml --no-progress --exclude-loopback \
  README.md AGENTS.md CHANGELOG.md CONTRIBUTING.md \
  docs rules skills connections templates styling branding \
  tools/breakroom/README.md tools/breakroom/docs
```

On macOS, use `lychee-aarch64-apple-darwin.tar.gz` or `lychee-x86_64-apple-darwin.tar.gz` from the same release. Each archive has a `.sha256` sibling. `GITHUB_TOKEN` is optional on a laptop. CI sets it to the workflow token (`contents: read`). Lychee 0.24.2 uses that token only as a fallback when a GitHub repository URL fails the normal request. It does not prove that a `/blob/` file exists; those links are checked through the raw remap below.

[`lychee.toml`](../lychee.toml) is the checker config. `--exclude-loopback` skips `localhost` and `127.0.0.1`. Links inside fenced code blocks are not checked. The job fails when a checked link is broken. No host is excluded.

GitHub HTML pages for `/blob/` files often return 503 when many are checked at once. `lychee.toml` remaps those file links to `raw.githubusercontent.com`, which returns 404 when the file is gone, so a broken file link still fails. Repository, tree and release links stay on `github.com`. The config slows those hosts and retries before failing. Add an `exclude` regex there only if some other host starts flapping.

The weekly pin check reads GitHub's latest stable tag. Lychee tags look like `lychee-v0.24.2`. `scripts/check_pins.py` keeps the trailing `0.24.2`, so a newer stable release can open a bump PR. The workflow always prefixes `lychee-v` when it downloads. That prefix is part of upstream's tag scheme; a pin bump does not change it.

## Reading results

Exit code 0 means every checked link returned an accepted status. Redirects count as success and are called out in a hint. A non-zero exit lists the file, the URL and the status code. `200`–`299` pass. A `404` means the target is missing. A `503` usually means the host was busy; rerun before editing the link.

## Remove

1. Delete the `lychee` entry from `packages` in `belt.json`.
2. Remove `.github/workflows/lychee.yml` and `lychee.toml`.
3. Delete this file. Drop the Link check row and section from [automation.md](automation.md), and the lychee mentions in [setup.md](setup.md), [design.md](design.md) and the README.
4. Run `python3 belt.py index` and commit `belt.index.json` and `AGENTS.md`.
