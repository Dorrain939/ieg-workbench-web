import { uploadAsset } from "./api.js";

const mountedEditors = new Map();
let activeEditor = null;

function htmlToText(html) {
  const div = document.createElement("div");
  div.innerHTML = html || "";
  return (div.textContent || "").trim();
}

function ensureTargetFields(target, key) {
  if (!target[`${key}_html`] && target[key]) {
    const safe = String(target[key]).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
    target[`${key}_html`] = `<p>${safe}</p>`;
  }
}

export function getActiveEditor() {
  return activeEditor;
}

export function setActiveEditor(editor) {
  activeEditor = editor;
}

export function destroyEditors() {
  for (const editor of mountedEditors.values()) {
    try { editor.destroy?.(); } catch {}
  }
  mountedEditors.clear();
  activeEditor = null;
}

export function mountEditor({ id, el, target, key, onChange }) {
  if (!id || !el || !target || !key) return null;
  if (mountedEditors.has(id)) return mountedEditors.get(id);
  ensureTargetFields(target, key);
  const factory = window.IEG_POSTER_EDITOR_ISOLATED;
  if (!factory?.create) throw new Error("独立编辑器运行时未加载");
  const editor = factory.create({
    el,
    target,
    key,
    slot: id,
    onFocus(ed) { activeEditor = ed; },
    onSelectionUpdate(ed) { activeEditor = ed; },
    onUpdate(ed) {
      target[`${key}_html`] = ed.getHTML();
      target[`${key}_editor_json`] = ed.getJSON();
      target[key] = htmlToText(target[`${key}_html`]);
      onChange?.(target, key, ed);
    },
  });
  if (editor) mountedEditors.set(id, editor);
  return editor;
}

export function runEditorCommand(command, value) {
  const editor = activeEditor;
  if (!editor || editor.isDestroyed) return false;
  const chain = editor.chain().focus();
  if (command === "bold") return chain.toggleBold().run();
  if (command === "italic") return chain.toggleItalic().run();
  if (command === "underline") return chain.toggleUnderline().run();
  if (command === "fontSize") return chain.setFontSize(value).run();
  if (command === "fontFamily") return chain.setFontFamily(value).run();
  if (command === "color") return chain.setColor(value).run();
  if (command === "highlight") return chain.toggleHighlight({ color: value || "#fff59d" }).run();
  if (command === "align") return chain.setTextAlign(value || "left").run();
  return false;
}

export async function insertImagesIntoActiveEditor(files, sessionId) {
  const editor = activeEditor;
  if (!editor || editor.isDestroyed || !files?.length) return [];
  const uploaded = [];
  for (const file of files) {
    const item = await uploadAsset(file, sessionId, "module_content_image", file.name || "正文内嵌图片");
    uploaded.push(item);
    editor.chain().focus().insertContent("\u200B").setImage({
      src: item.url,
      path: item.path,
      alt: item.filename || file.name || "image",
      width: "300",
      style: "max-width:100%;height:auto;vertical-align:middle;",
    }).insertContent(" ").run();
  }
  return uploaded;
}
