import { Projects, Covers, FunctionProjects, savePosterArtifact, artifactFileUrl } from "./api.js";
import { destroyEditors, mountEditor, runEditorCommand, insertImagesIntoActiveEditor, getActiveEditor } from "./editor.js";

const FUNCTION_ID = "poster_brief";
const root = document.getElementById("app");
const state = {
  version: "",
  view: "projects",
  loading: false,
  saving: false,
  error: "",
  toast: "",
  projects: [],
  stats: {},
  currentProject: null,
  posterItems: [],
  currentPoster: null,
  modules: [],
  previewUrl: "",
  lastArtifact: null,
  expanded: new Set(),
  createProjectOpen: false,
  createPosterOpen: false,
  projectDraft: { name: "", owner: "", theme_color: "#2563EB", project_type: "A" },
  posterDraft: { name: "", project_type: "A", scene: "S1" },
};

const TYPE_OPTIONS = [
  { id: "A", title: "培养项目型", hint: "长期培养、训练营、体系化项目", color: "#2563EB" },
  { id: "B", title: "活动招募型", hint: "单场活动、沙龙、开放报名", color: "#7C3AED" },
  { id: "C", title: "成果展示型", hint: "结项汇报、优秀作品、学员表彰", color: "#0891B2" },
];
const SCENE_OPTIONS = [
  { id: "S1", title: "开班/招募海报", hint: "报名要求、培养目标、时间地点" },
  { id: "S2", title: "课程介绍海报", hint: "课程亮点、讲师、收益" },
  { id: "S3", title: "专题训练海报", hint: "主题拆解、课程安排、CTA" },
  { id: "S4", title: "讲师/嘉宾海报", hint: "讲师阵容、经历、方向" },
  { id: "S5", title: "反馈复盘海报", hint: "评分、学员之声、成果" },
  { id: "S6b", title: "综合长图海报", hint: "多模块混合展示" },
];

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[ch]));
}

function setToast(message) {
  state.toast = message;
  render();
  clearTimeout(setToast.timer);
  setToast.timer = setTimeout(() => { state.toast = ""; render(); }, 2200);
}

function setError(err) {
  state.error = err ? String(err.message || err) : "";
  render();
}

function typeLabel(id) {
  return TYPE_OPTIONS.find(x => x.id === id)?.title || id || "未选择";
}

function sceneLabel(id) {
  return SCENE_OPTIONS.find(x => x.id === id)?.title || id || "未选择";
}

function statusLabel(status) {
  return { in_progress: "进行中", pending: "待启动", archived: "已归档" }[status] || "进行中";
}

function moduleTitle(module) {
  return module?.module_config?.module_title || module?.title || module?.name || module?.module_id || "未命名模块";
}

function defaultModules(scene = "S1") {
  const base = [
    ["M1", "项目导语", "请填写项目背景、培养对象和核心价值。"],
    ["M2", "培养目标/报名要求", "请填写培养目标、报名资格、适合人群。"],
    ["M5", "时间地点", "请填写时间、地点、形式，也可以插入表格截图或图片。"],
    ["M13", "讲师/嘉宾阵容", "请填写讲师姓名、头衔、经历，也可以插入头像图片。"],
    ["M24", "报名方式/CTA", "请填写报名入口、截止时间和联系人。"],
  ];
  if (scene === "S5") base.splice(2, 0, ["M16", "课程反馈", "请填写评分、学员感受、优秀作品或成果图。"]);
  if (scene === "S6b") base.splice(3, 0, ["M18", "成果展示", "请填写作品、项目、截图或图文说明。"]);
  return base.map(([id, title, content], index) => ({
    module_id: id,
    id: `${id}_${Date.now()}_${index}`,
    type: "spec_text_panel",
    required: index < 3,
    collapsed: index > 0,
    module_config: {
      module_title: title,
      show_title: true,
      content,
      content_html: `<p>${esc(content)}</p>`,
      fill: "#1f3f7b",
      outline: "#60a5fa",
      text_color: "#eef4ff",
      subsections: [],
    },
  }));
}

