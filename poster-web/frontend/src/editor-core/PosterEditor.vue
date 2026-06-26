<template>
  <div class="pe-root-ieg-poster-editor-20260626">
    <div class="pe-toolbar-ieg-poster-editor-20260626" @mousedown.prevent>
      <button
        type="button"
        class="pe-toolbar-button-ieg-poster-editor-20260626"
        :class="{ 'pe-active-ieg-poster-editor-20260626': isMarkActive('bold') }"
        :disabled="!editorReady"
        title="加粗"
        @click="toggleBold"
      >
        B
      </button>

      <button
        type="button"
        class="pe-toolbar-button-ieg-poster-editor-20260626"
        :class="{ 'pe-active-ieg-poster-editor-20260626': isMarkActive('italic') }"
        :disabled="!editorReady"
        title="斜体"
        @click="toggleItalic"
      >
        <em>I</em>
      </button>

      <button
        type="button"
        class="pe-toolbar-button-ieg-poster-editor-20260626"
        :class="{ 'pe-active-ieg-poster-editor-20260626': isMarkActive('underline') }"
        :disabled="!editorReady"
        title="下划线"
        @click="toggleUnderline"
      >
        <u>U</u>
      </button>

      <span class="pe-toolbar-divider-ieg-poster-editor-20260626"></span>

      <label class="pe-toolbar-field-ieg-poster-editor-20260626">
        <span class="pe-toolbar-label-ieg-poster-editor-20260626">字体</span>
        <select
          v-model="selectedFontFamily"
          class="pe-toolbar-select-ieg-poster-editor-20260626"
          :disabled="!editorReady"
          @change="applyFontFamily"
        >
          <option value="Arial">Arial</option>
          <option value="SimHei">SimHei</option>
          <option value="SimSun">SimSun</option>
          <option value="KaiTi">KaiTi</option>
        </select>
      </label>

      <label class="pe-toolbar-field-ieg-poster-editor-20260626">
        <span class="pe-toolbar-label-ieg-poster-editor-20260626">字号</span>
        <select
          v-model="selectedFontSize"
          class="pe-toolbar-select-ieg-poster-editor-20260626"
          :disabled="!editorReady"
          @change="applyFontSize"
        >
          <option value="12px">12px</option>
          <option value="14px">14px</option>
          <option value="18px">18px</option>
          <option value="24px">24px</option>
          <option value="36px">36px</option>
        </select>
      </label>

      <label class="pe-toolbar-color-field-ieg-poster-editor-20260626" title="文字颜色">
        <span class="pe-toolbar-label-ieg-poster-editor-20260626">文字</span>
        <input
          v-model="selectedTextColor"
          class="pe-toolbar-color-ieg-poster-editor-20260626"
          type="color"
          :disabled="!editorReady"
          @input="applyTextColor"
          @change="applyTextColor"
        />
      </label>

      <button
        type="button"
        class="pe-toolbar-button-ieg-poster-editor-20260626 pe-highlight-button-ieg-poster-editor-20260626"
        :class="{ 'pe-active-ieg-poster-editor-20260626': isMarkActive('peHighlight') }"
        :disabled="!editorReady"
        title="黄色高亮"
        @click="applyYellowHighlight"
      >
        高亮
      </button>

      <span class="pe-toolbar-divider-ieg-poster-editor-20260626"></span>

      <button
        type="button"
        class="pe-toolbar-button-ieg-poster-editor-20260626"
        :class="{ 'pe-active-ieg-poster-editor-20260626': isTextAlignActive('left') }"
        :disabled="!editorReady"
        title="左对齐"
        @click="alignLeft"
      >
        左
      </button>

      <button
        type="button"
        class="pe-toolbar-button-ieg-poster-editor-20260626"
        :class="{ 'pe-active-ieg-poster-editor-20260626': isTextAlignActive('center') }"
        :disabled="!editorReady"
        title="居中"
        @click="alignCenter"
      >
        中
      </button>

      <button
        type="button"
        class="pe-toolbar-button-ieg-poster-editor-20260626"
        :class="{ 'pe-active-ieg-poster-editor-20260626': isTextAlignActive('right') }"
        :disabled="!editorReady"
        title="右对齐"
        @click="alignRight"
      >
        右
      </button>

      <span class="pe-toolbar-divider-ieg-poster-editor-20260626"></span>

      <button
        type="button"
        class="pe-toolbar-button-ieg-poster-editor-20260626 pe-image-button-ieg-poster-editor-20260626"
        :disabled="!editorReady"
        title="插入图片"
        @click="insertImageByPrompt"
      >
        图片
      </button>
    </div>

    <div ref="editorMountRef" class="pe-editor-body-ieg-poster-editor-20260626" @mousedown="rememberCurrentSelection">
      <EditorContent v-if="editor" :editor="editor" />
    </div>
  </div>
