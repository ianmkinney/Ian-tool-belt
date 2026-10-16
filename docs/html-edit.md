# html-edit

Edit generated HTML in the browser and save a **clean** copy without editor chrome.

## Server mode

```sh
python3 belt.py edit path/to/page.html
python3 belt.py edit page.html --port 9000 --out page.edited.html
python3 belt.py edit page.html --in-place   # overwrite original (use with care)
```

Opens `http://127.0.0.1:8765/` with `editor.js` injected. Saves write `<name>.edited.html` beside the source unless `--out` or `--in-place` is set. Only the source file's directory is writable.

## Standalone script

```sh
python3 tools/html-edit/html_edit.py sample.html
```

## Without the server

- Use the bookmarklet in `tools/html-edit/bookmarklet.txt` while the server is running, or
- Add `<script src="editor.js"></script>` next to a local HTML file (save downloads the cleaned file).

## Shortcuts

| Shortcut | Action |
| --- | --- |
| Ctrl/Cmd+E | Toggle edit mode |
| Ctrl/Cmd+S | Save (server or download) |

Drafts autosave to `localStorage`; use **Restore draft** in the toolbar.

## Belt package

Registered as `html-edit` in `belt.json` (`tools/html-edit/`). Stdlib-only Python; editor UI uses blueprint colors in shadow DOM.