function strategyFromPoster(item) {
  return item?.poster_strategy && typeof item.poster_strategy === "object" ? item.poster_strategy : {};
}

function modulesFromPoster(item) {
  const strategy = strategyFromPoster(item);
  const modules = Array.isArray(strategy.module_plan) ? strategy.module_plan : [];
  return modules.length ? modules.map((m, i) => normalizeModule(m, i)) : defaultModules(item?.scene || state.currentProject?.project_type || "S1");
}

function normalizeModule(module, index) {
  const cfg = module.module_config || {};
  const id = module.id || `${module.module_id || "M"}_${index}_${Date.now()}`;
  return {
    ...module,
    id,
    module_id: module.module_id || module.code || `M${index + 1}`,
    type: module.type || "spec_text_panel",
    collapsed: module.collapsed !== false,
    module_config: {
      module_title: cfg.module_title || module.title || module.name || `模块 ${index + 1}`,
      show_title: cfg.show_title !== false,
      content: cfg.content || "",
      content_html: cfg.content_html || (cfg.content ? `<p>${esc(cfg.content)}</p>` : "<p></p>"),
      content_editor_json: cfg.content_editor_json || cfg.editor_json || null,
      fill: cfg.fill || "#1f3f7b",
      outline: cfg.outline || "#60a5fa",
      text_color: cfg.text_color || "#eef4ff",
      subsections: Array.isArray(cfg.subsections) ? cfg.subsections.map((s, si) => ({
        id: s.id || `sub_${id}_${si}_${Date.now()}`,
        title: s.title || "子模块小标题",
        title_html: s.title_html || `<p>${esc(s.title || "子模块小标题")}</p>`,
        title_editor_json: s.title_editor_json || null,
        text: s.text || "",
        text_html: s.text_html || (s.text ? `<p>${esc(s.text)}</p>` : "<p></p>"),
        text_editor_json: s.text_editor_json || null,
      })) : [],
    },
  };
}

async function loadProjects() {
  state.loading = true;
  setError("");
  try {
    const data = await Projects.list();
    state.projects = data.projects || [];
    state.stats = data.stats || {};
  } catch (err) { setError(err); }
  state.loading = false;
  render();
}

async function openProject(pid) {
  destroyEditors();
  state.loading = true;
  setError("");
  try {
    state.currentProject = await Projects.get(pid);
    state.view = "detail";
  } catch (err) { setError(err); }
  state.loading = false;
  render();
}

async function openPoster(pid) {
  destroyEditors();
  state.loading = true;
  setError("");
  try {
    state.currentProject = state.currentProject?.id === pid ? state.currentProject : await Projects.get(pid);
    const data = await FunctionProjects.list(pid, FUNCTION_ID);
    state.posterItems = data.items || [];
    state.currentPoster = state.posterItems[0] || null;
    state.modules = state.currentPoster ? modulesFromPoster(state.currentPoster) : [];
    state.expanded = new Set(state.modules.slice(0, 1).map(m => m.id));
    state.previewUrl = "";
    state.lastArtifact = null;
    state.view = "poster";
  } catch (err) { setError(err); }
  state.loading = false;
  render();
}

async function createProject() {
  const draft = state.projectDraft;
  if (!draft.name.trim()) return setToast("请先填写项目名称");
  state.saving = true;
  render();
  try {
    const cover = await Covers.generate({ name: draft.name, theme_color: draft.theme_color, project_type: draft.project_type });
    const created = await Projects.create({
      name: draft.name,
      description: "",
      project_type: draft.project_type,
      status: "in_progress",
      cover_id: cover.id,
      owner: { name: draft.owner || "未指派" },
    });
    state.createProjectOpen = false;
    state.projectDraft = { name: "", owner: "", theme_color: "#2563EB", project_type: "A" };
    await openProject(created.id);
  } catch (err) { setError(err); }
  state.saving = false;
  render();
}

