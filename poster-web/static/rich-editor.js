/**
 * rich-editor.js — IEG 海报拼搭器 · 富文本编辑器组件
 * =====================================================
 *
 * 设计原则（来自 2026-06-25 与 PM Dorrain 的最终需求确认）：
 *  1. 所见即所得（视觉层面）：编辑器与海报共享文字层 CSS，不强求容器 1:1
 *  2. 无品牌兜底：后端不改用户样式，渲染完全按编辑器输出
 *  3. 每个文字槽位 = 独立 Tiptap 实例 + 贴身浮动迷你工具栏
 *  4. 品牌纪律靠"能力限制"，不靠"事后覆盖"
 *
 * 槽位能力两档：
 *   - text-rich         ：字体 / 字号 / B / I / U / 字色 / 高亮
 *   - text-rich+image   ：上一档 + 行内图片（同行多张 / 自由拖拽 / 段落对齐）
 *
 * 集成方式：
 *   - 本文件是 ES module，通过 importmap 加载 Tiptap CDN
 *   - 把 RichEditor 组件挂到 window.RichEditor
 *   - app.js（非 module）在 FieldForm 注册时 `components: { FieldForm, RichEditor: window.RichEditor }`
 *   - 详见 POSTER_EDITOR_INTEGRATION.md
 *
 * 风格：Vue 3 Options API + 字符串模板（对齐 poster-web app.js 现有写法）
 */

import { Editor }       from '@tiptap/core';
import StarterKit       from '@tiptap/starter-kit';
import Underline        from '@tiptap/extension-underline';
import TextStyle        from '@tiptap/extension-text-style';
import Color            from '@tiptap/extension-color';
import Highlight        from '@tiptap/extension-highlight';
import FontFamily       from '@tiptap/extension-font-family';
import Image            from '@tiptap/extension-image';
import Placeholder      from '@tiptap/extension-placeholder';

/* ============================================================
 * 1) 预设常量
 * ============================================================ */
const FONT_FAMILIES = [
  { value: '',                                           label: '默认字体' },
  { value: 'TencentSans, "Tencent Sans", sans-serif',    label: '腾讯体' },
  { value: '"Source Han Sans CN", "思源黑体", sans-serif', label: '思源黑体' },
  { value: '"PingFang SC", sans-serif',                  label: '苹方' },
  { value: '"Microsoft YaHei", sans-serif',              label: '微软雅黑' },
  { value: 'Arial, sans-serif',                          label: 'Arial' },
  { value: '"Times New Roman", serif',                   label: 'Times New Roman' },
];

const FONT_SIZES_PRESET = [12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 60, 72];

