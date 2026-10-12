"""Build the static GitHub Pages site from belt sources. Stdlib only."""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = '/Ian-tool-belt/'

NAV = [
    ('index.html', 'Home'),
    ('tools.html', 'Tools'),
    ('connections.html', 'Connections'),
    ('skills.html', 'Skills'),
    ('breakroom.html', 'Break room'),
    ('automation.html', 'Automation'),
    ('local-ai.html', 'Local AI'),
    ('changelog.html', 'Changelog'),
    ('agents.html', 'For agents'),
]


def esc(text):
    return html.escape(str(text), quote=True)


def md_to_html(text):
    """Minimal markdown: headings, lists, code fences, paragraphs, links."""
    out = []
    in_code = False
    code_buf = []
    list_open = None
    for line in text.splitlines():
        if line.strip().startswith('```'):
            if in_code:
                out.append(f'<pre><code>{esc(chr(10).join(code_buf))}</code></pre>')
                code_buf = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue
        if re.match(r'^#{1,6}\s', line):
            if list_open:
                out.append(f'</{list_open}>')
                list_open = None
            level = len(line.split()[0])
            title = line[level + 1:].strip()
            out.append(f'<h{level}>{inline_md(title)}</h{level}>')
            continue
        if re.match(r'^[-*]\s+', line):
            if list_open != 'ul':
                if list_open:
                    out.append(f'</{list_open}>')
                out.append('<ul>')
                list_open = 'ul'
            out.append(f'<li>{inline_md(line[2:].strip())}</li>')
            continue
        if re.match(r'^\d+\.\s+', line):
            if list_open != 'ol':
                if list_open:
                    out.append(f'</{list_open}>')
                out.append('<ol>')
                list_open = 'ol'
            out.append(f'<li>{inline_md(re.sub(r"^\\d+\\.\\s+", "", line))}</li>')
            continue
        if not line.strip():
            if list_open:
                out.append(f'</{list_open}>')
                list_open = None
            continue
        if list_open:
            out.append(f'</{list_open}>')
            list_open = None
        out.append(f'<p>{inline_md(line)}</p>')
    if list_open:
        out.append(f'</{list_open}>')
    if in_code and code_buf:
        out.append(f'<pre><code>{esc(chr(10).join(code_buf))}</code></pre>')
    return '\n'.join(out)