async function createPosterProject() {
  if (!state.currentProject) return;
  const draft = state.posterDraft;
  if (!draft.name.trim()) return setToast("请填写海报子项目名称");
  state.saving = true;
  render();
  try {
    const payload = {
      name: draft.name,
      project_type: draft.project_type,
      scene: draft.scene,
      poster_strategy: {
        project_type: { id: draft.project_type, label: typeLabel(draft.project_type) },
        scene: { id: draft.scene, label: sceneLabel(draft.scene) },
        module_plan: defaultModules(draft.scene),
      },
    };
    const data = await FunctionProjects.create(state.currentProject.id, FUNCTION_ID, payload);
    state.createPosterOpen = false;
    const list = await FunctionProjects.list(state.currentProject.id, FUNCTION_ID);
    state.posterItems = list.items || [];
    state.currentPoster = (data.items || [])[0] || state.posterItems[0] || null;
    state.modules = state.currentPoster ? modulesFromPoster(state.currentPoster) : [];
    state.expanded = new Set(state.modules.slice(0, 1).map(m => m.id));
    setToast("海报子项目已创建");
  } catch (err) { setError(err); }
  state.saving = false;
  render();
}

async function selectPoster(id) {
  await savePoster(false);
  const item = state.posterItems.find(x => x.id === id);
  state.currentPoster = item || null;
  state.modules = item ? modulesFromPoster(item) : [];
  state.previewUrl = "";
  state.lastArtifact = null;
  state.expanded = new Set(state.modules.slice(0, 1).map(m => m.id));
  render();
}

function addModule() {
  const idx = state.modules.length + 1;
  const mod = normalizeModule({ module_id: `M${idx}`, module_config: { module_title: `新增模块 ${idx}`, content: "" } }, idx);
  mod.collapsed = false;
  state.modules.push(mod);
  state.expanded.add(mod.id);
  render();
}

function removeModule(id) {
  state.modules = state.modules.filter(m => m.id !== id);
  state.expanded.delete(id);
  render();
}

function moveModule(id, delta) {
  const i = state.modules.findIndex(m => m.id === id);
  const j = i + delta;
  if (i < 0 || j < 0 || j >= state.modules.length) return;
  const [item] = state.modules.splice(i, 1);
  state.modules.splice(j, 0, item);
  render();
}

function addSubmodule(moduleId) {
  const mod = state.modules.find(m => m.id === moduleId);
  if (!mod) return;
  mod.module_config.subsections.push({
    id: `sub_${Date.now()}_${Math.random().toString(16).slice(2)}`,
    title: "子模块小标题",
    title_html: "<p>子模块小标题</p>",
    text: "",
    text_html: "<p></p>",
  });
  state.expanded.add(moduleId);
  render();
}

function removeSubmodule(moduleId, subId) {
  const mod = state.modules.find(m => m.id === moduleId);
  if (!mod) return;
  mod.module_config.subsections = mod.module_config.subsections.filter(s => s.id !== subId);
  render();
}

