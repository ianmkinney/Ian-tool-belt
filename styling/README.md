# Tool Belt styling

Reusable design tokens for projects that want the [Tool Belt identity](../branding/README.md). `tokens.json` is the source; `tokens.css` is generated from it.

| Token | Value | Use |
| --- | --- | --- |
| `--tb-color-charcoal` | `#17212B` | Workshop charcoal: text, dark panels |
| `--tb-color-cream` | `#F5F0E6` | Canvas cream: page background |
| `--tb-color-brass` | `#D9A441` | Brass: accents, buckle shadow |
| `--tb-color-teal` | `#38B2AC` | Signal teal: status, focus rings |
| `--tb-color-paper`, `--tb-color-muted`, `--tb-color-line` | see JSON | Cards, secondary text, rules |
| `--tb-font-sans`, `--tb-font-mono` | system stacks | Prose and technical labels |

Fonts are system stacks, so nothing is downloaded. Keep text contrast readable: charcoal on cream or paper, cream on charcoal. Brass is an accent, not a body-text color on cream.

## Use in a project

Copy `tokens.css` (or the whole folder) into the project, then:

```css
@import "./tokens.css";

body {
  background: var(--tb-color-cream);
  color: var(--tb-color-charcoal);
  font-family: var(--tb-font-sans);
}
code { font-family: var(--tb-font-mono); }
```

Build tools and native apps can read `tokens.json` directly. The site in `docs/index.html` keeps its styles inline because GitHub Pages serves only `docs/`; a unit test keeps its palette in sync with these tokens.

## Change a token

Edit `tokens.json`, run `python3 scripts/build_tokens.py`, and commit both files. `python3 scripts/build_tokens.py --check` (run in CI) fails if they drift. Bump the `styling` package version in `belt.json` when a value changes.