def inline_md(text):
    text = esc(text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return text


def load_index(root):
    return json.loads((root / 'belt.index.json').read_text())


def automation_rows(root):
    text = (root / 'docs/automation.md').read_text()
    rows = []
    for line in text.splitlines():
        if not line.startswith('| **'):
            continue
        parts = [p.strip() for p in line.split('|')[1:-1]]
        if len(parts) < 4:
            continue
        name = re.sub(r'\*\*([^*]+)\*\*.*', r'\1', parts[0])
        file_m = re.search(r'`([^`]+)`', parts[0])
        fname = file_m.group(1) if file_m else parts[0]
        rows.append({'name': name, 'file': fname, 'trigger': parts[1], 'does': parts[2], 'perms': parts[3]})
    return rows


def git_releases(root):
    try:
        tags = subprocess.check_output(
            ['git', '-C', str(root), 'tag', '-l', '--sort=-version:refname'],
            text=True, stderr=subprocess.DEVNULL,
        ).strip().splitlines()
    except (OSError, subprocess.CalledProcessError):
        tags = []
    entries = []
    for tag in tags[:30]:
        try:
            body = subprocess.check_output(
                ['git', '-C', str(root), 'log', '-1', '--format=%s%n%b', tag],
                text=True, stderr=subprocess.DEVNULL,
            )
            subject, _, rest = body.partition('\n')
            entries.append({'tag': tag, 'subject': subject.strip(), 'body': rest.strip()})
        except subprocess.CalledProcessError:
            entries.append({'tag': tag, 'subject': tag, 'body': ''})
    changelog = root / 'CHANGELOG.md'
    if changelog.is_file():
        return {'source': 'CHANGELOG.md', 'markdown': changelog.read_text(), 'tags': entries}
    return {'source': 'git tags', 'markdown': '', 'tags': entries}


def css_text(root):
    tokens_css = (root / 'styling/tokens.css').read_text()
    return tokens_css + SITE_CSS


SITE_CSS = """
body{margin:0;background:var(--tb-color-blueprint-navy);color:var(--tb-color-blueprint-ink);
  font:16px/1.6 var(--tb-font-sans);}
a{color:var(--tb-color-blueprint-cyan);text-decoration-thickness:1px;text-underline-offset:3px}
a:hover{color:var(--tb-color-blueprint-amber)}
a:focus-visible{outline:2px solid var(--tb-color-blueprint-amber);outline-offset:3px}
.skip{position:absolute;left:1rem;top:-4rem;background:var(--tb-color-blueprint-navy);padding:.5rem 1rem;z-index:9}
.skip:focus{top:1rem}
.wrap{width:min(1100px,calc(100% - 2rem));margin:0 auto}
.site-header{border-bottom:1px solid var(--tb-color-blueprint-cyan);padding:1rem 0;display:flex;flex-wrap:wrap;gap:1rem;align-items:center;justify-content:space-between}
.brand{display:flex;align-items:center;gap:.75rem;text-decoration:none;color:inherit;font-weight:700}
.brand img{width:40px;height:40px;border:1px solid var(--tb-color-blueprint-cyan)}
nav{display:flex;flex-wrap:wrap;gap:.5rem 1rem;font-size:.875rem}
nav a{text-decoration:none;color:var(--tb-color-blueprint-ink);opacity:.9}
nav a[aria-current=page]{color:var(--tb-color-blueprint-amber);font-weight:650}
main{padding:2rem 0 4rem}
.title-block{border:1px solid var(--tb-color-blueprint-cyan);padding:.75rem 1rem;font:11px/1.5 var(--tb-font-mono);margin-bottom:2rem;display:grid;grid-template-columns:1fr auto;gap:1rem}
.title-block .dim{color:var(--tb-color-blueprint-cyan)}
h1{font-size:clamp(1.75rem,4vw,2.5rem);line-height:1.15;margin:0 0 1rem;font-weight:700}
h2{font-size:1.35rem;margin:2rem 0 .75rem;border-left:3px solid var(--tb-color-blueprint-cyan);padding-left:.75rem}
h3{font-size:1.1rem;margin:1.25rem 0 .5rem}
.lead{opacity:.92;max-width:42rem}
.grid{display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));margin:1.5rem 0}
.card{border:1px solid var(--tb-color-blueprint-cyan);padding:1rem;background:rgba(0,0,0,.12)}
.card h3{margin-top:0;font-family:var(--tb-font-mono);font-size:.95rem}
.card .meta{font:12px var(--tb-font-mono);color:var(--tb-color-blueprint-cyan);margin-bottom:.5rem}
table{width:100%;border-collapse:collapse;font-size:.9rem;margin:1rem 0}
th,td{border:1px solid var(--tb-color-blueprint-cyan);padding:.5rem .65rem;text-align:left;vertical-align:top}
th{font-family:var(--tb-font-mono);font-size:.75rem;color:var(--tb-color-blueprint-cyan)}
pre{background:rgba(0,0,0,.25);border:1px solid var(--tb-color-blueprint-cyan);padding:1rem;overflow-x:auto;font-size:.8rem;position:relative}
code{font-family:var(--tb-font-mono);font-size:.88em}
.copy{position:absolute;top:.5rem;right:.5rem;font:11px var(--tb-font-mono);background:transparent;border:1px solid var(--tb-color-blueprint-cyan);color:inherit;padding:.2rem .5rem;cursor:pointer}
.copy:focus-visible{outline:2px solid var(--tb-color-blueprint-amber)}
.search{margin:1rem 0}
.search input{width:100%;max-width:28rem;padding:.5rem .75rem;border:1px solid var(--tb-color-blueprint-cyan);background:rgba(0,0,0,.2);color:inherit;font:inherit}
.search input:focus{outline:2px solid var(--tb-color-blueprint-amber)}
[data-search-item].hidden{display:none}
.hero{display:grid;gap:2rem;grid-template-columns:1fr 1fr;align-items:center;margin:1rem 0 2rem}
@media(max-width:800px){.hero{grid-template-columns:1fr}}
.hero-svg{width:100%;max-width:420px;margin:auto;display:block}
@keyframes dim-pulse{0%,100%{opacity:.35}50%{opacity:1}}
.hero .dim-line{animation:dim-pulse 4s ease-in-out infinite}
@media(prefers-reduced-motion:reduce){.hero .dim-line{animation:none;opacity:.7}}
.cta{display:inline-block;margin-top:1rem;padding:.55rem 1rem;border:1px solid var(--tb-color-blueprint-amber);color:var(--tb-color-blueprint-amber);text-decoration:none;font-weight:650}
.cta:hover{background:var(--tb-color-blueprint-amber);color:var(--tb-color-blueprint-navy)}
.prose{max-width:52rem}
.prose img{max-width:100%}
footer{border-top:1px solid var(--tb-color-blueprint-cyan);padding:2rem 0;font:12px var(--tb-font-mono);opacity:.85}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:-1;
  background-image:linear-gradient(rgba(120,210,255,.08) 1px,transparent 1px),
    linear-gradient(90deg,rgba(120,210,255,.08) 1px,transparent 1px);
  background-size:24px 24px}
"""

HERO_SVG = """<svg class="hero-svg" viewBox="0 0 400 220" role="img" aria-label="Tool belt line drawing with dimension lines">
  <rect width="400" height="220" fill="none"/>
  <g stroke="#fff" stroke-width="1.2" fill="none">
    <rect x="60" y="95" width="280" height="22"/>
    <rect x="85" y="117" width="70" height="55"/><rect x="165" y="117" width="70" height="55"/><rect x="245" y="117" width="70" height="55"/>
    <rect x="188" y="100" width="24" height="12" stroke="#FFC450"/>
    <path d="M30 70 L55 95 M370 70 L345 95"/>
    <circle cx="200" cy="55" r="14" stroke="#FFC450"/><path d="M194 55 L198 59 L206 51" stroke="#fff"/>
  </g>
  <g stroke="#78D2FF" stroke-width="1" class="dim-line">
    <line x1="40" y1="40" x2="40" y2="180"/><line x1="36" y1="40" x2="44" y2="40"/><line x1="36" y1="180" x2="44" y2="180"/>
    <line x1="360" y1="50" x2="360" y2="170"/><line x1="356" y1="50" x2="364" y2="50"/><line x1="356" y1="170" x2="364" y2="170"/>
    <text x="48" y="115" fill="#78D2FF" font-size="10" font-family="monospace">180</text>
  </g>
  <g stroke="#78D2FF" stroke-width=".8" stroke-dasharray="4 3" opacity=".8">
    <line x1="85" y1="125" x2="155" y2="125"/><line x1="165" y1="125" x2="235" y2="125"/>
  </g>
</svg>"""


def render_shell(base, page_file, title, body, search_items, version, avatar='avatar.png'):
    nav_html = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == page_file else ''
        nav_html.append(f'<a href="{esc(base + href)}"{cur}>{esc(label)}</a>')
    search_data = json.dumps(search_items)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(title)} — Ian's Tool Belt">