function buildBrief() {
  const theme = TYPE_OPTIONS.find(x => x.id === (state.currentPoster?.project_type || state.currentProject?.project_type))?.color || state.currentProject?.cover_tone || "#2563EB";
  const sections = [
    {
      type: "hero_strip",
      height: 420,
      title_card: {
        style: "gradient",
        lines: [state.currentProject?.name || "未命名项目"],
        colors: ["#FFFFFF", "#DBEAFE"],
        font_size: 92,
        safe_zone: "center",
      },
    },
    {
      type: "subtitle_text",
      text: state.currentPoster?.name || "海报子项目",
      font_size: 34,
      text_color: "#EEF4FF",
    },
  ];
  for (const mod of state.modules) {
    const cfg = mod.module_config || {};
    const base = {
      type: "spec_text_panel",
      title: cfg.module_title || mod.module_id,
      module_title: cfg.module_title || mod.module_id,
      show_title: cfg.show_title !== false,
      content: cfg.content || "",
      content_html: cfg.content_html || "<p></p>",
      editor_json: cfg.content_editor_json || cfg.editor_json || null,
      fill: cfg.fill || "#1F3F7B",
      outline: cfg.outline || theme,
      text_color: cfg.text_color || "#EEF4FF",
      accent_color: theme,
      font_size: 30,
      image_fit: "contain",
    };
    sections.push(base);
    for (const sub of cfg.subsections || []) {
      sections.push({
        type: "spec_text_panel",
        title: sub.title || "子模块",
        module_title: sub.title || "子模块",
        content: sub.text || "",
        content_html: sub.text_html || "<p></p>",
        editor_json: sub.text_editor_json || null,
        fill: cfg.fill || "#1F3F7B",
        outline: cfg.outline || theme,
        text_color: cfg.text_color || "#EEF4FF",
        accent_color: theme,
        font_size: 28,
        image_fit: "contain",
      });
    }
  }
  return {
    scene: state.currentPoster?.scene || "S1",
    logo_position: "none",
    canvas: {
      width: 1440,
      bg_colors: [theme, "#0F172A"],
      palette_strategy: "named:modern_blue",
      pattern: "none",
      glow: false,
    },
    decorations: { density: "none" },
    sections,
  };
}

async function savePoster(showMessage = true) {
  if (!state.currentProject || !state.currentPoster) return;
  state.saving = true;
  renderToolbarOnly();
  try {
    const strategy = strategyFromPoster(state.currentPoster);
    const payload = {
      name: state.currentPoster.name,
      project_type: state.currentPoster.project_type || state.currentProject.project_type || "A",
      scene: state.currentPoster.scene || "S1",
      poster_strategy: {
        ...strategy,
        project_type: { id: state.currentPoster.project_type || state.currentProject.project_type || "A", label: typeLabel(state.currentPoster.project_type || state.currentProject.project_type || "A") },
        scene: { id: state.currentPoster.scene || "S1", label: sceneLabel(state.currentPoster.scene || "S1") },
        module_plan: state.modules,
        brief: buildBrief(),
      },
    };
    const updated = await FunctionProjects.update(state.currentProject.id, FUNCTION_ID, state.currentPoster.id, payload);
    state.currentPoster = { ...state.currentPoster, ...updated, poster_strategy: payload.poster_strategy };
    state.posterItems = state.posterItems.map(x => x.id === state.currentPoster.id ? state.currentPoster : x);
    if (showMessage) setToast("已保存当前编辑");
  } catch (err) { setError(err); }
  state.saving = false;
  renderToolbarOnly();
}

async function generatePreview() {
  if (!state.currentProject || !state.currentPoster) return;
  await savePoster(false);
  state.saving = true;
  state.previewUrl = "";
  render();
  try {
    const brief = buildBrief();
    const data = await savePosterArtifact(state.currentProject.id, brief);
    state.lastArtifact = data.artifact;
    state.previewUrl = artifactFileUrl(state.currentProject.id, data.artifact.id, "poster.png") + `&t=${Date.now()}`;
    setToast("海报预览已生成");
  } catch (err) { setError(err); }
  state.saving = false;
  render();
}

function renderToolbarOnly() {
  const node = document.querySelector(".modern-save-state");
  if (node) node.textContent = state.saving ? "保存中…" : "已就绪";
}