const COLOR_SWATCHES = ['#111827', '#FFFFFF', '#2563EB', '#9333EA', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#FBBF24', '#7B2CBF'];
const HIGHLIGHT_SWATCHES = ['#FFF59D', '#FFCC80', '#A5D6A7', '#90CAF9', '#F48FB1', '#CE93D8', '#FFE0B2'];

/* ============================================================
 * 2) 自定义 Tiptap 扩展
 * ============================================================ */

/**
 * FontSize Mark
 * Tiptap 官方没有字号扩展。这里继承 TextStyle，加 fontSize attribute。
 * 渲染为 inline style: font-size: Xpx
 */
const FontSize = TextStyle.extend({
  name: 'fontSize',
  addAttributes() {
    return {
      fontSize: {
        default: null,
        parseHTML: el => el.style.fontSize || null,
        renderHTML: attrs => attrs.fontSize ? { style: `font-size:${attrs.fontSize}` } : {},
      },
    };
  },
  addCommands() {
    return {
      setFontSize: size => ({ chain }) =>
        chain().setMark('textStyle', { fontSize: size }).run(),
      unsetFontSize: () => ({ chain }) =>
        chain().setMark('textStyle', { fontSize: null }).removeEmptyTextStyle().run(),
    };
  },
});

/**
 * ImageInline 节点
 * 继承官方 Image，改为 inline 节点（可与文字、其它图片同行）。
 * 加 width/height attribute，存储拖拽后的尺寸。
 * NodeView 提供 8 方向拖拽手柄。
 */
const ImageInline = Image.extend({
  name: 'image',
  inline: true,
  group: 'inline',
  draggable: true,
  addAttributes() {
    return {
      src:    { default: null },
      alt:    { default: null },
      width:  { default: null, parseHTML: el => el.getAttribute('width'),  renderHTML: a => a.width  ? { width:  a.width  } : {} },
      height: { default: null, parseHTML: el => el.getAttribute('height'), renderHTML: a => a.height ? { height: a.height } : {} },
    };
  },
  addNodeView() {
    return ({ node, editor, getPos }) => {
      const wrap = document.createElement('span');
      wrap.className = 'rich-img-wrap';
      wrap.contentEditable = 'false';

      const img = document.createElement('img');
      img.src = node.attrs.src;
      if (node.attrs.alt)    img.alt    = node.attrs.alt;
      if (node.attrs.width)  img.style.width  = node.attrs.width  + 'px';
      if (node.attrs.height) img.style.height = node.attrs.height + 'px';
      wrap.appendChild(img);

      // 8 方向拖拽手柄
      const HANDLES = ['nw','n','ne','e','se','s','sw','w'];
      HANDLES.forEach(dir => {
        const h = document.createElement('span');
        h.className = 'rich-img-handle rich-img-handle-' + dir;
        h.dataset.dir = dir;
        wrap.appendChild(h);
        h.addEventListener('mousedown', e => startResize(e, dir));
      });

      function startResize(e, dir) {
        e.preventDefault();
        e.stopPropagation();
        const startX = e.clientX, startY = e.clientY;
        const startW = img.offsetWidth, startH = img.offsetHeight;
        const ratio = startW / startH;
        const keepRatio = e.shiftKey;
        document.body.style.cursor = getComputedStyle(h).cursor;

        function onMove(ev) {
          const dx = ev.clientX - startX;
          const dy = ev.clientY - startY;
          let w = startW, h0 = startH;
          if (dir.includes('e')) w = startW + dx;
          if (dir.includes('w')) w = startW - dx;
          if (dir.includes('s')) h0 = startH + dy;
          if (dir.includes('n')) h0 = startH - dy;
          if (keepRatio || ev.shiftKey) {
            if (Math.abs(dx) > Math.abs(dy)) h0 = w / ratio;
            else w = h0 * ratio;
          }
          w = Math.max(20, w);
          h0 = Math.max(20, h0);
          img.style.width  = w + 'px';
          img.style.height = h0 + 'px';
        }
        function onUp() {
          document.removeEventListener('mousemove', onMove);
          document.removeEventListener('mouseup', onUp);
          document.body.style.cursor = '';
          // 写回 attribute
          if (typeof getPos === 'function') {
            const pos = getPos();
            editor.chain().setNodeSelection(pos).updateAttributes('image', {
              width: img.offsetWidth,
              height: img.offsetHeight,
            }).run();
          }
        }
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
      }

      return { dom: wrap };
    };
  },
});

/**
 * Paragraph 扩展：加 imageAlign attribute
 * 段落级图片对齐：作用于段内所有图（一组整体左/中/右）
 * 实现：在 paragraph 上加 data-image-align 属性，CSS 控制段落 text-align（图片是 inline）
 */
import Paragraph from '@tiptap/extension-paragraph';
const ParagraphImageAlign = Paragraph.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      imageAlign: {
        default: null,
        parseHTML: el => el.getAttribute('data-image-align'),
        renderHTML: attrs => {
          if (!attrs.imageAlign) return {};
          return {
            'data-image-align': attrs.imageAlign,
            style: `text-align:${attrs.imageAlign}`,
          };
        },
      },
    };
  },
  addCommands() {
    return {
      setImageAlign: dir => ({ commands }) =>
        commands.updateAttributes('paragraph', { imageAlign: dir }),
      unsetImageAlign: () => ({ commands }) =>
        commands.updateAttributes('paragraph', { imageAlign: null }),
    };
  },
});