<meta name="theme-color" content="#0E3478">
<title>{esc(title)} · Tool Belt</title>
<link rel="stylesheet" href="{esc(base)}assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="wrap site-header">
  <a class="brand" href="{esc(base)}index.html"><img src="{esc(base)}assets/{esc(avatar)}" alt="" width="40" height="40"> Ian's Tool Belt</a>
  <nav aria-label="Site">{''.join(nav_html)}</nav>
</header>
<main id="main" class="wrap">
<div class="title-block"><div><strong>DWG TB-001</strong><br><span class="dim">Pack once · Build anywhere</span></div>
<div class="dim">REV {esc(version)}<br>SCALE 1:1</div></div>
{body}
</main>
<footer class="wrap"><p>MIT licensed · Generated from the repository · <a href="https://github.com/ianmkinney/Ian-tool-belt">Source</a></p></footer>
<script>window.SITE_BASE="{esc(base)}";window.SITE_SEARCH={search_data};</script>
<script src="{esc(base)}assets/site.js" defer></script>
</body>
</html>"""


def write_page(out, base, page_file, title, body, search_items, version, avatar='avatar.png'):
    path = out / page_file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_shell(base, page_file, title, body, search_items, version, avatar))


def search_item(page, title, text):
    return {'page': page, 'title': title, 'text': text}


def build(root, out_dir, base=DEFAULT_BASE):
    root = Path(root).resolve()
    out = Path(out_dir).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / 'assets').mkdir()
    (out / 'data').mkdir()
    index = load_index(root)
    version = index['version']
    shutil.copy2(root / 'styling/tokens.css', out / 'assets/tokens.css')
    (out / 'assets/style.css').write_text(css_text(root))
    avatar_out = out / 'assets/avatar.png'
    for avatar_src in (root / 'toolbot-bro-avatar' / 'p48.png', root / 'branding' / 'avatar.png'):
        if avatar_src.is_file():
            shutil.copy2(avatar_src, avatar_out)
            break
    if not avatar_out.is_file():
        svg = root / 'branding' / 'avatar.svg'
        if svg.is_file():
            shutil.copy2(svg, out / 'assets/avatar.svg')
        else:
            raise FileNotFoundError('Avatar missing (toolbot-bro-avatar/p48.png or branding/avatar.svg)')
    avatar_asset = 'avatar.png' if avatar_out.is_file() else 'avatar.svg'
    shutil.copy2(root / 'belt.index.json', out / 'data/belt.index.json')
    agents_md = (root / 'AGENTS.md').read_text()
    (out / 'data/AGENTS.md').write_text(agents_md)

    search = []
    cmds = index['commands'][:5]
    cmd_rows = ''.join(
        f'<tr><th scope="row"><code>{esc(c["run"])}</code></th><td>{esc(c["description"])}</td></tr>'
        for c in cmds
    )
    home_body = f"""
