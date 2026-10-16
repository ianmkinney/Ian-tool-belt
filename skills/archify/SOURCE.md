# archify (upstream)

- **Repository:** https://github.com/tt-a1i/archify
- **License:** MIT (see upstream `archify/LICENSE`)
- **Vendored commit:** `58ab0b98d2d0def8e49dced705c7b566936723ec` (main, 2026-10-12)
- **Contents:** `skills/archify/SKILL.md` and the `references/` files it links, from upstream `archify/`. Renderer and example paths that are not vendored point at the pinned GitHub commit.

**What it is:** Archify turns requirements, Mermaid, or repository evidence into validated interactive architecture/workflow/sequence/dataflow/lifecycle diagrams as standalone HTML (inline SVG) with optional export.

Heavy dependencies (not installed by the belt): **Node.js 18+**, the upstream `archify/bin/archify.mjs` CLI and its validator/renderer bundle (install by cloning the repo or following upstream install docs). Optional browser/ffmpeg tooling for WebM export per upstream. The public npm package name `archify` is unrelated; use the GitHub repo, not `npm install archify`.