function render() {
  destroyEditors();
  if (!root) return;
  root.innerHTML = `
    <div class="modern-root">
      <header class="modern-topbar">
        <button class="modern-brand" data-action="go-projects"><span>IEG</span><b>人才发展项目管理 AI 工作台</b></button>
        <div class="modern-top-actions">
          <span class="modern-pill modern-save-state">${state.saving ? "处理中…" : "已就绪"}</span>
          <button class="modern-icon" data-action="open-create-project">＋ 新建项目</button>
        </div>
      </header>
      ${state.toast ? `<div class="modern-toast">${esc(state.toast)}</div>` : ""}
      ${state.error ? `<div class="modern-error"><b>错误</b>${esc(state.error)}</div>` : ""}
      ${state.view === "projects" ? renderProjectList() : ""}
      ${state.view === "detail" ? renderProjectDetail() : ""}
      ${state.view === "poster" ? renderPosterPage() : ""}
      ${state.createProjectOpen ? renderCreateProjectModal() : ""}
      ${state.createPosterOpen ? renderCreatePosterModal() : ""}
      <footer class="modern-footer">如有疑问，请联系 dorrainzeng(曾德蕴)<br>原型由 <span>Codex Claude</span> 通过自然语言生成</footer>
    </div>`;
  bindEvents();
  if (state.view === "poster") setTimeout(mountCurrentEditors, 0);
}

function renderProjectList() {
  return `
    <main class="modern-page">
      <section class="modern-hero-video"><div><h1>创意不设限 · 效率不加班</h1><p>从项目管理到海报生成，一套干净的新前端正在接管工作台。</p></div></section>
      <section class="modern-ai-box">
        <div class="modern-ai-input"><span>AI</span><input placeholder="说出你要创建或进入的项目，例如：创建特效训练营项目，负责人李虹瑾" /><button>↑</button></div>
      </section>
      <section class="modern-section-head"><h2>项目管理</h2><button data-action="open-create-project">新建项目</button></section>
      <section class="modern-project-grid">
        ${state.projects.map(p => `
          <article class="modern-project-card" data-action="open-project" data-id="${esc(p.id)}">
            <div class="modern-project-cover" style="background-image:url('${esc(p.cover_url || "")}'"><span>${esc(p.name || "未命名项目")}</span></div>
            <div class="modern-project-body"><h3>${esc(p.name)}</h3><p>${esc(statusLabel(p.status))} · ${esc(p.owner?.name || "未指派")}</p></div>
          </article>`).join("")}
        <button class="modern-project-card modern-new-card" data-action="open-create-project">＋<b>新建项目</b></button>
      </section>
    </main>`;
}

function renderProjectDetail() {
  const p = state.currentProject;
  if (!p) return "";
  return `
    <main class="modern-page">
      <button class="modern-back" data-action="go-projects">← 返回项目列表</button>
      <section class="modern-project-hero" style="--cover:url('${esc(p.cover_url || "")}')">
        <div><h1>${esc(p.name)}</h1><p>${esc(p.owner?.name || "未指派")} · ${esc(typeLabel(p.project_type))} · ${esc(statusLabel(p.status))}</p></div>
      </section>
      <section class="modern-function-grid">
        <button class="modern-function-card poster" data-action="open-poster" data-id="${esc(p.id)}"><span>海报</span><b>文案 / 生图</b></button>
        <button class="modern-function-card interview"><span>访谈</span><b>提纲 / 纪要</b></button>
        <button class="modern-function-card ppt"><span>PPT</span><b>大纲 / 制作</b></button>
        <button class="modern-function-card report"><span>研究报告</span><b>资料 / 成文</b></button>
      </section>
    </main>`;
}

