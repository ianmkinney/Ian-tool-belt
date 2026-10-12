# Publish Ian's Tool Belt with GitHub Pages

The public site is **generated**, not hand-edited. `python3 scripts/build_site.py` (or `python3 belt.py site`) renders blueprint-themed HTML into `site/` from `belt.json`, `belt.index.json`, skills, docs, workflows, and styling tokens.

## One-time activation

A repository administrator should open **Settings → Pages**:

1. Under **Build and deployment**, choose **GitHub Actions** (not “Deploy from a branch”).
2. After the first successful run of **Deploy GitHub Pages** (`pages.yml`) on `main`, use the URL GitHub shows (expected: `https://ianmkinney.github.io/Ian-tool-belt/`).

The legacy hand-written `docs/index.html` is replaced by a short redirect stub for anyone still using branch-based `/docs` publishing; the Actions workflow is the source of truth.

## Local preview

```sh
python3 belt.py site --out site
python3 -m http.server --directory site 8080
```

Open `http://127.0.0.1:8080/Ian-tool-belt/` (or set `SITE_BASE=/` when building for a local root).

CI runs `python3 scripts/build_site.py --check` on every push and pull request.

Official reference: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
