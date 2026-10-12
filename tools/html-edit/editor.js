(function () {
  'use strict';
  if (window.__HTML_EDIT_LOADED__) return;
  window.__HTML_EDIT_LOADED__ = true;

  const DRAFT_KEY = 'html-edit:draft';
  const undoStack = [];
  const redoStack = [];
  let editMode = false;
  let selected = null;

  const host = document.createElement('div');
  host.id = 'html-edit-host';
  const shadow = host.attachShadow({ mode: 'open' });
  shadow.innerHTML = `
<style>
:host { all: initial; font-family: ui-monospace, monospace; font-size: 12px; }
.bar { position: fixed; z-index: 2147483646; top: 8px; right: 8px; display: flex; gap: 6px; flex-wrap: wrap;
  background: #0E3478; color: #fff; border: 1px solid #78D2FF; padding: 8px; max-width: 360px; }
.bar button { background: transparent; color: #fff; border: 1px solid #78D2FF; padding: 4px 8px; cursor: pointer; }
.bar button.primary { border-color: #FFC450; color: #FFC450; }
.bar button:hover { background: rgba(120,210,255,.15); }
.hint { color: #78D2FF; margin: 0 0 6px; width: 100%; }
.menu { position: fixed; z-index: 2147483645; background: #0E3478; border: 1px solid #78D2FF; padding: 4px; display: none; }
.menu button { display: block; width: 100%; margin: 2px 0; }
</style>
<div class="bar" part="toolbar">
  <p class="hint">html-edit · Ctrl+E toggle · Ctrl+S save</p>
  <button type="button" data-act="toggle">Edit</button>
  <button type="button" data-act="bold"><b>B</b></button>
  <button type="button" data-act="italic"><i>I</i></button>
  <button type="button" data-act="h2">H2</button>
  <button type="button" data-act="undo">Undo</button>
  <button type="button" data-act="redo">Redo</button>
  <button type="button" class="primary" data-act="save">Save</button>
  <button type="button" data-act="restore">Restore draft</button>
</div>
<div class="menu" id="ctx"></div>`;
  document.documentElement.appendChild(host);
  const bar = shadow.querySelector('.bar');
  const ctx = shadow.getElementById('ctx');

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
    shadow.querySelector('[data-act="toggle"]').textContent = on ? 'Editing' : 'Edit';
  }

  function cleanDocument() {
    const clone = document.documentElement.cloneNode(true);
    clone.querySelector('#html-edit-host')?.remove();
    clone.querySelectorAll('[data-html-edit-injected]').forEach((n) => n.remove());
    clone.querySelectorAll('[contenteditable]').forEach((n) => n.removeAttribute('contenteditable'));
    clone.querySelectorAll('.html-edit-hover').forEach((n) => n.classList.remove('html-edit-hover'));
    let html = '<!DOCTYPE html>\n' + clone.outerHTML;
    html = html.replace(/\scontenteditable="(?:true|false)"/gi, '');
    html = html.replace(/\sclass=""/g, '');
    return html;
  }

  async function save() {
    const body = cleanDocument();
    if (location.protocol.startsWith('http')) {
      const res = await fetch('/save', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html: body }) });
      if (!res.ok) throw new Error('save failed');
      alert('Saved on server.');
      return;
    }
    const blob = new Blob([body], { type: 'text/html' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = (document.title || 'page') + '.edited.html';
    a.click();
  }

  function wrapCmd(fn) {
    return () => { snapshot(); fn(); };
  }

  bar.addEventListener('click', (ev) => {
    const act = ev.target.closest('[data-act]')?.getAttribute('data-act');
    if (!act) return;
    if (act === 'toggle') { snapshot(); setEditMode(!editMode); return; }
    if (act === 'save') { save().catch((e) => alert(e.message)); return; }
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
    if (!editMode) return;
    if (act === 'bold') wrapCmd(() => document.execCommand('bold'))();
    if (act === 'italic') wrapCmd(() => document.execCommand('italic'))();
    if (act === 'h2') wrapCmd(() => document.execCommand('formatBlock', false, 'h2'))();
  });

  document.addEventListener('keydown', (ev) => {
    if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'e') {
      ev.preventDefault(); snapshot(); setEditMode(!editMode);
    }
    if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 's') {
      ev.preventDefault(); save().catch((e) => alert(e.message));
    }
  });

  document.addEventListener('mouseover', (ev) => {
    if (!editMode) return;
    const t = ev.target;
    if (!(t instanceof Element) || t.closest('#html-edit-host')) return;
    t.classList.add('html-edit-hover');
    t.style.outline = '1px dashed #78D2FF';
  }, true);
  document.addEventListener('mouseout', (ev) => {
    const t = ev.target;
    if (t instanceof Element) { t.classList.remove('html-edit-hover'); t.style.outline = ''; }
  }, true);

  document.addEventListener('click', (ev) => {
    if (!editMode) return;
    const t = ev.target;
    if (!(t instanceof Element) || t.closest('#html-edit-host')) return;
    if (t.tagName === 'IMG') {
      ev.preventDefault();
      const src = prompt('Image URL or paste data URL', t.getAttribute('src') || '');
      if (src) { snapshot(); t.setAttribute('src', src); }
      return;
    }
    if (t.tagName === 'A') {
      ev.preventDefault();
      const href = prompt('Link href', t.getAttribute('href') || '');
      const text = prompt('Link text', t.textContent || '');
      if (href !== null) { snapshot(); t.setAttribute('href', href); if (text) t.textContent = text; }
      return;
    }
    selected = t;
    ctx.style.display = 'block';
    ctx.style.left = ev.pageX + 'px';
    ctx.style.top = ev.pageY + 'px';
    ctx.innerHTML = '';
    ['Delete', 'Duplicate', 'Move up', 'Move down'].forEach((label) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      b.addEventListener('click', () => {
        snapshot();
        if (label === 'Delete') t.remove();
        if (label === 'Duplicate') t.parentNode?.insertBefore(t.cloneNode(true), t.nextSibling);
        if (label === 'Move up' && t.previousElementSibling) t.parentNode?.insertBefore(t, t.previousElementSibling);
        if (label === 'Move down' && t.nextElementSibling) t.parentNode?.insertBefore(t.nextElementSibling, t);
        ctx.style.display = 'none';
      });
      ctx.appendChild(b);
    });
  }, true);

  window.HTML_EDIT = { cleanDocument, setEditMode, save };
})();