function renderPosterPage() {
  return `
    <main class="modern-poster-page">
      <div class="modern-fixed-back"><button data-action="back-detail">← 返回项目概览</button><button data-action="save-poster">保存当前编辑</button><button data-action="generate-preview">生成海报预览</button></div>
      <aside class="modern-preview-pane">
        <h2>海报预览</h2>
        <div class="modern-preview-box">${state.previewUrl ? `<img src="${esc(state.previewUrl)}" />` : `<div class="modern-empty-preview">点击“生成海报预览”后显示</div>`}</div>
        <div class="modern-ai-mini"><b>AI 助手</b><textarea placeholder="这里后续接项目内 AI 助手，不再和别的项目串记忆。"></textarea></div>
      </aside>
      <section class="modern-editor-pane">
        <div class="modern-poster-head"><div><h1>${esc(state.currentProject?.name || "项目")} · 海报</h1><p>项目所含海报子项目</p></div><button data-action="open-create-poster">新建海报子项目</button></div>
        <div class="modern-subproject-row">
          ${state.posterItems.map(item => `<button class="${state.currentPoster?.id === item.id ? "active" : ""}" data-action="select-poster" data-id="${esc(item.id)}">${esc(item.name)}<small>${esc(sceneLabel(item.scene))}</small></button>`).join("")}
        </div>
        ${state.currentPoster ? renderModuleEditor() : `<div class="modern-empty-card"><h2>还没有海报子项目</h2><p>点击“新建海报子项目”，选择类型和场景后开始模块编排。</p></div>`}
      </section>
    </main>`;
}

function renderModuleEditor() {
  return `
    <div class="modern-toolbar">
      <select data-cmd="fontFamily"><option value="Arial">Arial</option><option value="SimHei">默认中文黑体</option><option value="SimSun">宋体</option><option value="KaiTi">楷体</option></select>
      <select data-cmd="fontSize"><option value="12px">12</option><option value="14px">14</option><option value="18px">18</option><option value="24px">24</option><option value="32px">32</option><option value="36px">36</option></select>
      <input type="color" data-cmd="color" value="#111827" title="文字颜色" />
      <button data-cmd="highlight">高亮</button><button data-cmd="bold">B</button><button data-cmd="italic">I</button><button data-cmd="underline">U</button>
      <button data-cmd="align" data-value="left">左</button><button data-cmd="align" data-value="center">中</button><button data-cmd="align" data-value="right">右</button>
      <label class="modern-upload-btn">图片<input type="file" multiple accept="image/*" data-action="upload-editor-image" /></label>
    </div>
    <div class="modern-module-actions"><button data-action="add-module">＋ 新增模块</button><button data-action="generate-preview">生成海报预览</button></div>
    <div class="modern-modules">
      ${state.modules.map((m, i) => renderModule(m, i)).join("")}
    </div>`;
}

function renderModule(m, i) {
  const cfg = m.module_config || {};
  const open = state.expanded.has(m.id);
  return `
    <article class="modern-module-card" data-module-id="${esc(m.id)}">
      <header><button data-action="toggle-module" data-id="${esc(m.id)}">${open ? "收起" : "展开"}</button><h3>${esc(cfg.module_title || m.module_id)} <span>${esc(m.module_id)}</span></h3><div><button data-action="move-module" data-id="${esc(m.id)}" data-delta="-1">↑</button><button data-action="move-module" data-id="${esc(m.id)}" data-delta="1">↓</button><button data-action="remove-module" data-id="${esc(m.id)}">删除</button></div></header>
      ${open ? `<div class="modern-module-inner">
        <label>模块标题<input data-bind="module-title" data-id="${esc(m.id)}" value="${esc(cfg.module_title)}" /></label>
        <label class="modern-check"><input type="checkbox" data-bind="show-title" data-id="${esc(m.id)}" ${cfg.show_title !== false ? "checked" : ""} />显示模块标题</label>
        <div class="modern-appearance"><label>底色<input type="color" data-bind="fill" data-id="${esc(m.id)}" value="${esc(cfg.fill || "#1f3f7b")}" /></label><label>边线<input type="color" data-bind="outline" data-id="${esc(m.id)}" value="${esc(cfg.outline || "#60a5fa")}" /></label><label>文字色<input type="color" data-bind="text-color" data-id="${esc(m.id)}" value="${esc(cfg.text_color || "#eef4ff")}" /></label></div>
        <h4>模块输入内容</h4><div class="modern-rich-editor" data-editor="${esc(m.id)}:content"></div>
        <div class="modern-submodules">${(cfg.subsections || []).map(s => renderSubmodule(m, s)).join("")}</div>
        <button data-action="add-submodule" data-id="${esc(m.id)}">＋ 添加文字子模块</button>
      </div>` : ""}
    </article>`;
}