<h1>Tool Belt</h1>
<p class="lead">{esc(index['description'])}</p>
<div class="hero">
<div>
<pre><code>python3 path/to/Ian-tool-belt/belt.py use</code></pre>
<p>Drop MCP connections, skills, and rules into your project. Cursor is the default target.</p>
<a class="cta" href="{esc(base)}tools.html">Browse tools &amp; packages</a>
<h2>Everyday commands</h2>
<table><thead><tr><th>Command</th><th>Purpose</th></tr></thead><tbody>{cmd_rows}</tbody></table>
</div>
<div>{HERO_SVG}</div>
</div>"""
    def page(file, title, body):
        write_page(out, base, file, title, body, search, version, avatar_asset)

    page('index.html', 'Home', home_body)

    pkg_cards = []
    for p in index['packages']:
        pin = p.get('version', '')
        kind = p.get('kind', '')
        name = p.get('name', p.get('path', p['id']))
        pkg_cards.append(
            f'<article class="card" data-search-item id="pkg-{esc(p["id"])}" data-search="{esc(p["id"])} {esc(name)}">'
            f'<div class="meta">{esc(kind)} · pin {esc(pin)}</div><h3>{esc(p["id"])}</h3>'
            f'<p>{esc(p["description"])}</p><p><code>{esc(name)}</code></p></article>'
        )
        search.append(search_item('tools.html', p['id'], p['description']))
    tools_body = f'<h1>Tools &amp; packages</h1><p class="lead">Pinned packages and file bundles declared in belt.json.</p>'
    tools_body += '<div class="search"><label for="q-tools">Filter</label><input id="q-tools" type="search" data-search-target=".grid" placeholder="Search packages…"></div>'
    tools_body += f'<div class="grid">{"".join(pkg_cards)}</div>'
    page('tools.html', 'Tools', tools_body)

    conn_rows = []
    for s in index['servers']:
        conn_rows.append(
            f'<tr data-search-item data-search="{esc(s["id"])}"><th scope="row">{esc(s["id"])}</th>'
            f'<td>{esc(s["transport"])}</td><td>{esc(s["status"])}</td><td>{esc(s["description"])}</td></tr>'
        )
        search.append(search_item('connections.html', s['id'], s['description']))
    adapter_rows = []
    for a in index['adapters']:
        adapter_rows.append(
            f'<tr><th scope="row">{esc(a["id"])}</th><td>{esc(a.get("mcp", ""))}</td>'
            f'<td>{esc(a.get("skills", ""))}</td><td>{esc(a["description"])}</td></tr>'
        )
    model = index['models'][0]
    preset_rows = ''.join(
        f'<tr><td>{esc(pr["id"])}</td><td><code>{esc(pr["baseUrl"])}</code></td>'
        f'<td><code>{esc(pr["model"])}</code></td><td>{esc(pr["description"])}</td></tr>'
        for pr in model['presets']
    )
    conn_body = f"""<h1>Connections &amp; exports</h1>