/* ============================================================
 * 3) Tiptap 工厂函数（按预设组装扩展集）
 * ============================================================ */
function createTiptap({ element, content, preset, placeholder, onUpdate, onFocus, onBlur, onSelectionUpdate }) {
  // 公共扩展
  const base = [
    StarterKit.configure({
      heading: false,           // 海报场景不用标题层级
      paragraph: false,         // 用我们自定义的 ParagraphImageAlign 替代
    }),
    ParagraphImageAlign,
    Underline,
    TextStyle,
    FontSize,
    Color,
    Highlight.configure({ multicolor: true }),
    FontFamily,
    Placeholder.configure({ placeholder: placeholder || '请输入内容…' }),
  ];

  // image 预设额外加图片节点
  const extensions = preset === 'text-rich+image' ? [...base, ImageInline] : base;

  return new Editor({
    element,
    extensions,
    content: content || '',
    onUpdate({ editor }) {
      onUpdate && onUpdate(editor.getHTML());
    },
    onFocus()  { onFocus && onFocus(); },
    onBlur()   { onBlur && onBlur(); },
    onSelectionUpdate({ editor }) {
      onSelectionUpdate && onSelectionUpdate(editor);
    },
  });
}

/* ============================================================
 * 4) RichEditor Vue 组件
 *    风格：Options API + 字符串模板（对齐 app.js 现有写法）
 * ============================================================ */