function renderSubmodule(m, s) {
  return `<div class="modern-submodule" data-sub-id="${esc(s.id)}"><button data-action="remove-submodule" data-module-id="${esc(m.id)}" data-sub-id="${esc(s.id)}">删除子模块</button><h4>子模块小标题</h4><div class="modern-rich-editor compact" data-editor="${esc(m.id)}:${esc(s.id)}:title"></div><h4>子模块正文</h4><div class="modern-rich-editor" data-editor="${esc(m.id)}:${esc(s.id)}:text"></div></div>`;
}

function renderCreateProjectModal() {
  return `<div class="modern-modal"><div class="modern-dialog"><h2>新建项目</h2><label>项目名称<input data-draft="project-name" value="${esc(state.projectDraft.name)}" /></label><label>负责人<input data-draft="project-owner" value="${esc(state.projectDraft.owner)}" /></label><label>主题色<input type="color" data-draft="project-color" value="${esc(state.projectDraft.theme_color)}" /></label><div class="modern-type-grid">${TYPE_OPTIONS.map(t => `<button class="${state.projectDraft.project_type === t.id ? "active" : ""}" data-action="pick-project-type" data-id="${t.id}" style="--tone:${t.color}"><b>${t.id}</b><span>${t.title}</span><small>${t.hint}</small></button>`).join("")}</div><footer><button data-action="close-create-project">取消</button><button data-action="create-project">创建并进入</button></footer></div></div>`;
}

function renderCreatePosterModal() {
  return `<div class="modern-modal"><div class="modern-dialog wide"><h2>新建海报子项目</h2><label>海报子项目名称<input data-draft="poster-name" value="${esc(state.posterDraft.name)}" /></label><h3>项目类型</h3><div class="modern-type-grid">${TYPE_OPTIONS.map(t => `<button class="${state.posterDraft.project_type === t.id ? "active" : ""}" data-action="pick-poster-type" data-id="${t.id}" style="--tone:${t.color}"><b>${t.id}</b><span>${t.title}</span><small>${t.hint}</small></button>`).join("")}</div><h3>海报场景</h3><div class="modern-scene-grid">${SCENE_OPTIONS.map(s => `<button class="${state.posterDraft.scene === s.id ? "active" : ""}" data-action="pick-poster-scene" data-id="${s.id}"><b>${s.id}</b><span>${s.title}</span><small>${s.hint}</small></button>`).join("")}</div><footer><button data-action="close-create-poster">取消</button><button data-action="create-poster">创建海报子项目</button></footer></div></div>`;
}