<h2>MCP servers</h2><table><thead><tr><th>Id</th><th>Transport</th><th>Status</th><th>Description</th></tr></thead>
<tbody>{"".join(conn_rows)}</tbody></table>
<h2>Local AI model profile</h2><p>{esc(model["description"])}</p>
<table><thead><tr><th>Preset</th><th>Base URL</th><th>Model</th><th>Notes</th></tr></thead><tbody>{preset_rows}</tbody></table>
<h2>Client adapters</h2><table><thead><tr><th>Client</th><th>MCP</th><th>Skills</th><th>Description</th></tr></thead>
<tbody>{"".join(adapter_rows)}</tbody></table>"""
    page('connections.html', 'Connections', conn_body)

    skill_sections = []
    for sk in index['skills']:
        path = root / sk['path']
        raw = path.read_text()
        skill_sections.append(
            f'<section class="card" data-search-item id="skill-{esc(sk["id"])}" data-search="{esc(sk["id"])}">'
            f'<h2>{esc(sk["id"])}</h2><p>{esc(sk["description"])}</p>'
            f'<div class="prose">{md_to_html(raw)}</div></section>'
        )
        search.append(search_item('skills.html', sk['id'], sk['description']))
    skills_body = '<h1>Skills</h1><p class="lead">Portable SKILL.md instructions exported with belt.py use.</p>'
    skills_body += '<div class="search"><input type="search" data-search-target="main" placeholder="Search skills…" aria-label="Search skills"></div>'
    skills_body += ''.join(skill_sections)
    page('skills.html', 'Skills', skills_body)

    br_readme = (root / 'tools/breakroom/README.md').read_text()
    br_rules = (root / 'tools/breakroom/docs/AGENT_RULES.md').read_text()
    br_score = (root / 'tools/breakroom/docs/SCORING.md').read_text()
    break_body = f'<h1>Break room</h1><div class="prose">{md_to_html(br_readme)}</div>'
    break_body += f'<h2>Turn-start routine</h2><div class="prose">{md_to_html(br_rules)}</div>'
    break_body += f'<h2>Scoring</h2><div class="prose">{md_to_html(br_score)}</div>'
    page('breakroom.html', 'Break room', break_body)

    auto_rows = automation_rows(root)
    ar_html = []
    for w in index['workflows']:
        wf = Path(w['id']).name
        match = next((r for r in auto_rows if r['file'] == wf), None)
        trig = esc(match['trigger']) if match else '—'
        perms = esc(match['perms']) if match else 'read'
        ar_html.append(
            f'<tr data-search-item data-search="{esc(wf)}"><th scope="row"><code>{esc(wf)}</code></th>'
            f'<td>{trig}</td><td>{esc(w["description"])}</td><td>{perms}</td></tr>'
        )
        search.append(search_item('automation.html', wf, w['description']))
    auto_body = '<h1>Automation</h1><p class="lead">GitHub Actions workflows from belt.index.json and docs/automation.md.</p>'
    auto_body += '<table><thead><tr><th>Workflow</th><th>Trigger</th><th>Purpose</th><th>Permissions</th></tr></thead>'
    auto_body += f'<tbody>{"".join(ar_html)}</tbody></table>'
    auto_body += f'<div class="prose">{md_to_html((root / "docs/automation.md").read_text().split("## Update a belt variable")[0])}</div>'
    page('automation.html', 'Automation', auto_body)

    local_body = f'<h1>Local AI</h1><div class="prose">{md_to_html((root / "docs/local-ai.md").read_text())}</div>'
    page('local-ai.html', 'Local AI', local_body)

    rel = git_releases(root)
    if rel['markdown']:
        ch_body = f'<div class="prose">{md_to_html(rel["markdown"])}</div>'
    elif rel['tags']:
        items = ''.join(
            f'<li><strong>{esc(t["tag"])}</strong> — {esc(t["subject"])}</li>' for t in rel['tags']
        )
        ch_body = f'<p>Releases from git tags ({esc(rel["source"])}).</p><ul>{items}</ul>'
    else:
        ch_body = '<p>No CHANGELOG.md or git tags found in this checkout.</p>'
    page('changelog.html', 'Changelog', ch_body)

    agents_body = f"""<h1>For agents</h1>