</template>

<script setup lang="ts">
/*
 * WARNING: This component is intentionally isolated from legacy-app-adapter.js.
 * Before using it as the only production editor, remove old global legacy editor references
 * that may register global directives, patch Tiptap commands, or inject broad .ProseMirror CSS.
 */
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { Extension, mergeAttributes, type Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import TextStyle from '@tiptap/extension-text-style'
import Color from '@tiptap/extension-color'
import Highlight from '@tiptap/extension-highlight'
import FontFamily from '@tiptap/extension-font-family'
import Image from '@tiptap/extension-image'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'

type SelectionRange = {
  from: number
  to: number
}

type PosterEditorProps = {
  modelValue?: string
}

const props = withDefaults(defineProps<PosterEditorProps>(), {
  modelValue: '',
})

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void
}>()

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    peFontSize: {
      setFontSize: (fontSize: string) => ReturnType
      unsetFontSize: () => ReturnType
    }
    peFontFamily: {
      setFontFamily: (fontFamily: string) => ReturnType
      unsetFontFamily: () => ReturnType
    }
    peColor: {
      setColor: (color: string) => ReturnType
      unsetColor: () => ReturnType
    }
    peResizedImage: {
      setImage: (options: { src: string; alt?: string; title?: string; width?: string; style?: string }) => ReturnType
    }
  }
}

const editorMountRef = ref<HTMLElement | null>(null)
const DEFAULT_EMPTY_CONTENT = '<p></p>'
const DEFAULT_IMAGE_WIDTH = '300'
const DEFAULT_IMAGE_STYLE = 'max-width:100%;height:auto;vertical-align:middle;'
const YELLOW_HIGHLIGHT = '#fff59d'

const selectedFontFamily = ref('Arial')
const selectedFontSize = ref('18px')
const selectedTextColor = ref('#111827')
const lastSelection = ref<SelectionRange | null>(null)
const pendingExternalHtml = ref<string | null>(null)
const isApplyingExternalContent = ref(false)
const lastEmittedHtml = ref('')

function cleanCssValue(value: unknown): string {
  return String(value || '')
    .replace(/[<>]/g, '')
    .replace(/!important/gi, '')
    .trim()
}

function normalizeFontSize(value: unknown): string {
  const raw = cleanCssValue(value)
  if (!raw) return '18px'
  if (/^\d+(\.\d+)?px$/.test(raw)) return raw
  if (/^\d+(\.\d+)?$/.test(raw)) return `${raw}px`
  return '18px'
}