const RichEditor = {
  name: 'RichEditor',
  props: {
    modelValue: { type: String, default: '' },
    preset:     { type: String, default: 'text-rich' },      // 'text-rich' | 'text-rich+image'
    placeholder:{ type: String, default: '请输入内容…' },
    sessionId:  { type: String, default: '' },               // 用于上传接口
    uploadUrl:  { type: String, default: '/api/upload' },    // 图片上传端点
  },
  emits: ['update:modelValue'],
  data() {
    return {
      FONT_FAMILIES,
      FONT_SIZES_PRESET,
      COLOR_SWATCHES,
      HIGHLIGHT_SWATCHES,

      focused: false,                  // 控制工具栏显隐
      hasSelection: false,             // 是否有非空选区
      sizeInput: '',                   // 字号手动输入框值

      // 反映当前 mark 状态（用于按钮 active 态）
      isBold: false,
      isItalic: false,
      isUnderline: false,
      currentColor: '',
      currentBg: '',
      currentFontFamily: '',
      currentFontSize: '',
      currentImageAlign: '',

      _editor: null,                   // 不响应化，避免 ProseMirror 被代理破坏
      _blurTimer: null,
    };
  },
  computed: {
    allowImage() { return this.preset === 'text-rich+image'; },
  },
  watch: {
    // 外部 model 变化（如 reset、来自接口刷新）时同步 editor
    modelValue(newVal) {
      if (!this._editor) return;
      if (newVal === this._editor.getHTML()) return;
      this._editor.commands.setContent(newVal || '', false);
    },
  },
  mounted() {
    this._editor = createTiptap({
      element: this.$refs.editorEl,
      content: this.modelValue,
      preset: this.preset,
      placeholder: this.placeholder,
      onUpdate: (html) => this.$emit('update:modelValue', html),
      onFocus: () => {
        clearTimeout(this._blurTimer);
        this.focused = true;
      },
      onBlur: () => {
        // 延迟，避免点击工具栏按钮触发 blur 后工具栏立刻消失
        this._blurTimer = setTimeout(() => { this.focused = false; }, 180);
      },
      onSelectionUpdate: (ed) => this.syncState(ed),
    });
    // 暴露给外部（调试或链式调用）
    this.$el.__editor = this._editor;
  },
  beforeUnmount() {
    clearTimeout(this._blurTimer);
    this._editor && this._editor.destroy();
    this._editor = null;
  },
  methods: {
    /* ---- 状态同步 ---- */
    syncState(editor) {
      this.isBold      = editor.isActive('bold');
      this.isItalic    = editor.isActive('italic');
      this.isUnderline = editor.isActive('underline');
      const attrs = editor.getAttributes('textStyle');
      this.currentColor      = attrs.color || '';
      this.currentFontFamily = attrs.fontFamily || '';
      this.currentFontSize   = attrs.fontSize || '';
      const hl = editor.getAttributes('highlight');
      this.currentBg = hl.color || '';
      const para = editor.getAttributes('paragraph');
      this.currentImageAlign = para.imageAlign || '';
      const { from, to } = editor.state.selection;
      this.hasSelection = from !== to;
    },

    /* ---- 工具栏按钮事件（防 blur 抢焦点） ---- */
    keepFocus(e) { e.preventDefault(); },

    toggleBold()      { this._editor.chain().focus().toggleBold().run(); },
    toggleItalic()    { this._editor.chain().focus().toggleItalic().run(); },
    toggleUnderline() { this._editor.chain().focus().toggleUnderline().run(); },

    onFontFamilyChange(e) {
      const v = e.target.value;
      if (v) this._editor.chain().focus().setFontFamily(v).run();
      else   this._editor.chain().focus().unsetFontFamily().run();
    },
    onFontSizePick(size) {
      this._editor.chain().focus().setFontSize(size + 'px').run();
    },
    onFontSizeInput(e) {
      const raw = parseFloat(e.target.value);
      if (!raw || raw <= 0) return;
      this._editor.chain().focus().setFontSize(raw + 'px').run();
    },
    onColorPick(c)     { this._editor.chain().focus().setColor(c).run(); },
    onHighlightPick(c) { this._editor.chain().focus().toggleHighlight({ color: c }).run(); },
    onUnsetColor()     { this._editor.chain().focus().unsetColor().run(); },
    onUnsetHighlight() { this._editor.chain().focus().unsetHighlight().run(); },

    /* ---- 图片 ---- */
    triggerImage() {
      this.$refs.fileInput.click();
    },
    async onFilePicked(e) {
      const file = e.target.files && e.target.files[0];
      e.target.value = '';
      if (!file) return;

      // 不限制大小，仅给提示
      if (file.size > 5 * 1024 * 1024) {
        console.warn('[RichEditor] 图片较大 (' + (file.size/1024/1024).toFixed(1) + 'MB)，可能影响加载');
      }

      try {
        const url = await this.uploadImage(file);
        this._editor.chain().focus().insertContent({
          type: 'image',
          attrs: { src: url, alt: file.name },
        }).run();
      } catch (err) {
        console.error('[RichEditor] 图片上传失败', err);
        alert('图片上传失败：' + (err.message || err));
      }
    },
    async uploadImage(file) {
      // 复用 poster-web 现有 /api/upload；如端点不同请改 uploadUrl prop
      const fd = new FormData();
      fd.append('file', file);
      fd.append('session_id', this.sessionId || 'default');
      fd.append('asset_type', 'module_content_image');
      fd.append('asset_label', '富文本行内图片');
      const resp = await fetch(this.uploadUrl, { method: 'POST', body: fd });
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const data = await resp.json();
      // poster-web /api/upload 返回 { url: "/api/asset/...", path: "..." }
      return data.url || data.path || data.file_url || (data.data && data.data.url);
    },
    setImageAlign(dir) {
      this._editor.chain().focus().setImageAlign(dir).run();
    },
  },

  template: `
    <div class="rich-editor"
         :class="{ 'is-focused': focused }"
         :data-preset="preset">

      <!-- 贴身浮动迷你工具栏 -->
      <div class="rich-toolbar" v-show="focused" @mousedown="keepFocus">
        <!-- 字体 -->
        <select class="re-select re-select-font"
                :value="currentFontFamily"
                @change="onFontFamilyChange">
          <option v-for="f in FONT_FAMILIES" :key="f.value" :value="f.value"
                  :style="f.value ? { fontFamily: f.value } : {}">{{ f.label }}</option>
        </select>

        <!-- 字号 -->
        <div class="re-fontsize">
          <input class="re-fontsize-input"
                 type="text"
                 :value="currentFontSize"
                 placeholder="字号"
                 @change="onFontSizeInput" />
          <div class="re-fontsize-pop">
            <button v-for="s in FONT_SIZES_PRESET" :key="s"
                    type="button"
                    @mousedown="keepFocus"
                    @click="onFontSizePick(s)">{{ s }}</button>
          </div>
        </div>

        <span class="re-sep"></span>

        <button type="button" class="re-btn" :class="{ active: isBold }"
                @mousedown="keepFocus" @click="toggleBold" title="加粗 Ctrl+B"><b>B</b></button>
        <button type="button" class="re-btn" :class="{ active: isItalic }"
                @mousedown="keepFocus" @click="toggleItalic" title="斜体 Ctrl+I"><i>I</i></button>
        <button type="button" class="re-btn" :class="{ active: isUnderline }"
                @mousedown="keepFocus" @click="toggleUnderline" title="下划线 Ctrl+U"><u>U</u></button>

        <span class="re-sep"></span>

        <!-- 字色 -->
        <div class="re-pop">
          <button type="button" class="re-btn re-color-btn" @mousedown="keepFocus" title="字色">
            <span>A</span>
            <span class="re-color-bar" :style="{ background: currentColor || '#111' }"></span>
          </button>
          <div class="re-pop-panel">
            <div class="re-color-grid">
              <span v-for="c in COLOR_SWATCHES" :key="c"
                    class="re-swatch"
                    :style="{ background: c }"
                    @mousedown="keepFocus"
                    @click="onColorPick(c)"></span>
            </div>
            <button type="button" class="re-link" @mousedown="keepFocus" @click="onUnsetColor">清除颜色</button>
          </div>
        </div>

        <!-- 高亮 -->
        <div class="re-pop">
          <button type="button" class="re-btn re-color-btn" @mousedown="keepFocus" title="高亮">
            <span>▮</span>
            <span class="re-color-bar" :style="{ background: currentBg || '#FFEB3B' }"></span>
          </button>
          <div class="re-pop-panel">
            <div class="re-color-grid">
              <span v-for="c in HIGHLIGHT_SWATCHES" :key="c"
                    class="re-swatch"
                    :style="{ background: c }"
                    @mousedown="keepFocus"
                    @click="onHighlightPick(c)"></span>
            </div>
            <button type="button" class="re-link" @mousedown="keepFocus" @click="onUnsetHighlight">清除高亮</button>
          </div>
        </div>

        <!-- 图片（仅 text-rich+image 预设） -->
        <template v-if="allowImage">
          <span class="re-sep"></span>
          <button type="button" class="re-btn"
                  @mousedown="keepFocus" @click="triggerImage" title="插入图片">🖼</button>
          <button type="button" class="re-btn" :class="{ active: currentImageAlign==='left' }"
                  @mousedown="keepFocus" @click="setImageAlign('left')" title="本段图片左对齐">⯇</button>
          <button type="button" class="re-btn" :class="{ active: currentImageAlign==='center' }"
                  @mousedown="keepFocus" @click="setImageAlign('center')" title="本段图片居中">≡</button>
          <button type="button" class="re-btn" :class="{ active: currentImageAlign==='right' }"
                  @mousedown="keepFocus" @click="setImageAlign('right')" title="本段图片右对齐">⯈</button>
          <input ref="fileInput" type="file" accept="image/*" style="display:none"
                 @change="onFilePicked" />
        </template>
      </div>

      <!-- 编辑区 -->
      <div ref="editorEl" class="rich-content"></div>
    </div>
  `,
};

/* ============================================================
 * 5) 暴露给非 module 的 app.js
 *    app.js 通过 window.RichEditor 注册到 Vue 组件树
 * ============================================================ */
window.RichEditor = RichEditor;

// 标记加载完成（app.js 可监听以延后挂载）
window.__RichEditorReady = true;
document.dispatchEvent(new CustomEvent('rich-editor-ready'));
console.log('%c[rich-editor] ready, RichEditor mounted on window', 'color:#10b981;font-weight:700');

export { RichEditor, createTiptap, FontSize, ImageInline, ParagraphImageAlign };
