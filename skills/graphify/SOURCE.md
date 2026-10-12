# graphify (upstream)

- **Repository:** https://github.com/Graphify-Labs/graphify
- **License:** Apache-2.0 (see upstream `LICENSE` and `LICENSE-MIT`)
- **Vendored commit:** `a5ba60ddf6293d9f380321965ecf1084391dcc2b` (`v8` branch tip at vendoring)
- **Contents:** `skills/graphify/SKILL.md` adapted from upstream `graphify/skill.md` (agent instructions only; not the full Python package tree)

Heavy dependencies (install separately): **Python 3.10+**, PyPI package **`graphifyy`** (pinned in `belt.json`), native build tooling for **tree-sitter** parsers, **numpy** and other scientific stack pieces; optional **ffmpeg** / **Whisper** for video/audio, optional **Neo4j** or **FalkorDB** for graph push. No paid API keys required for local parse-and-query workflows; LLM-backed extraction uses your own configured model when enabled.