function normalizeFontFamily(value: unknown): string {
  const raw = cleanCssValue(value)
  if (!raw) return 'Arial'
  const allowed = ['Arial', 'SimHei', 'SimSun', 'KaiTi']
  if (allowed.includes(raw)) return raw
  return raw.replace(/;/g, '').replace(/"/g, '').replace(/'/g, '')
}

function normalizeColor(value: unknown, fallback = '#111827'): string {
  const raw = cleanCssValue(value)
  if (!raw) return fallback
  if (/^#[0-9a-fA-F]{3}$/.test(raw)) return raw
  if (/^#[0-9a-fA-F]{6}$/.test(raw)) return raw
  if (/^rgba?\([^)]+\)$/.test(raw)) return raw
  if (/^hsla?\([^)]+\)$/.test(raw)) return raw
  return fallback
}

function normalizeImageWidth(value: unknown): string {
  const raw = cleanCssValue(value)
  if (!raw) return DEFAULT_IMAGE_WIDTH
  const numeric = raw.replace('px', '').trim()
  const parsed = Number(numeric)
  if (!Number.isFinite(parsed)) return DEFAULT_IMAGE_WIDTH
  const clamped = Math.max(40, Math.min(1200, parsed))
  return String(Math.round(clamped))
}

function normalizeImageStyle(value: unknown): string {
  const raw = cleanCssValue(value)
  const style = raw || DEFAULT_IMAGE_STYLE
  const hasMaxWidth = /max-width\s*:/.test(style)
  const hasHeight = /height\s*:/.test(style)
  const hasVerticalAlign = /vertical-align\s*:/.test(style)
  const parts: string[] = []
  if (style) parts.push(style.replace(/;+$/, ''))
  if (!hasMaxWidth) parts.push('max-width:100%')
  if (!hasHeight) parts.push('height:auto')
  if (!hasVerticalAlign) parts.push('vertical-align:middle')
  return `${parts.join(';')};`
}

const CustomTextStyle = TextStyle.extend({
  name: 'peTextStyle',
  addAttributes() {
    return {
      ...(this.parent?.() || {}),
      fontSize: {
        default: null,
        parseHTML: (element: HTMLElement) => element.style.fontSize ? normalizeFontSize(element.style.fontSize) : null,
        renderHTML: (attributes: Record<string, unknown>) => attributes.fontSize ? { style: `font-size:${normalizeFontSize(attributes.fontSize)} !important;` } : {},
      },
      fontFamily: {
        default: null,
        parseHTML: (element: HTMLElement) => element.style.fontFamily ? normalizeFontFamily(element.style.fontFamily) : null,
        renderHTML: (attributes: Record<string, unknown>) => attributes.fontFamily ? { style: `font-family:${normalizeFontFamily(attributes.fontFamily)} !important;` } : {},
      },
      color: {
        default: null,
        parseHTML: (element: HTMLElement) => element.style.color || null,
        renderHTML: (attributes: Record<string, unknown>) => attributes.color ? { style: `color:${normalizeColor(attributes.color)} !important;` } : {},
      },
    }
  },
  renderHTML({ HTMLAttributes }) {
    return ['span', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), 0]
  },
})

const CustomColor = Color.extend({
  name: 'peColor',
  addOptions() {
    return {
      ...(this.parent?.() || {}),
      types: ['peTextStyle'],
    }
  },
  addCommands() {
    return {
      setColor:
        (color: string) =>
        ({ chain }) => chain().setMark('peTextStyle', { color: normalizeColor(color) }).run(),
      unsetColor:
        () =>
        ({ chain }) => chain().setMark('peTextStyle', { color: null }).removeEmptyTextStyle().run(),
    }
  },
})

const CustomHighlight = Highlight.extend({
  name: 'peHighlight',
  addOptions() {
    return {
      ...(this.parent?.() || {}),
      multicolor: true,
    }
  },
  addAttributes() {
    return {
      color: {
        default: null,
        parseHTML: (element: HTMLElement) => element.getAttribute('data-color') || element.style.backgroundColor || null,
        renderHTML: (attributes: Record<string, unknown>) => {
          const color = normalizeColor(attributes.color || YELLOW_HIGHLIGHT, YELLOW_HIGHLIGHT)
          return { 'data-color': color, style: `background-color:${color} !important;` }
        },
      },
    }
  },
  renderHTML({ HTMLAttributes }) {
    return ['mark', mergeAttributes(HTMLAttributes), 0]
  },
})

const CustomFontSize = TextStyle.extend({
  name: 'peFontSize',
  addCommands() {
    return {
      setFontSize:
        (fontSize: string) =>
        ({ chain }) => chain().setMark('peTextStyle', { fontSize: normalizeFontSize(fontSize) }).run(),
      unsetFontSize:
        () =>
        ({ chain }) => chain().setMark('peTextStyle', { fontSize: null }).removeEmptyTextStyle().run(),
    }
  },
})