function bindEvents() {
  root.querySelectorAll("[data-action]").forEach(el => {
    el.addEventListener("click", async (ev) => {
      const action = el.dataset.action;
      if (action === "open-project") return openProject(el.dataset.id);
      if (action === "go-projects") { destroyEditors(); state.view = "projects"; await loadProjects(); return; }
      if (action === "back-detail") { destroyEditors(); state.view = "detail"; return render(); }
      if (action === "open-create-project") { state.createProjectOpen = true; return render(); }
      if (action === "close-create-project") { state.createProjectOpen = false; return render(); }
      if (action === "create-project") return createProject();
      if (action === "pick-project-type") { state.projectDraft.project_type = el.dataset.id; return render(); }
      if (action === "open-poster") return openPoster(el.dataset.id);
      if (action === "open-create-poster") { state.posterDraft = { name: `${state.currentProject?.name || "项目"}海报`, project_type: state.currentProject?.project_type || "A", scene: "S1" }; state.createPosterOpen = true; return render(); }
      if (action === "close-create-poster") { state.createPosterOpen = false; return render(); }
      if (action === "pick-poster-type") { state.posterDraft.project_type = el.dataset.id; return render(); }
      if (action === "pick-poster-scene") { state.posterDraft.scene = el.dataset.id; return render(); }
      if (action === "create-poster") return createPosterProject();
      if (action === "select-poster") return selectPoster(el.dataset.id);
      if (action === "toggle-module") { state.expanded.has(el.dataset.id) ? state.expanded.delete(el.dataset.id) : state.expanded.add(el.dataset.id); return render(); }
      if (action === "add-module") return addModule();
      if (action === "remove-module") return removeModule(el.dataset.id);
      if (action === "move-module") return moveModule(el.dataset.id, Number(el.dataset.delta || 0));
      if (action === "add-submodule") return addSubmodule(el.dataset.id);
      if (action === "remove-submodule") return removeSubmodule(el.dataset.moduleId, el.dataset.subId);
      if (action === "save-poster") return savePoster(true);
      if (action === "generate-preview") return generatePreview();
    });
  });
  root.querySelectorAll("[data-draft]").forEach(el => el.addEventListener("input", () => {
    const k = el.dataset.draft;
    if (k === "project-name") state.projectDraft.name = el.value;
    if (k === "project-owner") state.projectDraft.owner = el.value;
    if (k === "project-color") state.projectDraft.theme_color = el.value;
    if (k === "poster-name") state.posterDraft.name = el.value;
  }));
  root.querySelectorAll("[data-bind]").forEach(el => el.addEventListener("input", () => {
    const mod = state.modules.find(m => m.id === el.dataset.id);
    if (!mod) return;
    if (el.dataset.bind === "module-title") mod.module_config.module_title = el.value;
    if (el.dataset.bind === "show-title") mod.module_config.show_title = el.checked;
    if (el.dataset.bind === "fill") mod.module_config.fill = el.value;
    if (el.dataset.bind === "outline") mod.module_config.outline = el.value;
    if (el.dataset.bind === "text-color") mod.module_config.text_color = el.value;
  }));
  root.querySelectorAll("[data-cmd]").forEach(el => el.addEventListener(el.tagName === "SELECT" || el.type === "color" ? "input" : "click", () => {
    runEditorCommand(el.dataset.cmd, el.dataset.value || el.value || undefined);
  }));
  const upload = root.querySelector("[data-action='upload-editor-image']");
  if (upload) upload.addEventListener("change", async () => {
    try { await insertImagesIntoActiveEditor([...upload.files], state.currentProject?.id || "default"); upload.value = ""; setToast("图片已插入编辑器"); }
    catch (err) { setError(err); }
  });
}

function mountCurrentEditors() {
  if (state.view !== "poster") return;
  for (const mod of state.modules) {
    const bodyEl = root.querySelector(`[data-editor="${CSS.escape(mod.id)}:content"]`);
    if (bodyEl) mountEditor({ id: `${mod.id}:content`, el: bodyEl, target: mod.module_config, key: "content", onChange: () => {} });
    for (const sub of mod.module_config.subsections || []) {
      const titleEl = root.querySelector(`[data-editor="${CSS.escape(mod.id)}:${CSS.escape(sub.id)}:title"]`);
      const textEl = root.querySelector(`[data-editor="${CSS.escape(mod.id)}:${CSS.escape(sub.id)}:text"]`);
      if (titleEl) mountEditor({ id: `${mod.id}:${sub.id}:title`, el: titleEl, target: sub, key: "title", onChange: () => {} });
      if (textEl) mountEditor({ id: `${mod.id}:${sub.id}:text`, el: textEl, target: sub, key: "text", onChange: () => {} });
    }
  }
}

export async function startModernPlatform({ version }) {
  state.version = version;
  document.body.classList.add("modern-platform-active");
  root.innerHTML = "<div class='modern-loading'>正在启动新前端体系…</div>";
  await window.TIPTAP_READY?.catch(() => null);
  await loadProjects();
  render();
}
