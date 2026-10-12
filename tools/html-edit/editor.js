(function () {
  'use strict';
  if (window.__HTML_EDIT_LOADED__) return;
  window.__HTML_EDIT_LOADED__ = true;

  const DRAFT_KEY = 'html-edit:draft';
  const NAVY = '#0E3478';
  const CYAN = '#78D2FF';
  const AMBER = '#FFC450';
  const INK = '#FFFFFF';
  const undoStack = [];
  const redoStack = [];
  let editMode = false;
  let collapsed = false;
  let hoverEl = null;
  let toolbarPos = { x: null, y: 8 };
  let drag = null;

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function icon(name) {
    const s = {
      grip: '<path d="M6 9h12M6 15h12" stroke="currentColor" stroke-width="1.5"/>',
      collapse: '<path d="M8 12h8M12 8v8" stroke="currentColor" stroke-width="1.5"/>',
      edit: '<path d="M4 20h4l10-10-4-4L4 16v4z" stroke="currentColor" fill="none" stroke-width="1.5"/><path d="M14 6l4 4" stroke="currentColor" stroke-width="1.5"/>',
      bold: '<path d="M7 5h6a3 3 0 010 6H7zm0 6h7a3 3 0 010 6H7z" stroke="currentColor" fill="none" stroke-width="1.5"/>',
      italic: '<path d="M12 5h-2l-3 14h2l3-14z" fill="currentColor"/>',
      h2: '<path d="M5 6v12M5 12h8M17 6v12M17 12h-4v-6h4" stroke="currentColor" stroke-width="1.5"/>',
      undo: '<path d="M8 8H5l3-4M5 8a6 6 0 106 6" stroke="currentColor" fill="none" stroke-width="1.5"/>',
      redo: '<path d="M16 8h3l-3-4M19 8a6 6 0 11-6 6" stroke="currentColor" fill="none" stroke-width="1.5"/>',
      save: '<path d="M6 20h12V8l-4-4H6v16z" stroke="currentColor" fill="none" stroke-width="1.5"/><path d="M10 20v-6h4v6" stroke="currentColor" stroke-width="1.5"/>',
      draft: '<path d="M6 4h12v16H6z" stroke="currentColor" fill="none" stroke-width="1.5"/><path d="M9 9h6M9 13h6" stroke="currentColor" stroke-width="1.5"/>',
      del: '<path d="M6 7h12M9 7V5h6v2M8 7l1 12h6l1-12" stroke="currentColor" fill="none" stroke-width="1.5"/>',
      dup: '<rect x="7" y="7" width="10" height="10" stroke="currentColor" fill="none" stroke-width="1.5"/><path d="M5 5h10v10" stroke="currentColor" fill="none" stroke-width="1.5"/>',
      up: '<path d="M12 6v12M8 10l4-4 4 4" stroke="currentColor" stroke-width="1.5"/>',
      down: '<path d="M12 18V6M8 14l4 4 4-4" stroke="currentColor" stroke-width="1.5"/>',
      close: '<path d="M8 8l8 8M16 8l-8 8" stroke="currentColor" stroke-width="1.5"/>',
    };
    return `<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">${s[name] || ''}</svg>`;
  }

  function btn(act, label, extra) {
    return `<button type="button" class="ibtn${extra || ''}" data-act="${act}" data-tip="${label}" aria-label="${label}">${icon(act.split('-')[0] in { grip: 1, collapse: 1, edit: 1, bold: 1, italic: 1, h2: 1, undo: 1, redo: 1, save: 1, draft: 1 } ? act.split('-')[0] : act === 'toggle' ? 'edit' : act === 'restore' ? 'draft' : act)}</button>`;
  }

  const host = document.createElement('div');
  host.id = 'html-edit-host';
  const shadow = host.attachShadow({ mode: 'open' });
  shadow.innerHTML = `
<style>
:host { all: initial; }
*, *::before, *::after { box-sizing: border-box; }
.panel {
  --navy: ${NAVY}; --cyan: ${CYAN}; --amber: ${AMBER}; --ink: ${INK};
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--ink);
  background-color: var(--navy);
  background-image:
    linear-gradient(rgba(255,255,255,.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.06) 1px, transparent 1px);
  background-size: 12px 12px;
  border: 1px solid rgba(255,255,255,.85);
  border-radius: 4px;
  box-shadow: 0 8px 32px rgba(0,0,0,.35);
}
.toolbar {
  position: fixed; z-index: 2147483646; top: 8px; right: 8px;
  display: flex; flex-direction: column; gap: 0; min-width: 280px;
  transition: ${reducedMotion ? 'none' : 'opacity .15s ease, transform .15s ease'};
}
.toolbar.collapsed { min-width: auto; width: auto; }
.toolbar.collapsed .tb-body, .toolbar.collapsed .tb-title { display: none; }
.toolbar.collapsed .tb-head { border-bottom: none; }
.tb-head {
  display: flex; align-items: center; gap: 6px; padding: 6px 8px;
  border-bottom: 1px solid rgba(255,255,255,.35); cursor: grab;
}
.tb-head:active { cursor: grabbing; }
.tb-title { flex: 1; color: var(--cyan); font-size: 10px; }
.tb-body { padding: 8px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.group { display: flex; gap: 4px; align-items: center; }
.divider { width: 1px; height: 24px; background: rgba(255,255,255,.35); margin: 0 2px; }
.ibtn {
  width: 32px; height: 32px; padding: 0; margin: 0;
  display: inline-flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,.15); color: var(--ink);
  border: 1px solid rgba(255,255,255,.75); border-radius: 3px;
  cursor: pointer; position: relative;
  transition: ${reducedMotion ? 'none' : 'background .12s, border-color .12s, color .12s'};
}
.ibtn:hover { background: rgba(120,210,255,.12); border-color: var(--cyan); color: var(--cyan); }
.ibtn:active { transform: ${reducedMotion ? 'none' : 'translateY(1px)'}; background: rgba(120,210,255,.2); }
.ibtn.primary { border-color: var(--amber); color: var(--amber); }
.ibtn.primary:hover { background: rgba(255,196,80,.15); }
.ibtn.active { border-color: var(--amber); box-shadow: inset 0 0 0 1px var(--amber); color: var(--amber); }
.ibtn[data-tip]:hover::after {
  content: attr(data-tip); position: absolute; bottom: calc(100% + 6px); left: 50%;
  transform: translateX(-50%); white-space: nowrap; padding: 4px 8px;
  background: var(--navy); border: 1px solid var(--cyan); color: var(--cyan);
  font-size: 9px; letter-spacing: 0.08em; border-radius: 3px; pointer-events: none; z-index: 2;
}
.pill-label { padding: 0 10px; font-size: 10px; color: var(--amber); }
.hover-layer {
  position: fixed; z-index: 2147483644; pointer-events: none; display: none;
}
.hover-layer.on { display: block; }
.hover-svg { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
.hover-tag {
  position: absolute; top: -20px; left: 0; padding: 2px 6px;
  background: var(--navy); border: 1px solid var(--cyan); color: var(--cyan);
  font-size: 9px; letter-spacing: 0.1em;
}
.ctx {
  position: fixed; z-index: 2147483645; display: none; padding: 4px;
  flex-direction: row; gap: 4px;
}
.ctx.on { display: flex; }
.dialog-back {
  position: fixed; inset: 0; z-index: 2147483647; background: rgba(14,52,120,.55);
  display: none; align-items: center; justify-content: center; padding: 16px;
}
.dialog-back.on { display: flex; }
.dialog { width: min(360px, 100%); padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.dialog h2 { margin: 0; font-size: 11px; color: var(--cyan); font-weight: 600; }
.field label { display: block; margin-bottom: 4px; color: rgba(255,255,255,.8); font-size: 9px; }
.field input, .field textarea {
  width: 100%; padding: 8px 10px; font-family: inherit; font-size: 12px;
  text-transform: none; letter-spacing: normal;
  background: rgba(0,0,0,.25); color: var(--ink); border: 1px solid rgba(255,255,255,.6);
  border-radius: 3px;
}
.field input:focus, .field textarea:focus { outline: none; border-color: var(--cyan); box-shadow: 0 0 0 1px var(--cyan); }
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; }
.dialog-actions button {
  padding: 8px 14px; font-family: inherit; font-size: 10px; letter-spacing: 0.08em;
  text-transform: uppercase; cursor: pointer; border-radius: 3px;
  border: 1px solid rgba(255,255,255,.75); background: transparent; color: var(--ink);
}
.dialog-actions button.primary { border-color: var(--amber); color: var(--amber); }
.toast {
  position: fixed; z-index: 2147483648; bottom: 24px; left: 50%; transform: translateX(-50%);
  padding: 10px 16px; display: none; max-width: 90vw;
  border-color: var(--cyan); color: var(--cyan);
}
.toast.on { display: block; animation: ${reducedMotion ? 'none' : 'toast-in .2s ease'}; }
@keyframes toast-in { from { opacity: 0; transform: translateX(-50%) translateY(8px); } }
@media (prefers-reduced-motion: reduce) {
  .toolbar, .ibtn, .toast.on { transition: none; animation: none; }
}
</style>
<div class="toolbar panel" id="toolbar">
  <div class="tb-head" id="drag-handle">
    <button type="button" class="ibtn" data-act="grip" data-tip="Drag" aria-label="Drag">${icon('grip')}</button>
    <span class="tb-title">HTML · EDIT</span>
    <button type="button" class="ibtn" data-act="collapse" data-tip="Collapse" aria-label="Collapse">${icon('collapse')}</button>
  </div>
  <div class="tb-body">
    <div class="group">
      <button type="button" class="ibtn" data-act="toggle" data-tip="Edit mode (Ctrl+E)" aria-label="Edit">${icon('edit')}</button>
    </div>
    <span class="divider"></span>
    <div class="group fmt">
      <button type="button" class="ibtn" data-act="bold" data-tip="Bold" aria-label="Bold">${icon('bold')}</button>
      <button type="button" class="ibtn" data-act="italic" data-tip="Italic" aria-label="Italic">${icon('italic')}</button>
      <button type="button" class="ibtn" data-act="h2" data-tip="Heading 2" aria-label="Heading 2">${icon('h2')}</button>
    </div>
    <span class="divider"></span>
    <div class="group">
      <button type="button" class="ibtn" data-act="undo" data-tip="Undo" aria-label="Undo">${icon('undo')}</button>
      <button type="button" class="ibtn" data-act="redo" data-tip="Redo" aria-label="Redo">${icon('redo')}</button>
    </div>
    <span class="divider"></span>
    <div class="group">
      <button type="button" class="ibtn primary" data-act="save" data-tip="Save (Ctrl+S)" aria-label="Save">${icon('save')}</button>
      <button type="button" class="ibtn" data-act="restore" data-tip="Restore draft" aria-label="Restore draft">${icon('draft')}</button>
    </div>
  </div>
  <span class="pill-label" hidden id="pill">EDIT</span>
</div>
<div class="hover-layer panel" id="hover-layer">
  <svg class="hover-svg" id="hover-svg"></svg>
  <span class="hover-tag" id="hover-tag">P</span>
</div>
<div class="ctx panel" id="ctx"></div>
<div class="dialog-back" id="dialog-back">
  <div class="dialog panel" role="dialog" aria-modal="true">
    <h2 id="dialog-title">Edit</h2>
    <div id="dialog-fields"></div>
    <div class="dialog-actions">
      <button type="button" data-act="dialog-cancel">Cancel</button>
      <button type="button" class="primary" data-act="dialog-ok">Apply</button>
    </div>
  </div>
</div>
<div class="toast panel" id="toast" role="status"></div>`;

  document.documentElement.appendChild(host);

  const toolbar = shadow.getElementById('toolbar');
  const hoverLayer = shadow.getElementById('hover-layer');
  const hoverSvg = shadow.getElementById('hover-svg');
  const hoverTag = shadow.getElementById('hover-tag');
  const ctx = shadow.getElementById('ctx');
  const dialogBack = shadow.getElementById('dialog-back');
  const dialogTitle = shadow.getElementById('dialog-title');
  const dialogFields = shadow.getElementById('dialog-fields');
  const toast = shadow.getElementById('toast');
  const dragHandle = shadow.getElementById('drag-handle');
  let dialogTarget = null;
  let dialogKind = null;

  function tagLabel(el) {
    const t = el.tagName;
    if (t === 'IMG') return 'IMG';
    if (t === 'A') return 'A';
    if (/^H[1-6]$/.test(t)) return t;
    if (t === 'P') return 'P';
    if (t === 'LI') return 'LI';
    return t.length <= 4 ? t : t.slice(0, 3);
  }

  function snapshot() {
    undoStack.push(document.documentElement.outerHTML);
    if (undoStack.length > 40) undoStack.shift();
    redoStack.length = 0;
    try { localStorage.setItem(DRAFT_KEY, document.documentElement.outerHTML); } catch (e) {}
  }

  function textBlocks() {
    return document.querySelectorAll('p,h1,h2,h3,h4,li,td,th,figcaption,blockquote,div');
  }

  function setEditMode(on) {
    editMode = on;
    textBlocks().forEach((el) => {
      if (el.closest('#html-edit-host')) return;
      if (on) el.setAttribute('contenteditable', 'true');
      else el.removeAttribute('contenteditable');
    });
    shadow.querySelector('[data-act="toggle"]').classList.toggle('active', on);
    if (!on) hideHover();
  }

  function cleanDocument() {
    const clone = document.documentElement.cloneNode(true);
    clone.querySelector('#html-edit-host')?.remove();
    clone.querySelectorAll('[data-html-edit-injected]').forEach((n) => n.remove());
    clone.querySelectorAll('[contenteditable]').forEach((n) => n.removeAttribute('contenteditable'));
    clone.querySelectorAll('[data-html-edit-hover]').forEach((n) => n.removeAttribute('data-html-edit-hover'));
    let html = '<!DOCTYPE html>\n' + clone.outerHTML;
    html = html.replace(/\scontenteditable="(?:true|false)"/gi, '');
    html = html.replace(/\sdata-html-edit-hover="[^"]*"/gi, '');
    html = html.replace(/\sclass=""/g, '');
    return html;
  }

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('on');
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => toast.classList.remove('on'), 4000);
  }

  async function save() {
    const body = cleanDocument();
    if (location.protocol.startsWith('http')) {
      const res = await fetch('/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html: body }),
      });
      if (!res.ok) throw new Error('save failed');
      const data = await res.json();
      showToast('Saved · ' + (data.path || 'server'));
      return;
    }
    const blob = new Blob([body], { type: 'text/html' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = (document.title || 'page') + '.edited.html';
    a.click();
    showToast('Downloaded · ' + a.download);
  }

  function hideHover() {
    hoverLayer.classList.remove('on');
    hoverEl = null;
  }

  function positionHover(el) {
    const r = el.getBoundingClientRect();
    hoverLayer.style.left = r.left + 'px';
    hoverLayer.style.top = r.top + 'px';
    hoverLayer.style.width = r.width + 'px';
    hoverLayer.style.height = r.height + 'px';
    hoverTag.textContent = tagLabel(el);
    const w = r.width;
    const h = r.height;
    const pad = 4;
    hoverSvg.innerHTML = `
      <rect x="${pad}" y="${pad}" width="${w - pad * 2}" height="${h - pad * 2}"
        fill="none" stroke="${CYAN}" stroke-width="1" stroke-dasharray="4 3"/>
      <path stroke="${CYAN}" stroke-width="1.5" fill="none" d="
        M${pad},${pad + 6} V${pad} H${pad + 6}
        M${w - pad - 6},${pad} H${w - pad} V${pad + 6}
        M${w - pad},${h - pad - 6} V${h - pad} H${w - pad - 6}
        M${pad + 6},${h - pad} H${pad} V${h - pad - 6}"/>
    `;
    hoverLayer.classList.add('on');
  }

  function openDialog(kind, el) {
    dialogTarget = el;
    dialogKind = kind;
    dialogBack.classList.add('on');
    if (kind === 'link') {
      dialogTitle.textContent = 'Edit link';
      dialogFields.innerHTML = `
        <div class="field"><label for="he-href">Href</label><input id="he-href" type="url" value="${el.getAttribute('href') || ''}"></div>
        <div class="field"><label for="he-text">Text</label><input id="he-text" type="text" value="${(el.textContent || '').replace(/"/g, '&quot;')}"></div>`;
    } else {
      dialogTitle.textContent = 'Edit image';
      dialogFields.innerHTML = `
        <div class="field"><label for="he-src">Source URL or data URL</label>
        <textarea id="he-src" rows="3">${el.getAttribute('src') || ''}</textarea></div>
        <div class="field"><label for="he-file">Upload replacement</label>
        <input id="he-file" type="file" accept="image/*"></div>`;
      const fileInput = shadow.getElementById('he-file');
      fileInput?.addEventListener('change', () => {
        const f = fileInput.files?.[0];
        if (!f) return;
        const reader = new FileReader();
        reader.onload = () => { shadow.getElementById('he-src').value = reader.result; };
        reader.readAsDataURL(f);
      });
    }
    shadow.getElementById('he-href')?.focus();
  }

  function closeDialog() {
    dialogBack.classList.remove('on');
    dialogTarget = null;
    dialogKind = null;
  }

  function applyDialog() {
    if (!dialogTarget) return;
    snapshot();
    if (dialogKind === 'link') {
      const href = shadow.getElementById('he-href')?.value ?? '';
      const text = shadow.getElementById('he-text')?.value ?? '';
      dialogTarget.setAttribute('href', href);
      if (text) dialogTarget.textContent = text;
    } else {
      const src = shadow.getElementById('he-src')?.value ?? '';
      if (src) dialogTarget.setAttribute('src', src);
    }
    closeDialog();
  }

  function showCtx(el, x, y) {
    ctx.innerHTML = '';
    const acts = [
      ['ctx-del', 'Delete', 'del'],
      ['ctx-dup', 'Duplicate', 'dup'],
      ['ctx-up', 'Move up', 'up'],
      ['ctx-down', 'Move down', 'down'],
    ];
    acts.forEach(([act, tip, ic]) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'ibtn';
      b.dataset.act = act;
      b.dataset.tip = tip;
      b.innerHTML = icon(ic);
      b.addEventListener('click', () => {
        snapshot();
        if (act === 'ctx-del') el.remove();
        if (act === 'ctx-dup') el.parentNode?.insertBefore(el.cloneNode(true), el.nextSibling);
        if (act === 'ctx-up' && el.previousElementSibling) el.parentNode?.insertBefore(el, el.previousElementSibling);
        if (act === 'ctx-down' && el.nextElementSibling) el.parentNode?.insertBefore(el.nextElementSibling, el);
        ctx.classList.remove('on');
        hideHover();
      });
      ctx.appendChild(b);
    });
    ctx.style.left = x + 'px';
    ctx.style.top = y + 'px';
    ctx.classList.add('on');
  }

  function placeToolbar() {
    if (toolbarPos.x != null) {
      toolbar.style.right = 'auto';
      toolbar.style.left = toolbarPos.x + 'px';
      toolbar.style.top = toolbarPos.y + 'px';
    }
  }

  dragHandle.addEventListener('pointerdown', (ev) => {
    if (ev.target.closest('[data-act="collapse"]')) return;
    drag = { x: ev.clientX, y: ev.clientY, ox: toolbarPos.x ?? toolbar.getBoundingClientRect().left, oy: toolbarPos.y ?? toolbar.getBoundingClientRect().top };
    dragHandle.setPointerCapture(ev.pointerId);
  });
  dragHandle.addEventListener('pointermove', (ev) => {
    if (!drag) return;
    toolbarPos.x = drag.ox + (ev.clientX - drag.x);
    toolbarPos.y = drag.oy + (ev.clientY - drag.y);
    placeToolbar();
  });
  dragHandle.addEventListener('pointerup', () => { drag = null; });

  shadow.addEventListener('click', (ev) => {
    const act = ev.target.closest('[data-act]')?.getAttribute('data-act');
    if (!act) return;
    if (act === 'grip') return;
    if (act === 'collapse') {
      collapsed = !collapsed;
      toolbar.classList.toggle('collapsed', collapsed);
      shadow.getElementById('pill').hidden = !collapsed;
      return;
    }
    if (act === 'toggle') { snapshot(); setEditMode(!editMode); return; }
    if (act === 'save') { save().catch((e) => showToast('Error · ' + e.message)); return; }
    if (act === 'restore') {
      const d = localStorage.getItem(DRAFT_KEY);
      if (d) { document.documentElement.outerHTML = d; window.__HTML_EDIT_LOADED__ = false; location.reload(); }
      return;
    }
    if (act === 'undo' && undoStack.length) {
      redoStack.push(document.documentElement.outerHTML);
      document.documentElement.outerHTML = undoStack.pop();
      return;
    }
    if (act === 'redo' && redoStack.length) {
      undoStack.push(document.documentElement.outerHTML);
      document.documentElement.outerHTML = redoStack.pop();
      return;
    }
    if (act === 'dialog-cancel') { closeDialog(); return; }
    if (act === 'dialog-ok') { applyDialog(); return; }
    if (!editMode) return;
    if (act === 'bold') { snapshot(); document.execCommand('bold'); }
    if (act === 'italic') { snapshot(); document.execCommand('italic'); }
    if (act === 'h2') { snapshot(); document.execCommand('formatBlock', false, 'h2'); }
  });

  document.addEventListener('keydown', (ev) => {
    if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'e') {
      ev.preventDefault(); snapshot(); setEditMode(!editMode);
    }
    if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 's') {
      ev.preventDefault(); save().catch((e) => showToast('Error · ' + e.message));
    }
    if (ev.key === 'Escape') { closeDialog(); ctx.classList.remove('on'); }
  });

  document.addEventListener('mouseover', (ev) => {
    if (!editMode) return;
    const t = ev.target;
    if (!(t instanceof Element) || t.closest('#html-edit-host')) return;
    hoverEl = t;
    positionHover(t);
  }, true);

  document.addEventListener('mouseout', (ev) => {
    if (!editMode) return;
    if (ev.target === hoverEl) hideHover();
  }, true);

  document.addEventListener('click', (ev) => {
    if (!editMode) return;
    const t = ev.target;
    if (!(t instanceof Element) || t.closest('#html-edit-host')) return;
    if (t.tagName === 'IMG') {
      ev.preventDefault();
      openDialog('image', t);
      return;
    }
    if (t.tagName === 'A') {
      ev.preventDefault();
      openDialog('link', t);
      return;
    }
    if (t.closest('a') || t.closest('img')) return;
    showCtx(t, ev.pageX, ev.pageY);
  }, true);

  document.addEventListener('scroll', () => { if (hoverEl) positionHover(hoverEl); }, true);

  window.HTML_EDIT = { cleanDocument, setEditMode, save, openDialog, setEditModeOn: () => setEditMode(true) };
})();