const CustomFontFamily = FontFamily.extend({
  name: 'peFontFamily',
  addOptions() {
    return {
      ...(this.parent?.() || {}),
      types: ['peTextStyle'],
    }
  },
  addCommands() {
    return {
      setFontFamily:
        (fontFamily: string) =>
        ({ chain }) => chain().setMark('peTextStyle', { fontFamily: normalizeFontFamily(fontFamily) }).run(),
      unsetFontFamily:
        () =>
        ({ chain }) => chain().setMark('peTextStyle', { fontFamily: null }).removeEmptyTextStyle().run(),
    }
  },
})

const ResizedImage = Image.extend({
  name: 'peResizedImage',
  inline() {
    return true
  },
  group() {
    return 'inline'
  },
  draggable: true,
  addAttributes() {
    return {
      ...(this.parent?.() || {}),
      width: {
        default: DEFAULT_IMAGE_WIDTH,
        parseHTML: (element: HTMLElement) => normalizeImageWidth(element.getAttribute('width') || element.style.width || DEFAULT_IMAGE_WIDTH),
        renderHTML: (attributes: Record<string, unknown>) => ({ width: normalizeImageWidth(attributes.width || DEFAULT_IMAGE_WIDTH) }),
      },
      style: {
        default: DEFAULT_IMAGE_STYLE,
        parseHTML: (element: HTMLElement) => normalizeImageStyle(element.getAttribute('style') || DEFAULT_IMAGE_STYLE),
        renderHTML: (attributes: Record<string, unknown>) => ({ style: normalizeImageStyle(attributes.style || DEFAULT_IMAGE_STYLE) }),
      },
    }
  },
  renderHTML({ HTMLAttributes }) {
    return ['img', mergeAttributes(HTMLAttributes, { width: normalizeImageWidth(HTMLAttributes.width || DEFAULT_IMAGE_WIDTH), style: normalizeImageStyle(HTMLAttributes.style || DEFAULT_IMAGE_STYLE) })]
  },
})

function normalizeHtmlForCompare(html: string): string {
  return String(html || '').replace(/\sdata-v-[a-zA-Z0-9-]+="[^"]*"/g, '').replace(/\s+/g, ' ').replace(/>\s+</g, '><').trim()
}

function dedupeAdjacentImagesInHtml(html: string): string {
  const source = String(html || '').trim()
  if (!source) return DEFAULT_EMPTY_CONTENT
  if (typeof window === 'undefined' || typeof window.DOMParser === 'undefined') return source
  const parser = new window.DOMParser()
  const doc = parser.parseFromString(source, 'text/html')
  Array.from(doc.body.querySelectorAll('img')).forEach((img) => {
    img.setAttribute('width', normalizeImageWidth(img.getAttribute('width') || img.style.width || DEFAULT_IMAGE_WIDTH))
    img.setAttribute('style', normalizeImageStyle(img.getAttribute('style') || DEFAULT_IMAGE_STYLE))
  })
  Array.from(doc.body.querySelectorAll('p, div, span')).forEach((parent) => {
    const children = Array.from(parent.childNodes)
    let previousImageKey = ''
    children.forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        if ((node.textContent || '').replace(/\u200B/g, '').trim()) previousImageKey = ''
        return
      }
      if (!(node instanceof HTMLElement)) {
        previousImageKey = ''
        return
      }
      const img = node.matches('img') ? node : node.querySelector(':scope > img')
      if (!img) {
        previousImageKey = ''
        return
      }
      const key = [img.getAttribute('src') || '', normalizeImageWidth(img.getAttribute('width') || img.style.width || DEFAULT_IMAGE_WIDTH)].join('|')
      if (key && key === previousImageKey) {
        node.remove()
        return
      }
      previousImageKey = key
    })
  })
  return doc.body.innerHTML.trim() || DEFAULT_EMPTY_CONTENT
}

function normalizeIncomingContent(html: string): string {
  const source = String(html || '').trim()
  if (!source) return DEFAULT_EMPTY_CONTENT
  return dedupeAdjacentImagesInHtml(source)
}