<p>Machine-readable map: <a href="{esc(base)}data/belt.index.json">belt.index.json</a></p>
<div class="prose">{md_to_html(agents_md)}</div>"""
    page('agents.html', 'For agents', agents_body)

    site_js = (root / 'scripts/site_assets/site.js').read_text()
    (out / 'assets/site.js').write_text(site_js)
    return out


def resolve_href(out, href, base):
    if href.startswith('http') or href.startswith('mailto:'):
        return None
    rel = href
    if base and href.startswith(base):
        rel = href[len(base):]
    elif href.startswith('/'):
        rel = href.lstrip('/')
    parts = Path(rel).parts
    if parts and parts[0] == 'Ian-tool-belt':
        rel = str(Path(*parts[1:]))
    return out / rel


def validate_site(out_dir, index, base=DEFAULT_BASE):
    out = Path(out_dir)
    errors = []
    html_files = list(out.rglob('*.html'))
    for path in html_files:
        text = path.read_text()
        for href in re.findall(r'href="([^"#]+)"', text):
            if href.startswith('http') or href.startswith('mailto:') or href.startswith('#'):
                continue
            if not (href.startswith(base) or href.startswith('data/') or 'assets/' in href):
                continue
            target = resolve_href(out, href, base)
            if target is None or not target.is_file():
                errors.append(f'{path.relative_to(out)}: missing link {href}')
    for p in index['packages']:
        if f'id="pkg-{p["id"]}"' not in (out / 'tools.html').read_text():
            errors.append(f'package missing on site: {p["id"]}')
    for s in index['servers']:
        if s['id'] not in (out / 'connections.html').read_text():
            errors.append(f'server missing on site: {s["id"]}')
    for sk in index['skills']:
        if f'id="skill-{sk["id"]}"' not in (out / 'skills.html').read_text():
            errors.append(f'skill missing on site: {sk["id"]}')
    for w in index['workflows']:
        if Path(w['id']).name not in (out / 'automation.html').read_text():
            errors.append(f'workflow missing on site: {w["id"]}')
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'site', help='output directory')
    parser.add_argument('--base', default=os.environ.get('SITE_BASE', DEFAULT_BASE), help='URL path prefix')
    parser.add_argument('--check', action='store_true', help='build and validate internal links and catalog coverage')
    args = parser.parse_args(argv)
    args.base = args.base if args.base.endswith('/') else args.base + '/'
    try:
        out = build(ROOT, args.out, args.base)
        index = load_index(ROOT)
        errors = validate_site(out, index, args.base)
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        print(f'Wrote site to {out}')
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f'Build failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
