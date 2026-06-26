/*
 * IEG isolated poster editor runtime.
 * WARNING: This runtime is intentionally isolated from legacy-app-adapter.js. If legacy-app-adapter.js is removed later,
 * keep this file or migrate its logic into frontend/src/editor-core/PosterEditor.vue before deleting the old reference.
 */
(function () {
  'use strict';

  const ROOT_CLASS = 'pe-root-ieg-poster-editor-20260626';
  const STYLE_ID = 'pe-style-ieg-poster-editor-20260626';
  const DEFAULT_EMPTY_CONTENT = '<p></p>';
  const DEFAULT_IMAGE_WIDTH = '300';
  const DEFAULT_IMAGE_STYLE = 'max-width:100%;height:auto;vertical-align:middle;';
  const YELLOW_HIGHLIGHT = '#fff59d';

  function cleanCssValue(value) {
    return String(value || '').replace(/[<>]/g, '').replace(/!important/gi, '').trim();
  }

  function normalizeFontSize(value) {
    const raw = cleanCssValue(value);
    if (!raw) return '18px';
    if (/^\d+(\.\d+)?px$/.test(raw)) return raw;
    if (/^\d+(\.\d+)?$/.test(raw)) return `${raw}px`;
    return '18px';
  }

  function normalizeFontFamily(value) {
    const raw = cleanCssValue(value);
    if (!raw) return 'Arial';
    const allowed = ['Arial', 'SimHei', 'SimSun', 'KaiTi'];
    if (allowed.includes(raw)) return raw;
    return raw.replace(/;/g, '').replace(/"/g, '').replace(/'/g, '');
  }

  function normalizeColor(value, fallback = '#111827') {
    const raw = cleanCssValue(value);
    if (!raw) return fallback;
    if (/^#[0-9a-fA-F]{3}$/.test(raw)) return raw;
    if (/^#[0-9a-fA-F]{6}$/.test(raw)) return raw;
    if (/^rgba?\([^)]+\)$/.test(raw)) return raw;
    if (/^hsla?\([^)]+\)$/.test(raw)) return raw;
    return fallback;
  }

  function normalizeImageWidth(value) {
    const raw = cleanCssValue(value);
    if (!raw) return DEFAULT_IMAGE_WIDTH;
    const numeric = raw.replace('px', '').trim();
    const parsed = Number(numeric);
    if (!Number.isFinite(parsed)) return DEFAULT_IMAGE_WIDTH;
    return String(Math.round(Math.max(40, Math.min(1200, parsed))));
  }

  function normalizeImageStyle(value) {
    const raw = cleanCssValue(value);
    const style = raw || DEFAULT_IMAGE_STYLE;
    const hasMaxWidth = /max-width\s*:/.test(style);
    const hasHeight = /height\s*:/.test(style);
    const hasVerticalAlign = /vertical-align\s*:/.test(style);
    const parts = [];
    if (style) parts.push(style.replace(/;+$/, ''));
    if (!hasMaxWidth) parts.push('max-width:100%');
    if (!hasHeight) parts.push('height:auto');
    if (!hasVerticalAlign) parts.push('vertical-align:middle');
    return `${parts.join(';')};`;
  }

  function normalizeHtmlForCompare(html) {
    return String(html || '').replace(/\s+/g, ' ').replace(/>\s+</g, '><').trim();
  }

  function dedupeAdjacentImagesInHtml(html) {
    const source = String(html || '').trim();
    if (!source) return DEFAULT_EMPTY_CONTENT;
    if (typeof window.DOMParser === 'undefined') return source;
    const parser = new window.DOMParser();
    const doc = parser.parseFromString(source, 'text/html');
    Array.from(doc.body.querySelectorAll('img')).forEach((img) => {
      img.setAttribute('width', normalizeImageWidth(img.getAttribute('width') || img.style.width || DEFAULT_IMAGE_WIDTH));
      img.setAttribute('style', normalizeImageStyle(img.getAttribute('style') || DEFAULT_IMAGE_STYLE));
    });
    Array.from(doc.body.querySelectorAll('p, div, span')).forEach((parent) => {
      const children = Array.from(parent.childNodes);
      let previousImageKey = '';
      children.forEach((node) => {
        if (node.nodeType === Node.TEXT_NODE) {
          if ((node.textContent || '').replace(/\u200B/g, '').trim()) previousImageKey = '';
          return;
        }
        if (!(node instanceof HTMLElement)) {
          previousImageKey = '';
          return;
        }
        const img = node.matches('img') ? node : node.querySelector(':scope > img');
        if (!img) {
          previousImageKey = '';
          return;
        }
        const key = [img.getAttribute('src') || '', normalizeImageWidth(img.getAttribute('width') || img.style.width || DEFAULT_IMAGE_WIDTH)].join('|');
        if (key && key === previousImageKey) {
          node.remove();
          return;
        }
        previousImageKey = key;
      });
    });
    return doc.body.innerHTML.trim() || DEFAULT_EMPTY_CONTENT;
  }

  function normalizeIncomingContent(html) {
    const source = String(html || '').trim();
    if (!source) return DEFAULT_EMPTY_CONTENT;
    return dedupeAdjacentImagesInHtml(source);
  }

  function normalizeJsonForLegacy(json) {
    function walk(node) {
      if (Array.isArray(node)) return node.map(walk);
      if (!node || typeof node !== 'object') return node;
      const cloned = {};
      Object.keys(node).forEach((key) => {
        if (key === 'content' || key === 'marks' || key === 'attrs' || key === 'type') return;
        cloned[key] = walk(node[key]);
      });
      if (node.type === 'peTextStyle') cloned.type = 'textStyle';
      else if (node.type === 'peHighlight') cloned.type = 'highlight';
      else if (node.type === 'peResizedImage') cloned.type = 'image';
      else cloned.type = node.type;
      if (Array.isArray(node.content)) cloned.content = node.content.map(walk);
      if (Array.isArray(node.marks)) cloned.marks = node.marks.map(walk);
      if (node.attrs && typeof node.attrs === 'object') {
        cloned.attrs = Object.assign({}, node.attrs);
        if (node.type === 'peResizedImage' || node.type === 'image' || node.type === 'posterImage') {
          cloned.attrs.width = normalizeImageWidth(cloned.attrs.width || cloned.attrs.widthPct || DEFAULT_IMAGE_WIDTH);
          cloned.attrs.style = normalizeImageStyle(cloned.attrs.style || DEFAULT_IMAGE_STYLE);
          if (cloned.attrs.path && !cloned.attrs.src) cloned.attrs.src = `/api/skill-asset?path=${encodeURIComponent(cloned.attrs.path)}`;
        }
      }
      return cloned;
    }
    return walk(json || { type: 'doc', content: [{ type: 'paragraph' }] });
  }

  function legacyJsonToPeJson(json) {
    function walk(node) {
      if (Array.isArray(node)) return node.map(walk);
      if (!node || typeof node !== 'object') return node;
      const cloned = {};
      Object.keys(node).forEach((key) => {
        if (key === 'content' || key === 'marks' || key === 'attrs' || key === 'type') return;
        cloned[key] = walk(node[key]);
      });
      if (node.type === 'textStyle') cloned.type = 'peTextStyle';
      else if (node.type === 'highlight') cloned.type = 'peHighlight';
      else if (node.type === 'image' || node.type === 'posterImage') cloned.type = 'peResizedImage';
      else cloned.type = node.type;
      if (Array.isArray(node.content)) cloned.content = node.content.map(walk);
      if (Array.isArray(node.marks)) cloned.marks = node.marks.map(walk);
      if (node.attrs && typeof node.attrs === 'object') {
        cloned.attrs = Object.assign({}, node.attrs);
        if (node.type === 'image' || node.type === 'posterImage' || node.type === 'peResizedImage') {
          const source = cloned.attrs.src || cloned.attrs.url || (cloned.attrs.path ? `/api/skill-asset?path=${encodeURIComponent(cloned.attrs.path)}` : '');
          cloned.attrs.src = source;
          cloned.attrs.width = normalizeImageWidth(cloned.attrs.width || cloned.attrs.widthPct || DEFAULT_IMAGE_WIDTH);
          cloned.attrs.style = normalizeImageStyle(cloned.attrs.style || DEFAULT_IMAGE_STYLE);
        }
      }
      return cloned;
    }
    return walk(json || { type: 'doc', content: [{ type: 'paragraph' }] });
  }

  function contentJsonFromTarget(target, key) {
    const fieldJson = target?.[`${key}_editor_json`];
    if (fieldJson && typeof fieldJson === 'object' && fieldJson.type === 'doc') return legacyJsonToPeJson(fieldJson);
    if (key === 'content') {
      if (target?.editor_json && typeof target.editor_json === 'object' && target.editor_json.type === 'doc') return legacyJsonToPeJson(target.editor_json);
      if (target?.content_editor_json && typeof target.content_editor_json === 'object' && target.content_editor_json.type === 'doc') return legacyJsonToPeJson(target.content_editor_json);
    }
    return null;
  }

  function installStyle() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
.${ROOT_CLASS} { isolation:isolate !important; contain:layout style !important; white-space:normal !important; cursor:text !important; }
.${ROOT_CLASS} .ProseMirror { min-height:inherit !important; outline:none !important; width:100% !important; white-space:pre-wrap !important; word-break:normal !important; overflow-wrap:anywhere !important; line-break:auto !important; color:inherit !important; font-size:inherit !important; font-family:inherit !important; line-height:inherit !important; }
.${ROOT_CLASS} .ProseMirror p { margin:0 0 0.65em !important; }
.${ROOT_CLASS} .ProseMirror p:last-child { margin-bottom:0 !important; }
.${ROOT_CLASS} .ProseMirror strong { font-weight:bold !important; }
.${ROOT_CLASS} .ProseMirror em { font-style:italic !important; }
.${ROOT_CLASS} .ProseMirror u { text-decoration:underline !important; }
.${ROOT_CLASS} .ProseMirror span { display:inline !important; }
.${ROOT_CLASS} .ProseMirror mark { padding:0 0.08em !important; border-radius:3px !important; color:inherit; }
.${ROOT_CLASS} .ProseMirror img { display:inline-block !important; max-width:100% !important; height:auto !important; vertical-align:middle !important; border-radius:8px !important; margin:4px !important; }
.${ROOT_CLASS} .ProseMirror img.ProseMirror-selectednode { outline:3px solid #2563eb !important; outline-offset:3px !important; }
.${ROOT_CLASS} .pe-inline-image-ieg-poster-editor-20260626 { display:inline-block !important; max-width:100% !important; height:auto !important; vertical-align:middle !important; }
`;
    document.head.appendChild(style);
  }

  function buildExtensions(T) {
    const CustomTextStyle = T.TextStyle.extend({
      name: 'peTextStyle',
      addAttributes() {
        return {
          ...(this.parent?.() || {}),
          fontSize: {
            default: null,
            parseHTML: (element) => element.style.fontSize ? normalizeFontSize(element.style.fontSize) : null,
            renderHTML: (attributes) => attributes.fontSize ? { style: `font-size:${normalizeFontSize(attributes.fontSize)} !important;` } : {},
          },
          fontFamily: {
            default: null,
            parseHTML: (element) => element.style.fontFamily ? normalizeFontFamily(element.style.fontFamily) : null,
            renderHTML: (attributes) => attributes.fontFamily ? { style: `font-family:${normalizeFontFamily(attributes.fontFamily)} !important;` } : {},
          },
          color: {
            default: null,
            parseHTML: (element) => element.style.color || null,
            renderHTML: (attributes) => attributes.color ? { style: `color:${normalizeColor(attributes.color)} !important;` } : {},
          },
        };
      },
      renderHTML({ HTMLAttributes }) {
        return ['span', T.mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), 0];
      },
    });

    const CustomColor = T.Extension.create({
      name: 'peColor',
      addCommands() {
        return {
          setColor: (color) => ({ chain }) => chain().setMark('peTextStyle', { color: normalizeColor(color) }).run(),
          unsetColor: () => ({ chain }) => chain().setMark('peTextStyle', { color: null }).removeEmptyTextStyle().run(),
        };
      },
    });

    const CustomHighlight = T.Highlight.extend({
      name: 'peHighlight',
      addOptions() {
        return { ...(this.parent?.() || {}), multicolor: true };
      },
      addAttributes() {
        return {
          color: {
            default: null,
            parseHTML: (element) => element.getAttribute('data-color') || element.style.backgroundColor || null,
            renderHTML: (attributes) => {
              const color = normalizeColor(attributes.color || YELLOW_HIGHLIGHT, YELLOW_HIGHLIGHT);
              return { 'data-color': color, style: `background-color:${color} !important;` };
            },
          },
        };
      },
      renderHTML({ HTMLAttributes }) {
        return ['mark', T.mergeAttributes(HTMLAttributes), 0];
      },
    });

    const CustomFontSize = T.Extension.create({
      name: 'peFontSize',
      addCommands() {
        return {
          setFontSize: (fontSize) => ({ chain }) => chain().setMark('peTextStyle', { fontSize: normalizeFontSize(fontSize) }).run(),
          unsetFontSize: () => ({ chain }) => chain().setMark('peTextStyle', { fontSize: null }).removeEmptyTextStyle().run(),
        };
      },
    });

    const CustomFontFamily = T.Extension.create({
      name: 'peFontFamily',
      addCommands() {
        return {
          setFontFamily: (fontFamily) => ({ chain }) => chain().setMark('peTextStyle', { fontFamily: normalizeFontFamily(fontFamily) }).run(),
          unsetFontFamily: () => ({ chain }) => chain().setMark('peTextStyle', { fontFamily: null }).removeEmptyTextStyle().run(),
        };
      },
    });

    const ResizedImage = T.Node.create({
      name: 'peResizedImage',
      group: 'inline',
      inline: true,
      atom: true,
      draggable: true,
      addAttributes() {
        return {
          src: { default: null },
          alt: { default: null },
          title: { default: null },
          width: {
            default: DEFAULT_IMAGE_WIDTH,
            parseHTML: (element) => normalizeImageWidth(element.getAttribute('width') || element.style.width || DEFAULT_IMAGE_WIDTH),
            renderHTML: (attributes) => ({ width: normalizeImageWidth(attributes.width || DEFAULT_IMAGE_WIDTH) }),
          },
          style: {
            default: DEFAULT_IMAGE_STYLE,
            parseHTML: (element) => normalizeImageStyle(element.getAttribute('style') || DEFAULT_IMAGE_STYLE),
            renderHTML: (attributes) => ({ style: normalizeImageStyle(attributes.style || DEFAULT_IMAGE_STYLE) }),
          },
        };
      },
      parseHTML() {
        return [{ tag: 'img[src]' }];
      },
      renderHTML({ HTMLAttributes }) {
        return ['img', T.mergeAttributes(HTMLAttributes, {
          class: 'pe-inline-image-ieg-poster-editor-20260626',
          width: normalizeImageWidth(HTMLAttributes.width || DEFAULT_IMAGE_WIDTH),
          style: normalizeImageStyle(HTMLAttributes.style || DEFAULT_IMAGE_STYLE),
        })];
      },
      addCommands() {
        return {
          setImage: (options) => ({ commands }) => commands.insertContent({ type: this.name, attrs: Object.assign({}, options, { width: normalizeImageWidth(options?.width || DEFAULT_IMAGE_WIDTH), style: normalizeImageStyle(options?.style || DEFAULT_IMAGE_STYLE) }) }),
        };
      },
    });

    const CustomTextAlign = T.TextAlign.extend({ name: 'peTextAlign' }).configure({
      types: ['paragraph'],
      alignments: ['left', 'center', 'right'],
      defaultAlignment: 'left',
    });

    return [
      T.StarterKit.configure({
        history: true,
        paragraph: true,
        bold: true,
        italic: true,
        strike: false,
        code: false,
        heading: false,
        blockquote: false,
        bulletList: false,
        orderedList: false,
        codeBlock: false,
        horizontalRule: false,
        hardBreak: true,
        dropcursor: true,
        gapcursor: true,
      }),
      CustomTextStyle,
      CustomColor,
      CustomHighlight.configure({ multicolor: true }),
      CustomFontFamily,
      CustomFontSize,
      CustomTextAlign,
      ResizedImage,
    ];
  }

  function normalizeContentFromTarget(target, key) {
    const json = contentJsonFromTarget(target, key);
    if (json) return json;
    const html = target?.[`${key}_html`] || '';
    const text = target?.[key] || '';
    if (html) return normalizeIncomingContent(html);
    if (text) return normalizeIncomingContent(`<p>${String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')}</p>`);
    return DEFAULT_EMPTY_CONTENT;
  }

  function create(options) {
    installStyle();
    const T = window.TIPTAP;
    if (!T || !T.Editor) return null;
    const el = options.el;
    const target = options.target;
    const key = options.key;
    const slot = options.slot || 'body';
    if (!el || !target || !key) return null;

    el.classList.add(ROOT_CLASS);
    el.classList.add('tiptap-ready');
    el.setAttribute('contenteditable', 'false');
    el.setAttribute('data-pe-isolated-editor', '1');
    el.removeAttribute('v-focus');
    el.removeAttribute('v-rich-html');
    el.removeAttribute('data-v-rich-html');
    el.innerHTML = '';

    const context = { target, key, slot, el };
    const editor = new T.Editor({
      element: el,
      extensions: buildExtensions(T),
      content: normalizeContentFromTarget(target, key),
      editorProps: {
        richContext: context,
        attributes: {
          class: 'pe-prosemirror-ieg-poster-editor-20260626',
          spellcheck: 'false',
        },
      },
      onCreate({ editor }) {
        options.onUpdate?.(editor);
      },
      onUpdate({ editor }) {
        options.onUpdate?.(editor);
      },
      onFocus({ editor }) {
        options.onFocus?.(editor);
      },
      onSelectionUpdate({ editor }) {
        options.onSelectionUpdate?.(editor);
      },
      onBlur() {
        options.onBlur?.(editor);
      },
    });

    editor.__richContext = context;
    editor.__peIsolatedEditor = true;
    const originalGetJSON = editor.getJSON.bind(editor);
    const originalGetHTML = editor.getHTML.bind(editor);
    editor.getJSON = function getJSONForLegacy() {
      return normalizeJsonForLegacy(originalGetJSON());
    };
    editor.getHTML = function getHTMLForLegacy() {
      return dedupeAdjacentImagesInHtml(originalGetHTML());
    };
    editor.peRawGetJSON = originalGetJSON;
    editor.peRawGetHTML = originalGetHTML;
    editor.peUpdateContext = function peUpdateContext(next) {
      editor.__richContext = next;
      editor.options.editorProps.richContext = next;
    };
    editor.peSetExternalContent = function peSetExternalContent(nextTarget, nextKey) {
      const nextHtml = normalizeContentFromTarget(nextTarget, nextKey);
      const currentHtml = editor.getHTML();
      if (normalizeHtmlForCompare(nextHtml) !== normalizeHtmlForCompare(currentHtml)) {
        editor.commands.setContent(nextHtml, false);
      }
    };
    return editor;
  }

  window.IEG_POSTER_EDITOR_ISOLATED = {
    create,
    version: '20260626-isolated-poster-editor',
  };
})();