function colorToHex(value: string, fallback: string): string {
  const raw = String(value || '').trim()
  if (/^#[0-9a-fA-F]{6}$/.test(raw)) return raw
  if (/^#[0-9a-fA-F]{3}$/.test(raw)) return `#${raw.slice(1).split('').map((char) => `${char}${char}`).join('')}`
  const rgbMatch = raw.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/)
  if (rgbMatch) {
    const red = Number(rgbMatch[1]).toString(16).padStart(2, '0')
    const green = Number(rgbMatch[2]).toString(16).padStart(2, '0')
    const blue = Number(rgbMatch[3]).toString(16).padStart(2, '0')
    return `#${red}${green}${blue}`
  }
  return fallback
}

function updateToolbarState(currentEditor: Editor): void {
  const textStyleAttrs = currentEditor.getAttributes('peTextStyle')
  const highlightAttrs = currentEditor.getAttributes('peHighlight')
  if (textStyleAttrs.fontFamily) selectedFontFamily.value = normalizeFontFamily(textStyleAttrs.fontFamily)
  if (textStyleAttrs.fontSize) selectedFontSize.value = normalizeFontSize(textStyleAttrs.fontSize)
  if (textStyleAttrs.color) selectedTextColor.value = colorToHex(String(textStyleAttrs.color), selectedTextColor.value)
  if (highlightAttrs.color) colorToHex(String(highlightAttrs.color), YELLOW_HIGHLIGHT)
}

function saveSelectionFromEditor(currentEditor: Editor): void {
  const selection = currentEditor.state.selection
  lastSelection.value = { from: selection.from, to: selection.to }
}

const editor = useEditor({
  content: normalizeIncomingContent(props.modelValue),
  extensions: [
    StarterKit.configure({
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
    Underline,
    CustomTextStyle,
    CustomColor.configure({ types: ['peTextStyle'] }),
    CustomHighlight.configure({ multicolor: true }),
    CustomFontFamily.configure({ types: ['peTextStyle'] }),
    CustomFontSize,
    TextAlign.extend({ name: 'peTextAlign' }).configure({ types: ['paragraph'], alignments: ['left', 'center', 'right'], defaultAlignment: 'left' }),
    ResizedImage.configure({ inline: true, allowBase64: true, HTMLAttributes: { class: 'pe-inline-image-ieg-poster-editor-20260626' } }),
  ],
  editorProps: {
    attributes: {
      class: 'pe-prosemirror-ieg-poster-editor-20260626',
      spellcheck: 'false',
    },
  },
  onCreate: ({ editor: currentEditor }) => {
    lastEmittedHtml.value = normalizeIncomingContent(currentEditor.getHTML())
    saveSelectionFromEditor(currentEditor)
    updateToolbarState(currentEditor)
  },
  onUpdate: ({ editor: currentEditor }) => {
    if (isApplyingExternalContent.value) return
    saveSelectionFromEditor(currentEditor)
    updateToolbarState(currentEditor)
    const html = dedupeAdjacentImagesInHtml(currentEditor.getHTML())
    lastEmittedHtml.value = html
    emit('update:modelValue', html)
  },
  onSelectionUpdate: ({ editor: currentEditor }) => {
    saveSelectionFromEditor(currentEditor)
    updateToolbarState(currentEditor)
  },
  onFocus: ({ editor: currentEditor }) => {
    saveSelectionFromEditor(currentEditor)
    updateToolbarState(currentEditor)
  },
  onBlur: () => {
    if (pendingExternalHtml.value !== null) {
      const value = pendingExternalHtml.value
      pendingExternalHtml.value = null
      applyExternalContent(value)
    }
  },
})

const editorReady = computed(() => Boolean(editor.value && !editor.value.isDestroyed))

function getEditor(): Editor | null {
  if (!editor.value || editor.value.isDestroyed) return null
  return editor.value
}

function chainWithSavedSelection() {
  const currentEditor = getEditor()
  if (!currentEditor) return null
  const chain = currentEditor.chain().focus()
  if (lastSelection.value) {
    const docSize = currentEditor.state.doc.content.size
    const from = Math.max(0, Math.min(docSize, lastSelection.value.from))
    const to = Math.max(from, Math.min(docSize, lastSelection.value.to))
    chain.setTextSelection({ from, to })
  }
  return chain
}

function rememberCurrentSelection(): void {
  const currentEditor = getEditor()
  if (!currentEditor) return
  saveSelectionFromEditor(currentEditor)
}

function isMarkActive(markName: string): boolean {
  const currentEditor = getEditor()
  return currentEditor ? currentEditor.isActive(markName) : false
}

function isTextAlignActive(align: 'left' | 'center' | 'right'): boolean {
  const currentEditor = getEditor()
  return currentEditor ? currentEditor.isActive({ textAlign: align }) : false
}

function toggleBold(): void {
  const chain = chainWithSavedSelection()
  if (!chain) return
  chain.toggleBold().run()
}

function toggleItalic(): void {
  const chain = chainWithSavedSelection()
  if (!chain) return
  chain.toggleItalic().run()
}

function toggleUnderline(): void {
  const chain = chainWithSavedSelection()
  if (!chain) return
  chain.toggleUnderline().run()
}

function applyFontFamily(): void {
  const chain = chainWithSavedSelection()
  if (!chain) return
  chain.setFontFamily(normalizeFontFamily(selectedFontFamily.value)).run()
}

function applyFontSize(): void {
  const chain = chainWithSavedSelection()
  if (!chain) return
  chain.setFontSize(normalizeFontSize(selectedFontSize.value)).run()
}

function applyTextColor(): void {
  const chain = chainWithSavedSelection()
  if (!chain) return
  chain.setColor(normalizeColor(selectedTextColor.value)).run()
}

function applyYellowHighlight(): void {
  const chain = chainWithSavedSelection()
  if (!chain) return
  chain.setHighlight({ color: YELLOW_HIGHLIGHT }).run()
}

function alignLeft(): void {
  const chain = chainWithSavedSelection()
  if (!chain) return
  chain.setTextAlign('left').run()
}

function alignCenter(): void {
  const chain = chainWithSavedSelection()
  if (!chain) return
  chain.setTextAlign('center').run()
}

function alignRight(): void {
  const chain = chainWithSavedSelection()
  if (!chain) return
  chain.setTextAlign('right').run()
}

function insertImageByPrompt(): void {
  const currentEditor = getEditor()
  if (!currentEditor) return
  const url = window.prompt('请输入图片 URL')
  if (!url) return
  const cleanUrl = url.trim()
  if (!cleanUrl) return
  if (lastSelection.value) {
    const docSize = currentEditor.state.doc.content.size
    const from = Math.max(0, Math.min(docSize, lastSelection.value.from))
    const to = Math.max(from, Math.min(docSize, lastSelection.value.to))
    currentEditor.commands.setTextSelection({ from, to })
  }
  currentEditor.chain().focus().setImage({ src: cleanUrl, width: DEFAULT_IMAGE_WIDTH, style: DEFAULT_IMAGE_STYLE }).insertContent(' ').run()
}

function applyExternalContent(value: string): void {
  const currentEditor = getEditor()
  if (!currentEditor) return
  const normalizedValue = normalizeIncomingContent(value)
  const currentHtml = normalizeIncomingContent(currentEditor.getHTML())
  if (normalizeHtmlForCompare(normalizedValue) === normalizeHtmlForCompare(currentHtml)) return
  isApplyingExternalContent.value = true
  try {
    currentEditor.commands.setContent(normalizedValue, false)
    lastEmittedHtml.value = normalizedValue
  } finally {
    nextTick(() => {
      isApplyingExternalContent.value = false
    })
  }
}

watch(
  () => props.modelValue,
  (newValue) => {
    const currentEditor = getEditor()
    if (!currentEditor) return
    const nextHtml = normalizeIncomingContent(newValue || '')
    const currentHtml = normalizeIncomingContent(currentEditor.getHTML())
    if (normalizeHtmlForCompare(nextHtml) === normalizeHtmlForCompare(currentHtml)) return
    if (normalizeHtmlForCompare(nextHtml) === normalizeHtmlForCompare(lastEmittedHtml.value)) return
    if (currentEditor.isFocused) {
      pendingExternalHtml.value = nextHtml
      return
    }
    applyExternalContent(nextHtml)
  },
)

onBeforeUnmount(() => {
  if (editor.value && !editor.value.isDestroyed) {
    editor.value.destroy()
  }
  editor.value = null
})
</script>

<style scoped>
.pe-root-ieg-poster-editor-20260626 {
  width: 100%;
  border: 1px solid #d8e3f8;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  overflow: hidden;
  isolation: isolate;
  contain: layout style;
}

.pe-toolbar-ieg-poster-editor-20260626 {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f8fbff;
  border-bottom: 1px solid #d8e3f8;
}

.pe-toolbar-button-ieg-poster-editor-20260626 {
  height: 34px;
  min-width: 34px;
  padding: 0 10px;
  border: 1px solid #cbd8ee;
  border-radius: 8px;
  background: #ffffff;
  color: #172033;
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}

.pe-toolbar-button-ieg-poster-editor-20260626:hover:not(:disabled) {
  background: #eef5ff;
  border-color: #8bb7ff;
  color: #1d4ed8;
}

.pe-toolbar-button-ieg-poster-editor-20260626.pe-active-ieg-poster-editor-20260626 {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.22);
}

.pe-toolbar-button-ieg-poster-editor-20260626:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.pe-highlight-button-ieg-poster-editor-20260626 {
  background: #fff9c4;
  border-color: #facc15;
  color: #713f12;
}

.pe-image-button-ieg-poster-editor-20260626 {
  min-width: 56px;
}

.pe-toolbar-divider-ieg-poster-editor-20260626 {
  width: 1px;
  height: 28px;
  background: #d8e3f8;
  margin: 0 2px;
}

.pe-toolbar-field-ieg-poster-editor-20260626,
.pe-toolbar-color-field-ieg-poster-editor-20260626 {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
}

.pe-toolbar-label-ieg-poster-editor-20260626 {
  font-size: 12px;
  font-weight: 700;
  color: #475569;
  white-space: nowrap;
}

.pe-toolbar-select-ieg-poster-editor-20260626 {
  height: 34px;
  min-width: 92px;
  padding: 0 8px;
  border: 1px solid #cbd8ee;
  border-radius: 8px;
  background: #ffffff;
  color: #172033;
  font-size: 13px;
  outline: none;
}

.pe-toolbar-select-ieg-poster-editor-20260626:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.pe-toolbar-color-ieg-poster-editor-20260626 {
  width: 34px;
  height: 34px;
  padding: 2px;
  border: 1px solid #cbd8ee;
  border-radius: 8px;
  background: #ffffff;
  cursor: pointer;
}

.pe-toolbar-color-ieg-poster-editor-20260626:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.pe-editor-body-ieg-poster-editor-20260626 {
  min-height: 220px;
  padding: 16px;
  background: #ffffff;
}
</style>

<style scoped>
.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror) {
  min-height: 190px !important;
  padding: 14px 16px !important;
  border: 1px solid #d7e2f7 !important;
  border-radius: 10px !important;
  background: #ffffff !important;
  color: #111827 !important;
  font-size: 18px !important;
  line-height: 1.65 !important;
  outline: none !important;
  white-space: pre-wrap !important;
  word-break: normal !important;
  overflow-wrap: anywhere !important;
}

.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror:focus) {
  border-color: #2563eb !important;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
}

.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror p) {
  margin: 0 0 0.75em 0 !important;
}

.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror p:last-child) {
  margin-bottom: 0 !important;
}

.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror strong) {
  font-weight: bold !important;
}

.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror em) {
  font-style: italic !important;
}

.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror u) {
  text-decoration: underline !important;
}

.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror span) {
  display: inline !important;
}

.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror img) {
  display: inline-block !important;
  max-width: 100% !important;
  height: auto !important;
  vertical-align: middle !important;
  border-radius: 8px !important;
  margin: 4px 4px !important;
}

.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror img.ProseMirror-selectednode) {
  outline: 3px solid #2563eb !important;
  outline-offset: 3px !important;
}

.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror mark) {
  padding: 0 0.08em !important;
  border-radius: 3px !important;
}

.pe-root-ieg-poster-editor-20260626 :deep(.pe-editor-body-ieg-poster-editor-20260626 .ProseMirror .pe-inline-image-ieg-poster-editor-20260626) {
  display: inline-block !important;
  max-width: 100% !important;
  height: auto !important;
  vertical-align: middle !important;
}
</style>
