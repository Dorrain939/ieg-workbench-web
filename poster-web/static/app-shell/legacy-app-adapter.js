// IEG 海报拼搭器 · 前端逻辑
const { createApp, reactive, ref, computed, onMounted, watch, nextTick } = Vue;

// ========== 常量 ==========
const STATUS_LABEL = { in_progress: '进行中', pending: '待启动', archived: '已归档' };
const TABS = [
  { key: 'all', label: '全部', icon: '📁' },
  { key: 'in_progress', label: '进行中', icon: '▶' },
  { key: 'pending', label: '待启动', icon: '⏸' },
  { key: 'archived', label: '已归档', icon: '📦' },
  { key: 'week_updated', label: '本周更新', icon: '✨' },
];
const NAV_META = {
  projects: { icon: '📁', title: '项目管理', desc: '按培训活动组织文案稿与海报版本。' },
  templates: { icon: '📋', title: '模板库', desc: '收藏常用 brief 模板，快速复制为新项目。' },
  materials: { icon: '🖼️', title: '素材库', desc: '上传共享插画、Logo、装饰图，跨项目复用。' },
  knowledge: { icon: '📚', title: '知识库', desc: '挂载品牌规范、过往海报案例，AI 调用时自动检索。' },
  tasks: { icon: '✅', title: '我的任务', desc: '聚合所有项目里指给你的待办，例如 brief 待审核、文案待填回。' },
  trash: { icon: '🗑️', title: '回收站', desc: '已删除的项目暂存 30 天，可一键恢复。' },
};
const SKILL_LABEL = { design_brief: '设计阐释', copywriter: '文案生成', poster_render: '海报渲染', poster_brief: '海报生图', poster_copy_import: '文案识别成图' };
const SKILL_ICON = { design_brief: '🧭', copywriter: '✍️', poster_render: '🖼️', poster_brief: '🎨', poster_copy_import: '📄' };
const KB_ACCEPT = '.txt,.md,.markdown,.json,.html,.htm,.pdf,.docx,.pptx,.csv,.tsv,.xlsx,.xls,.png,.jpg,.jpeg,.webp,.gif,.bmp,.svg';
const COLOR_SWATCHES = ['auto', '#FFFFFF', '#111827', '#2563EB', '#9333EA', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#FBBF24'];
const MODULE_NAME_LABELS = {
  'module.tm1_tm13_visual_layer': '海报主视觉编辑区',
  'module.tm1_top_logo': 'TM1 顶部 Logo',
  'module.tm2_bottom_logo': 'TM2 底部 Logo',
  'module.tm3_global_bg': 'TM3 全局底图',
  'module.tm4_hero_bg': 'TM4 头部底图',
  'module.tm5_main_wordart': 'TM5 主标题艺术字',
  'module.tm6_subtitle_wordart': 'TM6 副标题艺术字',
  'module.tm7_main_title_decoration': 'TM7 主标题装饰图',
  'module.tm8_subtitle_decoration': 'TM8 副标题装饰图',
  'module.tm9_section_title_plain': 'TM9 模块标题（简洁下划线）',
  'module.tm10_section_title_left_card': 'TM10 模块标题（左侧标题卡）',
  'module.tm11_section_title_center_card': 'TM11 模块标题（居中标题卡）',
  'module.tm12_section_title_decoration': 'TM12 模块标题装饰图',
  'module.tm13_module_frame': 'TM13 模块底框/背景素材',
  'module.hero_title': '海报主视觉编辑区',
  'module.theme_hero': '主题标题区',
  'module.theme_hero_review': '回顾标题区',
  'module.series_identity': '系列识别标题区',
  'module.series_identity_feedback': '系列反馈标题区',
  'module.project_background': '项目背景',
  'module.project_overview': '项目概览',
  'module.project_content': '项目内容',
  'module.project_recap': '项目回顾',
  'module.completion_response': '结项回应',
  'module.closing_blessing': '收尾祝福',
  'module.training_goals': '培养目标',
  'module.share_outline': '分享提纲',
  'module.share_recap': '分享回顾',
  'module.event_summary': '活动摘要',
  'module.signup_notice': '报名须知',
  'module.core_question': '核心问题',
  'module.next_preview': '下期预告',
  'module.series_next': '系列导航/下期入口',
  'module.faculty_grid': '讲师阵容',
  'module.guest_profile_deep': '讲师阵容',
  'module.agenda_table': '日程/安排表',
  'module.logo_endorsement': '品牌 Logo 视觉层',
  'module.signup_cta': '报名按钮',
  'module.replay_cta': '回放按钮',
  'module.qa_interview': '访谈问答',
  'module.project_timeline': '项目时间轴',
  'module.full_timeline': '完整历程时间轴',
  'module.photo_collage': '活动照片墙',
  'module.group_photo': '大合影展示',
  'module.course_matrix': '课程矩阵',
  'module.course_rating': '课程评分',
  'module.rating_summary': '评分汇总',
  'module.event_multidim_rating': '多维评分',
  'module.student_voice': '学员反馈',
  'module.feedback_gain_suggestion': '收获与建议反馈',
  'module.work_showcase': '作品/成果展示',
  'module.mentor_quote': '导师寄语',
  'module.course_card': '课程卡片',
  'module.course_feedback_card': '课程反馈卡片',
  'module.course_feedback_schema': '课程反馈子结构',
  'module.m1_text': 'M1 纯文字',
  'module.m2_highlight_text': 'M2 纯文字（含高亮）',
  'module.m3_text_subsections': 'M3 纯文字父子模块',
  'module.m4_plain_text': 'M4 无底框纯文字',
  'module.m5_text_table': 'M5 文字 + 表格',
  'module.m6_image_text_single': 'M6 单图图文',
  'module.m7_image_text_subsections': 'M7 图文父子模块',
  'module.m8_single_image_text': 'M8 文字 + 单图',
  'module.m9_multi_image_text': 'M9 文字 + 多图',
  'module.m10_single_person_card': 'M10 单人卡片',
  'module.m11_person_cards_row': 'M11 多张头像卡片',
  'module.m12_avatar_wall': 'M12 多人头像墙',
  'module.m13_avatar_wall_groups': 'M13 多人头像墙父子模块',
  'module.m14_text_name_list': 'M14 纯文字名单',
  'module.m15_text_name_list_groups': 'M15 纯文字名单父子模块',
  'module.m16_course_speaker_split': 'M16 课程卡片（左讲师右课程）',
  'module.m17_course_text_speaker': 'M17 课程卡片（上文下讲师）',
  'module.m18_course_parent_children': 'M18 多课程父子模块',
  'module.m19_rating_bars': 'M19 课程评分条',
  'module.m20_single_image': 'M20 纯图片单张',
  'module.m21_multi_image_collage': 'M21 纯图片拼盘',
  'module.m22_button_inside': 'M22 按钮（模块内）',
  'module.m23_button_outside': 'M23 按钮（模块外）',
  'module.m24_contact_text': 'M24 联系方式文字',
  'module.m25_contact_qr': 'M25 联系方式二维码',
};
const COMPONENT_LABELS = {
  hero_strip: '标题视觉层',
  series_identity: '系列识别',
  lead_paragraph: '正文段落',
  bullet_points_block: '要点列表',
  info_card: '信息卡片',
  notice_box: '提示/预告框',
  faculty_grid: '讲师头像网格',
  data_table: '表格',
  complex_table: '复杂表格',
  table_module: '表格图片模块',
  top_logo_bar: 'Logo 条',
  footer_logobar: 'Logo 条',
  cta_button: '行动按钮',
  qa_block: '问答卡片',
  curriculum_timeline: '时间轴',
  image_block: '图片模块',
  spec_text_panel: '纯文字规格',
  spec_image_grid: '图片网格规格',
  spec_image_text_split: '图文混排规格',
  spec_action_bar: '独立按钮规格',
  spec_rating_bars: '评分条规格',
  spec_avatar_group_wall: '分组头像墙规格',
  spec_quote_cards: '反馈引言卡规格',
  spec_course_card_list: '课程/讲师大模块规格',
  spec_feedback_story_flow: '反馈故事流规格',
};
const STRUCTURED_RENDERERS = new Set([
  'faculty_grid',
  'qa_block',
  'curriculum_timeline',
  'data_table',
  'complex_table',
  'cta_button',
  'contact_inline',
  'spec_text_panel',
  'spec_avatar_group_wall',
  'spec_course_card_list',
  'spec_feedback_story_flow',
  'spec_rating_bars',
  'spec_quote_cards',
  'spec_image_grid',
  'spec_image_text_split',
  'spec_action_bar',
]);

// ========== 工具函数 ==========
function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function moduleMCode(m) {
  const key = String(m?.script_key || '');
  const mm = key.match(/^module\.m(\d+)_/);
  return mm ? Number(mm[1]) : 0;
}

// 按 . 分割的 key 取/设值（如 "title_card.image"）
function getDeep(obj, path) {
  return path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
}
function setDeep(obj, path, val) {
  const keys = path.split('.');
  let cur = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    if (!cur[keys[i]] || typeof cur[keys[i]] !== 'object') cur[keys[i]] = {};
    cur = cur[keys[i]];
  }
  cur[keys[keys.length - 1]] = val;
}

// 清洗 brief：删除 _uid、空字符串文件路径、null/undefined
function sanitizeBrief(brief) {
  const cleaned = JSON.parse(JSON.stringify(brief));
  // 文件类字段（可能因用户清空残留 ""）— 凡 path 结尾或 image/avatar 字段，空字符串就删
  const FILE_HINT_KEYS = [
    'image', 'image_path', 'avatar', 'asset_frame_path', 'logo_path',
    'bg_image_path', 'global_bg_path', 'qr_image', 'wordart_path',
  ];
  function clean(obj) {
    if (obj == null) return;
    if (Array.isArray(obj)) {
      // 过滤数组中的空字符串
      for (let i = obj.length - 1; i >= 0; i--) {
        if (obj[i] === '' || obj[i] == null) obj.splice(i, 1);
        else if (typeof obj[i] === 'object') clean(obj[i]);
      }
      return;
    }
    if (typeof obj !== 'object') return;
    for (const k of Object.keys(obj)) {
      const v = obj[k];
      if (k === '_uid') { delete obj[k]; continue; }
      // 空字符串的文件字段直接删
      if (FILE_HINT_KEYS.includes(k) && (v === '' || v == null)) {
        delete obj[k];
        continue;
      }
      // 通用：null / undefined 删
      if (v == null) { delete obj[k]; continue; }
      // 递归
      if (typeof v === 'object') clean(v);
    }
  }
  clean(cleaned);

  // 强类型修正：常见 LLM 出错点
  if (cleaned.canvas) {
    // bg_colors 必须是 [a, b] 数组
    const bg = cleaned.canvas.bg_colors;
    if (typeof bg === 'string') {
      cleaned.canvas.bg_colors = [bg, bg];
    } else if (Array.isArray(bg)) {
      if (bg.length === 0) delete cleaned.canvas.bg_colors;
      else if (bg.length === 1) cleaned.canvas.bg_colors = [bg[0], bg[0]];
      else if (bg.length > 2) cleaned.canvas.bg_colors = bg.slice(0, 2);
    }
  }

  // sections 字段类型修正
  (cleaned.sections || []).forEach(s => {
    // notice_box: bullets 中 dict 必须有 text
    if (s.type === 'notice_box' && Array.isArray(s.bullets)) {
      s.bullets = s.bullets.filter(b => {
        if (typeof b === 'string') return b.trim() !== '';
        if (b && typeof b === 'object') return b.text;
        return false;
      });
    }
    // data_table: rows 必须是二维数组
    if (s.type === 'data_table') {
      if (Array.isArray(s.rows)) {
        s.rows = s.rows.filter(r => Array.isArray(r) && r.length > 0);
      }
      // headers 必须是字符串数组
      if (Array.isArray(s.headers)) {
        s.headers = s.headers.map(h => typeof h === 'string' ? h : String(h ?? ''));
      }
    }
    // faculty_grid: members 数组
    if (s.type === 'faculty_grid' && Array.isArray(s.members)) {
      s.members = s.members.filter(m => m && typeof m === 'object');
    }
    // 数字字段：常见错传字符串
    const NUMERIC_KEYS = ['font_size', 'header_font_size', 'name_font_size',
      'title_font_size', 'avatar_size', 'pad_top', 'pad_bottom', 'pad',
      'gap', 'gap_x', 'gap_y', 'cols', 'ring_width', 'frame_inset',
      'offset_x', 'corner', 'corner_radius', 'line_height',
      'index', 'logo_height', 'qr_size', 'max_title_lines'];
    for (const k of NUMERIC_KEYS) {
      if (s[k] !== undefined && typeof s[k] === 'string') {
        const n = parseFloat(s[k]);
        if (!isNaN(n)) s[k] = n; else delete s[k];
      }
    }
    // image_block 的 image_path 必须有，否则删 section（避免引擎崩）
    if (s.type === 'image_block' && (!s.image_path || s.image_path === '')) {
      s.__skip = true;
    }
  });
  cleaned.sections = (cleaned.sections || []).filter(s => !s.__skip);

  return cleaned;
}

// ========== 通用字段表单组件 ==========
const FieldForm = {
  props: ['fields', 'model', 'sessionId', 'skillUploads', 'assetTypes'],
  data() { return { colorSwatches: COLOR_SWATCHES }; },
  emits: ['upload', 'change'],
  template: `
  <div>
    <div v-for="f in fields" :key="f.key" class="form-row">
      <label>{{ f.label }} <span v-if="f.required" style="color:var(--accent-light)">*</span></label>

      <!-- text -->
      <input v-if="f.type==='text'" type="text" :value="get(f.key)" @input="set(f.key, $event.target.value)" />

      <!-- textarea -->
      <textarea v-else-if="f.type==='textarea'" :value="get(f.key)"
        @input="set(f.key, $event.target.value)"></textarea>

      <!-- number -->
      <input v-else-if="f.type==='number'" type="number" :value="get(f.key)"
        :min="f.min" :max="f.max" :step="f.step || 1"
        @input="set(f.key, parseFloat($event.target.value))" />

      <!-- select -->
      <select v-else-if="f.type==='select'" :value="get(f.key)" @change="set(f.key, $event.target.value)">
        <option v-for="opt in normalizeOptions(f.options)" :value="opt.value">{{ opt.label }}</option>
      </select>

      <!-- bool -->
      <label v-else-if="f.type==='bool'" class="checkbox">
        <input type="checkbox" :checked="get(f.key)" @change="set(f.key, $event.target.checked)" />
        启用
      </label>

      <!-- color -->
      <div v-else-if="f.type==='color'" class="swatch-field">
        <div class="swatch-row">
          <button v-for="c in colorSwatches" :key="c" type="button"
            class="color-swatch" :class="{ active: (get(f.key) || f.default) === c, auto: c === 'auto' }"
            :style="c === 'auto' ? {} : { background: c }"
            @click="set(f.key, c)">{{ c === 'auto' ? 'A' : '' }}</button>
        </div>
        <input type="text" :value="get(f.key)" @input="set(f.key, $event.target.value)" placeholder="auto 或 #RRGGBB" />
      </div>

      <!-- color2: 两个色值（渐变） -->
      <div v-else-if="f.type==='color2'" class="swatch-field">
        <div class="color-pair-inputs">
          <input type="text" :value="(get(f.key) || ['#000','#000'])[0]" @input="setIdx(f.key, 0, $event.target.value)" />
          <input type="text" :value="(get(f.key) || ['#000','#000'])[1]" @input="setIdx(f.key, 1, $event.target.value)" />
        </div>
        <div class="swatch-row">
          <button v-for="c in colorSwatches.filter(x => x !== 'auto')" :key="c" type="button"
            class="color-swatch" :style="{ background: c }" @click="set(f.key, [c, c])"></button>
        </div>
      </div>

      <!-- file -->
      <div v-else-if="f.type==='file'">
        <div class="asset-type-hint" v-if="fieldAssetTypes(f).length">
          只接收：{{ fieldAssetTypes(f).map(assetTypeLabel).join(' / ') }}
        </div>
        <div class="file-row">
          <input type="text" :value="get(f.key)" placeholder="上传或粘贴路径"
            @input="set(f.key, $event.target.value)" />
          <button class="btn btn-sm" @click="triggerUpload(f.key, f)">上传</button>
          <button class="btn btn-sm" @click="pickFromLib(f.key, f)">素材库</button>
        </div>
        <div v-if="get(f.key)" class="file-preview">
          <img :src="filePreviewUrl(get(f.key))" @error="$event.target.style.display='none'" />
        </div>
      </div>

      <!-- array (字符串数组，每行一个) -->
      <textarea v-else-if="f.type==='array'"
        :value="(get(f.key) || []).join('\\n')"
        @input="set(f.key, $event.target.value.split('\\n').filter(x => x !== ''))"
        :placeholder="'每行一项'"></textarea>

      <!-- matrix: 二维数组 -->
      <table v-else-if="f.type==='matrix'" class="matrix-table">
        <tbody>
          <tr v-for="(row, ri) in get(f.key) || []" :key="ri">
            <td v-for="(cell, ci) in row" :key="ci">
              <input :value="cell"
                @input="setMatrix(f.key, ri, ci, $event.target.value)" />
            </td>
            <td style="width:30px">
              <button class="btn btn-sm btn-danger" @click="rmMatrixRow(f.key, ri)">×</button>
            </td>
          </tr>
        </tbody>
      </table>
      <button v-if="f.type==='matrix'" class="btn btn-sm" @click="addMatrixRow(f.key)">+ 添加行</button>

      <!-- members (faculty) -->
      <div v-else-if="f.type==='members'">
        <div class="member-list">
          <div v-for="(m, mi) in (get(f.key) || [])" :key="mi" class="member-row">
            <div class="row-fields">
              <input placeholder="姓名" :value="m.name" @input="setMember(f.key, mi, 'name', $event.target.value)" />
              <input placeholder="职务" :value="m.title" @input="setMember(f.key, mi, 'title', $event.target.value)" />
              <div class="file-row">
                <input placeholder="头像路径" :value="m.avatar"
                  @input="setMember(f.key, mi, 'avatar', $event.target.value)" />
                <button class="btn btn-sm" @click="triggerUploadMember(f.key, mi)">上传</button>
              </div>
            </div>
            <button class="btn btn-sm btn-danger" @click="rmMember(f.key, mi)">×</button>
          </div>
        </div>
        <button class="btn btn-sm" @click="addMember(f.key)" style="margin-top:6px">+ 添加成员</button>
      </div>

      <!-- bullets -->
      <div v-else-if="f.type==='bullets'">
        <div v-for="(b, bi) in normalizedBullets(f.key)" :key="bi" class="bullet-row">
          <textarea :value="b.text" @input="setBulletText(f.key, bi, $event.target.value)"></textarea>
          <div class="meta">
            <label class="checkbox">
              <input type="checkbox" :checked="b.highlight"
                @change="setBulletHighlight(f.key, bi, $event.target.checked)" />
              高亮
            </label>
            <div v-if="b.highlight" class="swatch-row mini">
              <button v-for="c in colorSwatches.filter(x => x !== 'auto')" :key="c" type="button"
                class="color-swatch" :class="{ active: (b.highlight_color || '#FF4444') === c }"
                :style="{ background: c }" @click="setBulletColor(f.key, bi, c)"></button>
            </div>
            <button class="btn btn-sm btn-danger" @click="rmBullet(f.key, bi)" style="margin-left:auto">×</button>
          </div>
        </div>
        <button class="btn btn-sm" @click="addBullet(f.key)" style="margin-top:6px">+ 添加条目</button>
      </div>

      <!-- 默认：未知类型 -->
      <input v-else type="text" :value="get(f.key)" @input="set(f.key, $event.target.value)" />
    </div>
  </div>
  `,
  methods: {
    get(key) {
      return getDeep(this.model, key);
    },
    set(key, val) {
      setDeep(this.model, key, val);
      this.$emit('change', { key, value: val });
    },
    setIdx(key, idx, val) {
      const arr = (this.get(key) || []).slice();
      arr[idx] = val;
      this.set(key, arr);
    },
    normalizeOptions(opts) {
      if (!opts) return [];
      return opts.map(o => typeof o === 'string' ? { value: o, label: o } : o);
    },
    fieldAssetTypes(f) {
      return Array.isArray(f?.asset_types) ? f.asset_types : [];
    },
    defaultAssetType(f) {
      return this.fieldAssetTypes(f)[0] || 'module_content_image';
    },
    assetTypeLabel(value) {
      const item = (this.assetTypes || []).find(x => x.value === value);
      return item?.label || value || '图片素材';
    },
    triggerUpload(key, f) {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = async () => {
        if (!input.files[0]) return;
        const fd = new FormData();
        fd.append('file', input.files[0]);
        fd.append('session_id', this.sessionId);
        fd.append('asset_type', this.defaultAssetType(f));
        fd.append('asset_label', this.assetTypeLabel(this.defaultAssetType(f)));
        const r = await fetch('/api/upload', { method: 'POST', body: fd });
        const j = await r.json();
        if (j.path) this.set(key, j.path);
      };
      input.click();
    },
    triggerUploadMember(key, mi) {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = async () => {
        if (!input.files[0]) return;
        const fd = new FormData();
        fd.append('file', input.files[0]);
        fd.append('session_id', this.sessionId);
        fd.append('asset_type', 'person_avatar');
        fd.append('asset_label', '人员头像图');
        fd.append('related_name', (this.get(key) || [])[mi]?.name || '');
        fd.append('related_title', (this.get(key) || [])[mi]?.title || '');
        const r = await fetch('/api/upload', { method: 'POST', body: fd });
        const j = await r.json();
        if (j.path) this.setMember(key, mi, 'avatar', j.path);
      };
      input.click();
    },
    pickFromLib(key, f) {
      this.$emit('upload', { type: 'pick', key, asset_types: this.fieldAssetTypes(f) });
    },
    filePreviewUrl(p) {
      if (!p) return '';
      // 已是 url
      if (p.startsWith('/api/') || p.startsWith('http')) return p;
      // 走 skill-asset
      return '/api/skill-asset?path=' + encodeURIComponent(p);
    },
    // matrix
    setMatrix(key, ri, ci, val) {
      const m = JSON.parse(JSON.stringify(this.get(key) || []));
      while (m.length <= ri) m.push([]);
      while (m[ri].length <= ci) m[ri].push('');
      m[ri][ci] = val;
      this.set(key, m);
    },
    addMatrixRow(key) {
      const m = (this.get(key) || []).slice();
      const cols = m[0]?.length || 2;
      m.push(Array(cols).fill(''));
      this.set(key, m);
    },
    rmMatrixRow(key, ri) {
      const m = (this.get(key) || []).slice();
      m.splice(ri, 1);
      this.set(key, m);
    },
    // members
    addMember(key) {
      const arr = (this.get(key) || []).slice();
      arr.push({ name: '', title: '', avatar: '' });
      this.set(key, arr);
    },
    setMember(key, mi, field, val) {
      const arr = JSON.parse(JSON.stringify(this.get(key) || []));
      if (!arr[mi]) arr[mi] = {};
      arr[mi][field] = val;
      this.set(key, arr);
    },
    rmMember(key, mi) {
      const arr = (this.get(key) || []).slice();
      arr.splice(mi, 1);
      this.set(key, arr);
    },
    // bullets
    normalizedBullets(key) {
      const arr = this.get(key) || [];
      return arr.map(b => typeof b === 'string'
        ? { text: b, highlight: false }
        : { text: b.text || '', highlight: !!b.highlight,
            highlight_color: b.highlight_color || '#FF4444' });
    },
    addBullet(key) {
      const arr = (this.get(key) || []).slice();
      arr.push('');
      this.set(key, arr);
    },
    rmBullet(key, bi) {
      const arr = (this.get(key) || []).slice();
      arr.splice(bi, 1);
      this.set(key, arr);
    },
    setBulletText(key, bi, val) {
      const norm = this.normalizedBullets(key);
      norm[bi].text = val;
      this.writeBullets(key, norm);
    },
    setBulletHighlight(key, bi, val) {
      const norm = this.normalizedBullets(key);
      norm[bi].highlight = val;
      this.writeBullets(key, norm);
    },
    setBulletColor(key, bi, val) {
      const norm = this.normalizedBullets(key);
      norm[bi].highlight_color = val;
      this.writeBullets(key, norm);
    },
    writeBullets(key, norm) {
      // 没高亮的存字符串，有高亮的存 dict（兼容引擎期望的格式）
      const out = norm.map(b => b.highlight
        ? { text: b.text, highlight: true, highlight_color: b.highlight_color }
        : b.text
      );
      this.set(key, out);
    },
  },
};

// ========== 主应用 ==========
const app = createApp({
  components: { FieldForm },
  setup() {
    // ========== 视图状态机（v0.2 新增） ==========
    const view = ref('list');               // 'list' | 'detail' | 'editor'
    const projects = ref([]);
    const projectStats = reactive({ in_progress: 0, pending: 0, archived: 0, week_updated: 0 });
    const currentProject = ref(null);

    // 列表筛选 / sidebar
    const navTab = ref('projects');         // projects/templates/materials/knowledge/tasks/trash
    const filterTab = ref('all');           // all/in_progress/pending/archived
    const searchQuery = ref('');
    const menuOpenFor = ref(null);
    const detailStatusMenuOpen = ref(false);
    const homeAssistant = reactive({
      mode: 'project',
      input: '',
      reply: '',
      busy: false,
      messages: [],
      pendingPrompt: '',
      attachments: [],
      uploadingAttachment: false,
      listening: false,
      recognition: null,
    });
    const projectAssistantMemory = reactive({});

    // v0.4 详情页二级导航
    const detailNav = ref('overview');  // overview/copywriter/poster_brief/interview_outline/ppt_outline/kb/all_artifacts
    const runningJob = ref(null);  // 当前正在运行的 skill job（H7 简化版仅前端追踪）
    const artifactHistoryOpen = ref(false);
    let posterStrategySaveTimer = null;
    let posterPreviewRenderTimer = null;

    // Skill 注册表（启动拉一次）
    const skillsRegistry = ref({});
    // Skill 表单的当前值（按 detailNav 切换时重置）
    const skillForm = reactive({});
    const skillRunning = ref(false);
    const skillStream = reactive({
      streaming: false,
      done: false,
      error: '',
      text: '',           // 累积的 token 文本
      progress: [],       // 进度提示
      lastArtifact: null,
      posterUrl: '',      // 海报渲染产物 URL（poster_brief 用）
      posterPreviewDirty: false,
      autoSaving: false,
    });
    const posterLightbox = reactive({
      show: false,
      url: '',
      zoom: 100,
    });
    const copyImport = reactive({
      uploading: false,
      doc: null,
      file: null,
      fileName: '',
      extra: '',
      globalBgPrompt: '',
      heroBgPrompt: '',
      wordartPrompt: '',
      subtitleText: '',
      titleVisualMode: 'auto',
      logoPosition: 'bottom',
      logoAlign: 'center',
      logoHeight: 76,
      logoGap: 80,
      visualLayerUploads: {
        global_bg: [],
        hero_bg: [],
        main_wordart: [],
        subtitle_wordart: [],
        module_frame: [],
        logo_color: [],
      },
      visualAssetType: 'global_bg',
      visualAssetLabel: '',
      visualAssets: [],
      visualAssetsUploading: false,
    });

    const posterStrategies = reactive({ project_types: [], scenes: {}, theme_style_map: [], default: null });
    const posterStrategySelection = reactive({ project_type: 'A', scene: 'S1' });
    const posterStrategy = ref(null);
    const posterFunctionProjects = ref([]);
    const selectedPosterFunctionProjectIds = ref([]);
    const currentPosterFunctionProject = ref(null);
    const posterFunctionProjectsLoading = ref(false);
    const posterEditDirty = ref(false);
    const posterFunctionNameEditing = ref(false);
    const posterFunctionNameBeforeEdit = ref('');
    const posterFunctionCreate = reactive({
      show: false,
      busy: false,
      name: '',
      project_type: 'A',
      scene: 'S1',
      strategy: null,
    });
    let choiceDialogResolve = null;
    const choiceDialog = reactive({
      show: false,
      title: '',
      message: '',
      primaryLabel: '',
      secondaryLabel: '',
    });
    const moduleAddKey = ref('');
    const moduleImageUploading = reactive({});
    const moduleAutofill = reactive({
      files: [],
      fileMetas: [],
      imageAssets: [],
      running: false,
      copyGenerating: false,
      copyApplying: false,
      copyRequirement: '',
      overwriteMode: 'fill_empty',
      copyDraft: null,
      copySavedArtifact: null,
      notes: [],
    });
    const copyChat = reactive({
      history: [],
      input: '',
      busy: false,
      kbOpen: false,
    });
    const copyChatMessagesEl = ref(null);

    const MODULE_UNDERLINE_COLORS = [
      { label: '自动', value: 'auto', color: 'linear-gradient(90deg,#2563EB,#06B6D4)' },
      { label: '黑色', value: '#111827', color: '#111827' },
      { label: '深灰', value: '#374151', color: '#374151' },
      { label: '浅灰', value: '#9CA3AF', color: '#9CA3AF' },
      { label: '白色', value: '#FFFFFF', color: '#FFFFFF' },
      { label: '红色', value: '#EF4444', color: '#EF4444' },
      { label: '玫红', value: '#E11D48', color: '#E11D48' },
      { label: '橙色', value: '#F97316', color: '#F97316' },
      { label: '金色', value: '#F59E0B', color: '#F59E0B' },
      { label: '黄色', value: '#FACC15', color: '#FACC15' },
      { label: '草绿', value: '#84CC16', color: '#84CC16' },
      { label: '绿色', value: '#10B981', color: '#10B981' },
      { label: '青色', value: '#06B6D4', color: '#06B6D4' },
      { label: '天蓝', value: '#38BDF8', color: '#38BDF8' },
      { label: '蓝色', value: '#2563EB', color: '#2563EB' },
      { label: '靛蓝', value: '#4F46E5', color: '#4F46E5' },
      { label: '紫色', value: '#7C3AED', color: '#7C3AED' },
      { label: '浅紫', value: '#A855F7', color: '#A855F7' },
      { label: '粉色', value: '#EC4899', color: '#EC4899' },
      { label: '珊瑚', value: '#FB7185', color: '#FB7185' },
      { label: '棕色', value: '#92400E', color: '#92400E' },
      { label: '深蓝', value: '#1E3A8A', color: '#1E3A8A' },
      { label: '深紫', value: '#581C87', color: '#581C87' },
      { label: '墨绿', value: '#065F46', color: '#065F46' },
      { label: '透明', value: 'transparent', color: 'repeating-linear-gradient(45deg,#fff,#fff 4px,#e5e7eb 4px,#e5e7eb 8px)' },
    ];
    const MODULE_PANEL_COLORS = MODULE_UNDERLINE_COLORS;
    const MODULE_BORDER_COLORS = MODULE_UNDERLINE_COLORS;
    const MODULE_TEXT_COLORS = MODULE_UNDERLINE_COLORS;
    const MODULE_FONT_OPTIONS = [
      { label: '默认中文黑体', value: 'default' },
      { label: '苹方 / 系统黑体', value: 'pingfang' },
      { label: '思源黑体', value: 'source_han_sans' },
      { label: 'Inter / SF Pro', value: 'inter' },
    ];
    const floatingRich = reactive({
      visible: false,
      slot: 'body',
      top: 0,
      left: 0,
      target: null,
      key: '',
      editor: null,
      range: null,
      font_family: 'default',
      font_size: 24,
      text_color: '#111827',
      highlight_color: '#FFF3A3',
      uploadingImage: false,
    });
    const floatingRichStyle = computed(() => ({
      top: `${floatingRich.top}px`,
      left: `${floatingRich.left}px`,
    }));


    // ============================================================
    // TipTap 富文本编辑器运行时（生产工程版同样复用这套数据合同）
    // - editor_json 是主数据；content_html/content/images 是兼容字段
    // - 图片使用正式 posterImage 节点，并支持 8 个方向缩放
    // ============================================================
    const tiptapEditors = new WeakMap();
    const tiptapEditorEls = new Set();
    let tiptapExtensionsCache = null;


    async function fetchPosterStrategies() {
      try {
        const r = await fetch('/api/poster-strategies');
        const j = await r.json();
        Object.assign(posterStrategies, j);
        posterStrategy.value = hydratePosterStrategy(j.default || null);
      } catch (e) {
        showToast('加载海报策略规则失败：' + e, 'error');
      }
    }

    async function resolvePosterStrategy() {
      try {
        const r = await fetch('/api/poster-strategies/resolve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...posterStrategySelection }),
        });
        const j = await r.json();
        posterStrategy.value = hydratePosterStrategy(j);
      } catch (e) {
        showToast('解析海报策略失败：' + e, 'error');
      }
    }

    async function resetPosterGenerationWorkspace() {
      if (posterPreviewRenderTimer) {
        clearTimeout(posterPreviewRenderTimer);
        posterPreviewRenderTimer = null;
      }
      if (posterStrategySaveTimer) {
        clearTimeout(posterStrategySaveTimer);
        posterStrategySaveTimer = null;
      }
      copyImport.file = null;
      copyImport.fileName = '';
      copyImport.doc = null;
      copyImport.extra = '';
      copyImport.visualAssetLabel = '';
      copyImport.visualAssets.splice(0);
      for (const key of Object.keys(copyImport.visualLayerUploads || {})) {
        copyImport.visualLayerUploads[key] = [];
      }
      copyImport.globalBgPrompt = '';
      copyImport.heroBgPrompt = '';
      copyImport.wordartPrompt = '';
      copyImport.subtitleText = '';
      await fetchPosterFunctionProjects();
      if (currentPosterFunctionProject.value) {
        loadPosterFunctionProject(currentPosterFunctionProject.value);
      } else if (currentProject.value?.poster_strategy) {
        posterStrategy.value = hydratePosterStrategy(currentProject.value.poster_strategy);
        posterStrategySelection.project_type = posterStrategy.value?.project_type?.id || currentProject.value.project_type || posterStrategySelection.project_type;
        posterStrategySelection.scene = posterStrategy.value?.scene?.id || currentProject.value.scene || posterStrategySelection.scene;
        applyTitleVisualConfig(posterStrategy.value?.title_visual_config || {});
      } else {
        await resolvePosterStrategy();
      }
    }

    function selectProjectTypeForPoster(typeId) {
      posterStrategySelection.project_type = typeId;
      const type = posterStrategies.project_types.find(t => t.id === typeId);
      if (type && !type.allowed_scenes.includes(posterStrategySelection.scene)) {
        posterStrategySelection.scene = type.allowed_scenes[0];
      }
      resolvePosterStrategy();
    }

    async function selectProjectTypeForNewProject(typeId) {
      newProjectForm.project_type = typeId;
    }

    function allowedNewProjectScenes() {
      const type = posterStrategies.project_types.find(t => t.id === newProjectForm.project_type);
      const keys = type?.allowed_scenes || [];
      return keys.map(k => ({ key: k, ...(posterStrategies.scenes[k] || {}) }));
    }

    async function resolveNewProjectStrategy() {
      try {
        const r = await fetch('/api/poster-strategies/resolve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ project_type: newProjectForm.project_type, scene: newProjectForm.scene }),
        });
        const j = await r.json();
        newProjectForm.poster_strategy = hydratePosterStrategy(j);
      } catch (e) {
        showToast('解析新项目模块失败：' + e, 'error');
      }
    }

    function allowedPosterScenes() {
      const type = posterStrategies.project_types.find(t => t.id === posterStrategySelection.project_type);
      const keys = type?.allowed_scenes || [];
      return keys.map(k => ({ key: k, ...(posterStrategies.scenes[k] || {}) }));
    }

    function allowedCurrentPosterScenes() {
      return allowedPosterScenes();
    }

    function askChoice({ title, message, primaryLabel, secondaryLabel }) {
      choiceDialog.title = title || '确认操作';
      choiceDialog.message = message || '';
      choiceDialog.primaryLabel = primaryLabel || '确认';
      choiceDialog.secondaryLabel = secondaryLabel || '取消';
      choiceDialog.show = true;
      return new Promise(resolve => {
        choiceDialogResolve = resolve;
      });
    }

    function resolveChoiceDialog(choice) {
      choiceDialog.show = false;
      const resolve = choiceDialogResolve;
      choiceDialogResolve = null;
      if (resolve) resolve(choice);
    }

    async function resolveCurrentPosterStrategy() {
      await resolvePosterStrategy();
      if (currentPosterFunctionProject.value && posterStrategy.value) {
        currentPosterFunctionProject.value.project_type = posterStrategy.value.project_type?.id || posterStrategySelection.project_type;
        currentPosterFunctionProject.value.scene = posterStrategy.value.scene?.id || posterStrategySelection.scene;
      }
    }

    async function selectCurrentPosterType(typeId) {
      posterStrategySelection.project_type = typeId;
      const type = posterStrategies.project_types.find(t => t.id === typeId);
      if (type && !type.allowed_scenes.includes(posterStrategySelection.scene)) {
        posterStrategySelection.scene = type.allowed_scenes[0];
      }
      await resolveCurrentPosterStrategy();
    }

    async function openPosterFunctionCreateWith(projectType, sceneKey) {
      posterFunctionCreate.show = true;
      posterFunctionCreate.busy = false;
      posterFunctionCreate.project_type = projectType || posterStrategySelection.project_type || 'A';
      const type = posterStrategies.project_types.find(t => t.id === posterFunctionCreate.project_type);
      posterFunctionCreate.scene = type?.allowed_scenes?.includes(sceneKey)
        ? sceneKey
        : (type?.allowed_scenes?.[0] || sceneKey || 'S1');
      posterFunctionCreate.name = '';
      posterFunctionCreate.strategy = null;
      await resolvePosterFunctionCreateStrategy();
    }

    async function confirmPosterStrategyOverwrite(targetType, targetScene) {
      const choice = await askChoice({
        title: '确认变更海报类型/场景？',
        message: '变更后会按新的类型和场景重新生成模块编排，当前下方模块内容可能被覆盖。你也可以选择新建一个海报子项目，保留当前编辑内容。',
        primaryLabel: '确认变动并覆盖',
        secondaryLabel: '新建海报子项目',
      });
      if (choice === 'primary') {
        posterStrategySelection.project_type = targetType;
        posterStrategySelection.scene = targetScene;
        await resolveCurrentPosterStrategy();
        markPosterPreviewDirty();
        return true;
      }
      return false;
    }

    async function handleCurrentPosterTypeChange(typeId) {
      const oldType = posterStrategy.value?.project_type?.id || currentPosterFunctionProject.value?.project_type || 'A';
      const oldScene = posterStrategy.value?.scene?.id || currentPosterFunctionProject.value?.scene || 'S1';
      const type = posterStrategies.project_types.find(t => t.id === typeId);
      const nextScene = type?.allowed_scenes?.includes(oldScene) ? oldScene : (type?.allowed_scenes?.[0] || oldScene);
      const changed = typeId !== oldType || nextScene !== oldScene;
      if (!changed) return;
      const overwrite = await confirmPosterStrategyOverwrite(typeId, nextScene);
      if (!overwrite) {
        posterStrategySelection.project_type = oldType;
        posterStrategySelection.scene = oldScene;
        await createPosterFunctionProjectFromSelection(typeId, nextScene);
      }
    }

    async function handleCurrentPosterSceneChange(sceneKey) {
      const oldType = posterStrategy.value?.project_type?.id || currentPosterFunctionProject.value?.project_type || posterStrategySelection.project_type;
      const oldScene = posterStrategy.value?.scene?.id || currentPosterFunctionProject.value?.scene || 'S1';
      if (sceneKey === oldScene) return;
      const overwrite = await confirmPosterStrategyOverwrite(oldType, sceneKey);
      if (!overwrite) {
        posterStrategySelection.project_type = oldType;
        posterStrategySelection.scene = oldScene;
        await createPosterFunctionProjectFromSelection(oldType, sceneKey);
      }
    }

    function currentPosterStrategyPayload() {
      if (!posterStrategy.value) return null;
      flushAllTiptapEditorsToData();
      const payload = JSON.parse(JSON.stringify(posterStrategy.value));
      payload.project_id = currentProject.value?.id || '';
      payload.function_id = 'poster_brief';
      payload.function_project_id = currentPosterFunctionProject.value?.id || '';
      payload.function_project_name = currentPosterFunctionProject.value?.name || '';
      payload.module_plan = editableModulesPayload();
      payload.module_user_inputs = payload.module_plan.map(m => ({
        id: m.id,
        name: m.name,
        script_key: m.script_key,
        title_enabled: !!m.module_config?.title_enabled,
        module_title: m.module_config?.module_title || m.name,
        underline_color: m.module_config?.underline_color || 'auto',
        content: m.module_config?.content || '',
        images: m.module_config?.images || [],
        hero_layers: !!m.module_config?.hero_layers,
      }));
      payload.title_visual_config = titleVisualPayload();
      return payload;
    }

    function titleVisualPayload() {
      const layerAssets = Object.values(copyImport.visualLayerUploads || {}).flat().map(a => ({
        path: a.path,
        name: a.name,
        asset_type: a.asset_type,
        asset_type_label: a.asset_type_label,
        asset_label: a.asset_label || '',
      }));
      return {
        mode: copyImport.titleVisualMode || 'auto',
        subtitle_text: copyImport.subtitleText || '',
        logo_position: copyImport.logoPosition || 'bottom',
        logo_align: copyImport.logoAlign || 'center',
        logo_height: Number(copyImport.logoHeight || 76),
        logo_gap: Number(copyImport.logoGap || 80),
        global_bg_prompt: copyImport.globalBgPrompt || '',
        hero_bg_prompt: copyImport.heroBgPrompt || '',
        wordart_prompt: copyImport.wordartPrompt || '',
        layer_assets: layerAssets,
      };
    }

    function applyTitleVisualConfig(config = {}) {
      copyImport.titleVisualMode = config.mode || copyImport.titleVisualMode || 'auto';
      copyImport.subtitleText = config.subtitle_text || '';
      copyImport.logoPosition = config.logo_position || copyImport.logoPosition || 'bottom';
      copyImport.logoAlign = config.logo_align || copyImport.logoAlign || 'center';
      copyImport.logoHeight = Number(config.logo_height || copyImport.logoHeight || 76);
      copyImport.logoGap = Number(config.logo_gap || copyImport.logoGap || 80);
      copyImport.globalBgPrompt = config.global_bg_prompt || '';
      copyImport.heroBgPrompt = config.hero_bg_prompt || '';
      copyImport.wordartPrompt = config.wordart_prompt || '';
      for (const key of Object.keys(copyImport.visualLayerUploads || {})) {
        copyImport.visualLayerUploads[key] = [];
      }
      for (const asset of config.layer_assets || []) {
        const bucket = titleVisualBucket(asset.asset_type);
        if (!bucket) continue;
        copyImport.visualLayerUploads[bucket] = copyImport.visualLayerUploads[bucket] || [];
        copyImport.visualLayerUploads[bucket].push({ ...asset });
      }
    }

    function hydratePosterStrategy(strategy) {
      if (!strategy) return null;
      const cloned = JSON.parse(JSON.stringify(strategy));
      cloned.module_plan = (cloned.module_plan || []).map((m, idx) => hydrateStrategyModule(m, idx));
      return cloned;
    }

    function hydrateStrategyModule(module, idx = 0) {
      const cloned = JSON.parse(JSON.stringify(module || {}));
      cloned.id = cloned.id || `CUSTOM-${Date.now()}-${idx}`;
      cloned.name = cloned.name || '自定义模块';
      cloned.purpose = cloned.purpose || '补充本张海报需要的信息';
      cloned.component = cloned.component || 'lead_paragraph';
      cloned.script_key = cloned.script_key || `module.custom_${Date.now()}`;
      cloned.required = !!cloned.required;
      cloned.module_config = {
        title_enabled: !isTitleVisualModule(cloned) && cloned.component !== 'top_logo_bar',
        module_title: cloned.name,
        underline_color: 'auto',
        panel_fill: 'auto',
        panel_border: 'auto',
        module_frame_mode: 'generated',
        module_frame_path: '',
        title_decoration_path: '',
        title_decoration_position: 'left',
        title_decoration_size: 42,
        content: '',
        images: [],
        hero_layers: isTitleVisualModule(cloned),
        ...(cloned.module_config || {}),
      };
      cloned.ui_open = !!cloned.ui_open;
      cloned.ui_appearance_open = !!cloned.ui_appearance_open;
      cloned.ui_text_style_open = !!cloned.ui_text_style_open;
      ensureStructuredModuleConfig(cloned);
      return cloned;
    }

    function editableModulesPayload() {
      return (posterStrategy.value?.module_plan || []).map((m, idx) => ({
        ...JSON.parse(JSON.stringify(m)),
        order: idx + 1,
      }));
    }

    function moduleStatusLabel(m) {
      return m.status_label || m.capability?.status_label || '能力未登记';
    }

    function moduleStatusClass(m) {
      const status = m.status || m.capability?.status || 'missing';
      return {
        ready: status === 'ready',
        enhance: status === 'needs_enhancement',
        missing: status === 'missing',
      };
    }

    function moduleDisplayName(m) {
      if (!m) return '自定义模块';
      return m.display_name
        || MODULE_NAME_LABELS[m.script_key]
        || m.label
        || (m.name && !/^module\.|^[a-z0-9_]+$/i.test(m.name) ? m.name : '')
        || '自定义模块';
    }

    function moduleTitleLabel(m) {
      if (!m) return '自定义模块';
      if (isTitleVisualModule(m)) return '海报主视觉编辑区';
      return m.module_config?.module_title
        || (m.name && !/^module\.|^[a-z0-9_]+$/i.test(m.name) ? m.name : '')
        || m.display_name
        || MODULE_NAME_LABELS[m.script_key]
        || '自定义模块';
    }

    function startModuleTitleEdit(m) {
      if (!m || isTitleVisualModule(m) || isLogoVisualModule(m)) return;
      m.ui_title_before = m.module_config?.module_title || moduleTitleLabel(m);
      m.ui_title_editing = true;
      setTimeout(() => {
        const el = document.querySelector('.inline-module-title-input');
        if (el) {
          el.focus();
          el.select?.();
        }
      }, 0);
    }

    function finishModuleTitleEdit(m) {
      if (!m) return;
      const next = (m.module_config?.module_title || '').trim();
      if (!next) m.module_config.module_title = m.ui_title_before || m.name || '未命名模块';
      m.ui_title_editing = false;
      m.ui_title_before = '';
      markPosterPreviewDirty();
    }

    function cancelModuleTitleEdit(m) {
      if (!m) return;
      if (m.ui_title_before) m.module_config.module_title = m.ui_title_before;
      m.ui_title_editing = false;
      m.ui_title_before = '';
    }

    function colorOption(value) {
      return MODULE_UNDERLINE_COLORS.find(c => c.value === value) || MODULE_UNDERLINE_COLORS[0];
    }

    function colorOptionStyle(value) {
      return colorOption(value)?.color || 'linear-gradient(90deg,#2563EB,#06B6D4)';
    }

    function colorOptionLabel(value) {
      return colorOption(value)?.label || '自动';
    }

    function toggleModuleColorPicker(m, key) {
      if (!m) return;
      m.ui_color_picker = m.ui_color_picker === key ? '' : key;
    }

    function setModuleColor(m, key, value) {
      if (!m?.module_config) return;
      m.module_config[key] = value;
      if (key === 'text_color' && value && value !== 'auto' && value !== 'transparent') {
        richCommand('foreColor', value);
      }
      m.ui_color_picker = '';
      markPosterPreviewDirty();
    }

    function hexToRgb(hex) {
      if (!hex || typeof hex !== 'string' || !hex.startsWith('#') || hex.length < 7) return null;
      return {
        r: parseInt(hex.slice(1, 3), 16),
        g: parseInt(hex.slice(3, 5), 16),
        b: parseInt(hex.slice(5, 7), 16),
      };
    }

    function nearestModuleColor(rgb, opts = {}) {
      if (!rgb) return 'auto';
      const candidates = MODULE_UNDERLINE_COLORS
        .filter(c => c.value.startsWith('#'))
        .map(c => ({ ...c, rgb: hexToRgb(c.value) }))
        .filter(c => c.rgb);
      let best = candidates[0];
      let bestScore = Infinity;
      for (const c of candidates) {
        const dr = c.rgb.r - rgb.r;
        const dg = c.rgb.g - rgb.g;
        const db = c.rgb.b - rgb.b;
        const brightness = (c.rgb.r * 299 + c.rgb.g * 587 + c.rgb.b * 114) / 1000;
        let score = dr * dr + dg * dg + db * db;
        if (opts.light && brightness < 180) score += 50000;
        if (opts.dark && brightness > 190) score += 40000;
        if (score < bestScore) {
          bestScore = score;
          best = c;
        }
      }
      return best?.value || 'auto';
    }

    async function dominantColorFromImage(url) {
      return new Promise((resolve) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
          try {
            const canvas = document.createElement('canvas');
            const size = 48;
            canvas.width = size;
            canvas.height = size;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, size, size);
            const data = ctx.getImageData(0, 0, size, size).data;
            let r = 0, g = 0, b = 0, count = 0;
            for (let i = 0; i < data.length; i += 16) {
              const alpha = data[i + 3];
              if (alpha < 80) continue;
              const rr = data[i], gg = data[i + 1], bb = data[i + 2];
              const brightness = (rr * 299 + gg * 587 + bb * 114) / 1000;
              if (brightness > 245 || brightness < 18) continue;
              r += rr; g += gg; b += bb; count++;
            }
            resolve(count ? { r: Math.round(r / count), g: Math.round(g / count), b: Math.round(b / count) } : null);
          } catch (e) {
            resolve(null);
          }
        };
        img.onerror = () => resolve(null);
        img.src = url;
      });
    }

    async function applyVisualLayerColorsFromAsset(asset) {
      if (!asset?.url || !['global_bg', 'hero_bg', 'main_wordart', 'subtitle_wordart'].includes(asset.asset_type)) return;
      const rgb = await dominantColorFromImage(asset.url);
      if (!rgb) return;
      const accent = nearestModuleColor(rgb);
      const fill = nearestModuleColor(rgb, { light: true });
      const border = nearestModuleColor(rgb, { dark: true });
      (posterStrategy.value?.module_plan || []).forEach(m => {
        if (isTitleVisualModule(m) || isLogoVisualModule(m)) return;
        m.module_config = m.module_config || {};
        m.module_config.underline_color = accent;
        m.module_config.panel_border = border;
        m.module_config.panel_fill = fill;
        if (!m.module_config.text_color || m.module_config.text_color === 'auto') {
          m.module_config.text_color = '#111827';
        }
      });
    }

    function moduleTypeCodeLabel(m) {
      const code = moduleMCode(m);
      if ([11, 12, 13].includes(code)) return 'M13';
      if (code) return `M${code}`;
      const key = String(m?.script_key || '');
      const tm = key.match(/^module\.tm(\d+)/);
      if (tm) return `TM${tm[1]}`;
      if (key === 'module.tm1_tm13_visual_layer') return 'TM1-TM13';
      return m?.id || '';
    }

    function moduleComponentLabel(m) {
      const key = m?.component || m?.capability?.renderer || '';
      return COMPONENT_LABELS[key] || COMPONENT_LABELS[m?.capability?.renderer] || '自定义规格';
    }

    function moduleMetaText(m) {
      const purpose = m?.purpose || m?.capability?.notes || '补充本张海报需要的信息';
      return `${purpose} · ${moduleComponentLabel(m)}`;
    }

    function structuredModuleRenderer(m) {
      return m?.capability?.renderer || m?.component || '';
    }

    function specialModuleKind(m) {
      const key = m?.script_key || '';
      const renderer = structuredModuleRenderer(m);
      const mCode = moduleMCode(m);
      if ([1, 2, 3, 4, 14, 15].includes(mCode) || renderer === 'spec_text_panel') return 'text_panel';
      if (mCode === 5) return 'table';
      if ([6, 8, 25].includes(mCode)) return 'image_text';
      if ([7, 9].includes(mCode)) return 'feedback_flow';
      if ([10, 16, 17, 18].includes(mCode)) return 'course_list';
      if ([11, 12, 13].includes(mCode)) return 'faculty_lineup';
      if (mCode === 19) return 'rating_bars';
      if ([20, 21].includes(mCode)) return 'image_grid';
      if ([22, 23].includes(mCode)) return 'action_bar';
      if (mCode === 24) return 'contact_text';
      if (key === 'module.faculty_grid' || key === 'module.guest_profile_deep' || renderer === 'faculty_grid' || renderer === 'spec_avatar_group_wall') return 'faculty_lineup';
      if (renderer === 'spec_course_card_list') return 'course_list';
      if (renderer === 'spec_feedback_story_flow') return 'feedback_flow';
      if (renderer === 'spec_rating_bars') return 'rating_bars';
      if (renderer === 'spec_quote_cards') return 'quote_cards';
      if (renderer === 'spec_image_grid') return 'image_grid';
      if (renderer === 'spec_image_text_split') return 'image_text';
      if (renderer === 'spec_action_bar' || renderer === 'cta_button' || key.endsWith('_cta')) return 'action_bar';
      if (renderer === 'qa_block') return 'qa_block';
      if (renderer === 'curriculum_timeline') return 'timeline';
      if (renderer === 'data_table' || renderer === 'complex_table' || key === 'module.agenda_table') return 'table';
      return '';
    }

    function isStructuredModule(m) {
      return !isTitleVisualModule(m) && !isLogoVisualModule(m)
        && (STRUCTURED_RENDERERS.has(structuredModuleRenderer(m)) || !!specialModuleKind(m));
    }

    function ensureStructuredModuleConfig(module) {
      if (!module || !module.module_config || !isStructuredModule(module)) return;
      const cfg = module.module_config;
      const kind = specialModuleKind(module);
      const mCode = moduleMCode(module);
      cfg.structured_enabled = cfg.structured_enabled !== false;
      cfg.layout = cfg.layout || 'left_image_right_text';
      cfg.actions = Array.isArray(cfg.actions) ? cfg.actions : [];
      cfg.font_size = Number(cfg.font_size || 32);
      cfg.font_family = cfg.font_family || 'default';
      cfg.font_weight = cfg.font_weight || 'regular';
      cfg.font_style = cfg.font_style || 'normal';
      cfg.text_decoration = cfg.text_decoration || 'none';
      cfg.text_align = cfg.text_align || 'left';
      cfg.line_height = Number(cfg.line_height || 1.45);
      cfg.paragraph_spacing = Number(cfg.paragraph_spacing || 18);
      cfg.text_color = cfg.text_color || 'auto';
      cfg.highlight_color = cfg.highlight_color || '#FBBF24';
      if (mCode === 4 || kind === 'plain_text') {
        cfg.title_enabled = false;
        cfg.panel_fill = 'transparent';
        cfg.panel_border = 'transparent';
      }
      if (kind === 'faculty_lineup') {
        cfg.faculty_mode = cfg.faculty_mode || 'mixed';
        cfg.submodules = Array.isArray(cfg.submodules) && cfg.submodules.length ? cfg.submodules : [
          { title: '讲师/嘉宾分组', columns: 5, items: [{ name: '讲师姓名', org: '头衔/职位', avatar: '' }] },
        ];
        cfg.speaker = cfg.speaker || {
          name: '讲师姓名',
          title: '头衔/职务',
          avatar: '',
          sections: [
            { title: '经历背景', text: '' },
            { title: '研究方向', text: '' },
            { title: '课程亮点', text: '' },
          ],
        };
      } else if (kind === 'course_list') {
        cfg.items = Array.isArray(cfg.items) && cfg.items.length ? cfg.items : [
          { title: mCode === 10 ? '讲师姓名' : '课程/讲师标题', layout: mCode === 17 ? 'top_image_bottom_text' : 'left_image_right_text', text: '这里填写课程介绍、讲师介绍或模块说明', image: '', actions: [] },
        ];
      } else if (kind === 'feedback_flow') {
        cfg.submodules = Array.isArray(cfg.submodules) && cfg.submodules.length ? cfg.submodules : [
          { title: '课程评分', layout_form: 'rating_bars', items: [{ label: '课程满意度', score: 4.8, max: 5 }] },
          { title: '学员之声', layout_form: 'image_text_split', layout: 'right_image_left_text', text: '这里填写原文学员反馈、课程亮点或现场记录', image: '', actions: [] },
        ];
      } else if (kind === 'rating_bars') {
        cfg.items = Array.isArray(cfg.items) && cfg.items.length ? cfg.items : [
          { label: '评分项', score: 4.8, max: 5 },
        ];
      } else if (kind === 'quote_cards') {
        cfg.items = Array.isArray(cfg.items) && cfg.items.length ? cfg.items : [
          { text: '这里填写原文反馈', author: '反馈人' },
        ];
      } else if (kind === 'image_grid') {
        cfg.columns = cfg.columns || (mCode === 20 ? 1 : 3);
        cfg.aspect_ratio = cfg.aspect_ratio || 0.66;
      } else if (['text_panel', 'plain_text', 'contact_text'].includes(kind)) {
        cfg.subsections = Array.isArray(cfg.subsections) ? cfg.subsections : (
          [3, 15].includes(mCode) ? [{ title: '', text: '' }] : []
        );
        cfg.list_items = Array.isArray(cfg.list_items) ? cfg.list_items : (
          [14, 15].includes(mCode) ? ['姓名 / 部门 / 说明'] : []
        );
      } else if (kind === 'qa_block') {
        cfg.items = Array.isArray(cfg.items) && cfg.items.length ? cfg.items : [
          { q: '问题', a: '回答' },
        ];
      } else if (kind === 'timeline') {
        cfg.parts = Array.isArray(cfg.parts) && cfg.parts.length ? cfg.parts : [
          { label: 'Part 1', time: '', format: '', topic: '阶段主题', output: '' },
        ];
      } else if (kind === 'table') {
        cfg.headers = Array.isArray(cfg.headers) && cfg.headers.length ? cfg.headers : ['时间', '内容', '形式'];
        cfg.rows = Array.isArray(cfg.rows) && cfg.rows.length ? cfg.rows : [['', '', '']];
      } else if (kind === 'action_bar') {
        cfg.actions = cfg.actions.length ? cfg.actions : [{ text: '立即报名', hint: '', color: '' }];
      }
    }

    function textEditorStyle(cfg) {
      const color = cfg?.text_color && cfg.text_color !== 'auto' ? cfg.text_color : '#111827';
      const hex = /^#([0-9a-f]{6})$/i.test(color) ? color.slice(1) : '';
      const isLight = hex ? (
        (parseInt(hex.slice(0, 2), 16) * 299
          + parseInt(hex.slice(2, 4), 16) * 587
          + parseInt(hex.slice(4, 6), 16) * 114) / 1000 > 185
      ) : false;
      const align = cfg?.text_align || 'left';
      const fontSize = Number(cfg?.font_size || 32);
      const lineHeight = Number(cfg?.line_height || 1.45);
      const weight = cfg?.font_weight === 'bold' ? 700 : 400;
      const style = cfg?.font_style === 'italic' ? 'italic' : 'normal';
      const decoration = cfg?.text_decoration === 'underline' ? 'underline' : 'none';
      const familyMap = {
        default: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif',
        pingfang: '"PingFang SC", -apple-system, BlinkMacSystemFont, sans-serif',
        source_han_sans: '"Source Han Sans SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif',
        inter: 'Inter, "SF Pro Text", -apple-system, BlinkMacSystemFont, sans-serif',
      };
      return {
        color,
        textAlign: align,
        fontSize: `${Math.max(18, Math.min(72, fontSize))}px`,
        lineHeight,
        fontWeight: weight,
        fontStyle: style,
        textDecoration: decoration,
        fontFamily: familyMap[cfg?.font_family] || familyMap.default,
        backgroundColor: isLight ? '#111827' : '#FFFFFF',
        borderColor: isLight ? 'rgba(255,255,255,0.24)' : 'rgba(37,99,235,0.18)',
      };
    }

    function subTitleEditorStyle(cfg) {
      return {
        ...textEditorStyle(cfg),
        fontSize: '22px',
        lineHeight: 1.25,
        fontWeight: 700,
        backgroundColor: '#FFFFFF',
      };
    }

    function escapeHtmlText(value) {
      return String(value ?? '').replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
      }[ch]));
    }

    function normalizeRichColor(value, fallback = '') {
      const v = String(value || '').trim();
      if (!v || v === 'auto') return fallback;
      if (/^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(v)) return v;
      if (/^rgba?\(/i.test(v)) return v;
      if (v.toLowerCase() === 'transparent') return 'transparent';
      return fallback;
    }

    function currentRichFieldJsonName(key) {
      return key ? `${key}_editor_json` : 'editor_json';
    }

    function richAssetUrl(pathOrUrl) {
      const raw = String(pathOrUrl || '').trim();
      if (!raw) return '';
      if (/^(https?:|data:image\/|\/api\/|\/static\/)/i.test(raw)) return raw;
      return '/api/skill-asset?path=' + encodeURIComponent(raw);
    }

    function normalizePosterImageAttrs(attrs = {}) {
      const path = attrs.path || attrs['data-asset-path'] || '';
      const src = attrs.src || attrs.url || richAssetUrl(path);
      let widthPct = Number(attrs.widthPct ?? attrs.width_pct ?? attrs['data-width-pct'] ?? 0.32);
      if (!Number.isFinite(widthPct)) widthPct = 0.32;
      // FIX: 问题2 - 历史 HTML/JSON 中的图片宽度可能保存成 1，重新进入时统一收敛，避免旧图撑满编辑器。
      widthPct = Math.max(0.08, Math.min(0.48, widthPct));
      const align = ['left', 'center', 'right'].includes(attrs.align) ? attrs.align : 'center';
      return { src, path, alt: attrs.alt || '', widthPct, align };
    }

    function collectImagesFromEditorJson(json) {
      const out = [];
      function walk(node) {
        if (!node || typeof node !== 'object') return;
        if (node.type === 'posterImage' || node.type === 'image') {
          const a = normalizePosterImageAttrs(node.attrs || {});
          const path = a.path || '';
          const src = a.src || richAssetUrl(path);
          if (path || src) {
            out.push({
              name: a.alt || (path ? path.split('/').pop() : '正文图片'),
              path,
              url: src,
              width_pct: a.widthPct,
              align: a.align || 'center',
              asset_type: 'module_content_image',
              asset_label: '正文内嵌图片',
            });
          }
        }
        (node.content || []).forEach(walk);
      }
      walk(json);
      return out;
    }

    function legacyHtmlToEditorJson(html = '', fallbackText = '') {
      const doc = { type: 'doc', content: [] };
      const root = document.createElement('div');
      root.innerHTML = html || '';
      function markAttrsFromElement(el, inherited = []) {
        const marks = inherited.slice();
        if (!el || el.nodeType !== 1) return marks;
        const tag = el.tagName.toLowerCase();
        const style = el.style || {};
        if (tag === 'strong' || tag === 'b' || /bold|700|800|900/.test(style.fontWeight || '')) marks.push({ type: 'bold' });
        if (tag === 'em' || tag === 'i' || style.fontStyle === 'italic') marks.push({ type: 'italic' });
        if (tag === 'u' || /underline/.test(style.textDecoration || '')) marks.push({ type: 'underline' });
        const textStyle = {};
        if (style.color) textStyle.color = style.color;
        if (style.fontSize) textStyle.fontSize = style.fontSize;
        if (style.fontFamily) textStyle.fontFamily = style.fontFamily;
        if (Object.keys(textStyle).length) marks.push({ type: 'textStyle', attrs: textStyle });
        if (style.backgroundColor && style.backgroundColor !== 'transparent') marks.push({ type: 'highlight', attrs: { color: style.backgroundColor } });
        return marks;
      }
      function inlineNodes(node, inheritedMarks = []) {
        const nodes = [];
        if (node.nodeType === 3) {
          const text = node.textContent || '';
          if (text) nodes.push({ type: 'text', text, ...(inheritedMarks.length ? { marks: inheritedMarks } : {}) });
          return nodes;
        }
        if (node.nodeType !== 1) return nodes;
        const el = node;
        const tag = el.tagName.toLowerCase();
        if (tag === 'br') return [{ type: 'hardBreak' }];
        if (el.classList?.contains('rich-image-resizer')) return [];
        const marks = markAttrsFromElement(el, inheritedMarks);
        el.childNodes.forEach(child => nodes.push(...inlineNodes(child, marks)));
        return nodes;
      }
      function imageNodeFromElement(el) {
        const img = el.matches?.('img') ? el : el.querySelector?.('img');
        const path = el.dataset?.assetPath || img?.dataset?.assetPath || img?.getAttribute?.('data-asset-path') || '';
        const src = img?.getAttribute?.('src') || richAssetUrl(path);
        if (!path && !src) return null;
        // FIX: 问题2 - HTML 回退解析图片时保留 data-width-pct，避免重新进入后按原图尺寸撑大。
        let widthPct = Number(
          el.getAttribute?.('data-width-pct')
          || el.dataset?.widthPct
          || img?.getAttribute?.('data-width-pct')
          || img?.dataset?.widthPct
          || 0.32
        );
        const w = parseFloat(el.style?.width || img?.style?.width || '');
        if (String(el.style?.width || '').includes('%')) widthPct = parseFloat(el.style.width) / 100;
        else if (w && root.clientWidth) widthPct = Math.max(0.08, Math.min(1, w / root.clientWidth));
        const align = el.dataset?.align || el.getAttribute?.('data-align') || 'center';
        return { type: 'posterImage', attrs: normalizePosterImageAttrs({ src, path, alt: img?.alt || '', widthPct, align }) };
      }
      function blockFromNode(node) {
        if (node.nodeType === 3) {
          const text = node.textContent || '';
          if (text.trim()) return { type: 'paragraph', content: [{ type: 'text', text }] };
          return null;
        }
        if (node.nodeType !== 1) return null;
        const el = node;
        if (el.classList?.contains('rich-image-resizer') || el.matches?.('img')) return imageNodeFromElement(el);
        const tag = el.tagName.toLowerCase();
        const align = el.style?.textAlign || el.getAttribute('align') || null;
        if (['p', 'div', 'section', 'article', 'li', 'h1', 'h2', 'h3', 'h4'].includes(tag)) {
          const content = [];
          el.childNodes.forEach(child => {
            if (child.nodeType === 1 && (child.classList?.contains('rich-image-resizer') || child.matches?.('img'))) {
              const existing = content.filter(n => n.type !== 'hardBreak');
              if (existing.length) doc.content.push({ type: 'paragraph', attrs: align ? { textAlign: align } : {}, content: existing });
              content.length = 0;
              const img = imageNodeFromElement(child);
              if (img) doc.content.push(img);
            } else {
              content.push(...inlineNodes(child, []));
            }
          });
          const clean = content.filter(n => n.type !== 'hardBreak' || content.length > 1);
          if (clean.length) return { type: 'paragraph', attrs: align ? { textAlign: align } : {}, content: clean };
          return null;
        }
        const content = inlineNodes(el, []);
        return content.length ? { type: 'paragraph', content } : null;
      }
      root.childNodes.forEach(node => {
        const b = blockFromNode(node);
        if (b) doc.content.push(b);
      });
      if (!doc.content.length && fallbackText) {
        doc.content = String(fallbackText).split(/\n+/).filter(Boolean).map(t => ({ type: 'paragraph', content: [{ type: 'text', text: t }] }));
      }
      if (!doc.content.length) doc.content = [{ type: 'paragraph' }];
      return doc;
    }

    function editorJsonToPlainText(json) {
      const parts = [];
      function walk(node) {
        if (!node || typeof node !== 'object') return;
        if (node.type === 'text') parts.push(node.text || '');
        if (node.type === 'hardBreak') parts.push('\n');
        if (node.type === 'paragraph' && parts.length && !String(parts[parts.length - 1]).endsWith('\n')) parts.push('\n');
        (node.content || []).forEach(walk);
        if (node.type === 'paragraph' && parts.length && !String(parts[parts.length - 1]).endsWith('\n')) parts.push('\n');
        if (node.type === 'posterImage' || node.type === 'image') parts.push('[图片]\n');
      }
      walk(json);
      return parts.join('').replace(/\n{3,}/g, '\n\n').trim();
    }

    function mergeRichEditorImages(target, editorOrJson) {
      if (!target || typeof target !== 'object') return;
      let inlineImages = [];
      if (editorOrJson?.getJSON) inlineImages = collectImagesFromEditorJson(editorOrJson.getJSON());
      else if (editorOrJson?.type === 'doc') inlineImages = collectImagesFromEditorJson(editorOrJson);
      else if (editorOrJson?.querySelectorAll) inlineImages = collectRichEditorImages(editorOrJson);
      if (!inlineImages.length) return;
      target.images = Array.isArray(target.images) ? target.images : [];
      for (const item of inlineImages) {
        const idx = target.images.findIndex(x => x && x.path === item.path && item.path);
        if (idx >= 0) target.images.splice(idx, 1, { ...target.images[idx], ...item });
        else target.images.push(item);
      }
      if (!target.image && inlineImages[0]?.path) target.image = inlineImages[0].path;
    }

    function collectRichEditorImages(editor) {
      if (!editor) return [];
      return Array.from(editor.querySelectorAll('.rich-image-resizer[data-asset-path], .rich-tiptap-image-node[data-asset-path]'))
        .map((node, idx) => {
          const img = node.querySelector('img');
          const path = node.dataset.assetPath || '';
          if (!path) return null;
          return {
            name: img?.alt || path.split('/').pop() || ('正文图片' + (idx + 1)),
            path,
            url: img?.getAttribute('src') || '',
            width: node.style.width || '',
            width_pct: editor.clientWidth ? Math.max(0.08, Math.min(1, node.offsetWidth / editor.clientWidth)) : Number(node.dataset.widthPct || 0.55),
            align: node.dataset.align || 'center',
            asset_type: 'module_content_image',
            asset_label: '正文内嵌图片',
          };
        })
        .filter(Boolean);
    }

    function normalizeEditorJsonImages(json) {
      function walk(node) {
        if (!node || typeof node !== 'object') return node;
        if (node.type === 'posterImage' || node.type === 'image') node.attrs = normalizePosterImageAttrs(node.attrs || {});
        if (Array.isArray(node.content)) node.content = node.content.map(walk);
        return node;
      }
      const cloned = walk(JSON.parse(JSON.stringify(json || { type: 'doc', content: [{ type: 'paragraph' }] })));
      if (cloned?.type === 'doc' && Array.isArray(cloned.content)) {
        const deduped = [];
        let lastImageKey = '';
        cloned.content.forEach(node => {
          const normalized = (
            node?.type === 'posterImage' || node?.type === 'image'
              ? { type: 'paragraph', content: [node, { type: 'text', text: ' ' }] }
              : node
          );
          // FIX: 问题2 - 兜底去重，避免旧 JSON/HTML 双来源造成相邻重复图片。
          const first = normalized?.content?.find?.(x => x?.type === 'posterImage' || x?.type === 'image');
          const imageKey = first ? (first.attrs?.path || first.attrs?.src || '') : '';
          if (imageKey && imageKey === lastImageKey) return;
          deduped.push(normalized);
          lastImageKey = imageKey || '';
        });
        cloned.content = deduped;
      }
      return cloned;
    }

    function getTiptapContext(editor) {
      return editor?.options?.editorProps?.richContext || editor?.__richContext || null;
    }

    function syncTiptapEditorData(editor) {
      if (!editor || editor.isDestroyed) return;
      const ctx = getTiptapContext(editor);
      if (!ctx?.target || !ctx.key) return;
      const json = normalizeEditorJsonImages(editor.getJSON());
      const html = editor.getHTML();
      const text = editor.getText('\n');
      // FIX: 问题5 - 按当前编辑器的 key 独立保存，主内容 content 与子模块 title/text 不互相覆盖。
      ctx.target[ctx.key] = text;
      ctx.target[`${ctx.key}_html`] = html;
      ctx.target[currentRichFieldJsonName(ctx.key)] = json;
      if (ctx.key === 'content') {
        ctx.target.editor_json = json;
        ctx.target.content_editor_json = json;
      }
      mergeRichEditorImages(ctx.target, json);
      markPosterPreviewDirty();
    }

    function activeTiptapEditor() {
      // FIX: 问题1/4 - 工具栏输入框会夺走焦点，不能只依赖 document.activeElement；
      // 从浮动工具栏记录、当前 ProseMirror focus、宿主 DOM 三路恢复真实 TipTap 实例。
      const hostFromFloating = floatingRich.editor?.closest?.('.rich-editor.tiptap-host') || floatingRich.editor || null;
      const hostFromFocus = document.activeElement?.closest?.('.rich-editor.tiptap-host') || null;
      const hostFromPm = document.querySelector('.rich-editor.tiptap-host .ProseMirror-focused')?.closest?.('.rich-editor.tiptap-host') || null;
      const editor =
        (hostFromFloating ? tiptapEditors.get(hostFromFloating) : null) ||
        (hostFromFocus ? tiptapEditors.get(hostFromFocus) : null) ||
        (hostFromPm ? tiptapEditors.get(hostFromPm) : null) ||
        floatingRich.tiptapEditor ||
        null;
      if (editor && !editor.isDestroyed) {
        floatingRich.tiptapEditor = editor;
        const ctx = getTiptapContext(editor);
        if (ctx?.el) floatingRich.editor = ctx.el;
        return editor;
      }
      return null;
    }

    function createPosterImageExtension(T) {
      return T.Node.create({
        name: 'posterImage',
        // FIX: 问题3 - 图片必须是 inline node，才能放在文字之间、一行多图混排。
        group: 'inline',
        inline: true,
        atom: true,
        selectable: true,
        draggable: true,
        addAttributes() {
          return {
            src: {
              default: '',
              parseHTML: el => el.getAttribute('src') || el.querySelector?.('img')?.getAttribute('src') || '',
            },
            path: {
              default: '',
              parseHTML: el => el.getAttribute('data-asset-path') || el.querySelector?.('img')?.getAttribute('data-asset-path') || '',
            },
            alt: {
              default: '',
              parseHTML: el => el.getAttribute('alt') || el.querySelector?.('img')?.getAttribute('alt') || '',
            },
            widthPct: {
              default: 0.32,
              parseHTML: el => Number(el.getAttribute('data-width-pct') || el.dataset?.widthPct || 0.32),
            },
            align: {
              default: 'center',
              parseHTML: el => el.getAttribute('data-align') || el.dataset?.align || 'center',
            },
          };
        },
        parseHTML() {
          return [
            { tag: 'span[data-type="poster-image"]' },
            { tag: 'span.rich-image-resizer' },
            { tag: 'img[data-asset-path]' },
          ];
        },
        renderHTML({ node }) {
          const a = normalizePosterImageAttrs(node.attrs || {});
          const style = `width:${Math.round((Number(a.widthPct) || 0.32) * 100)}%;vertical-align:middle;`;
          return ['span', { 'data-type': 'poster-image', 'data-asset-path': a.path || '', 'data-width-pct': a.widthPct || 0.32, 'data-align': a.align || 'center', style }, ['img', { src: a.src || richAssetUrl(a.path), alt: a.alt || '', 'data-asset-path': a.path || '' }]];
        },
        addNodeView() {
          return ({ node, editor, getPos }) => {
            let attrs = normalizePosterImageAttrs(node.attrs || {});
            const dom = document.createElement('span');
            dom.className = 'rich-image-resizer rich-tiptap-image-node';
            dom.contentEditable = 'false';
            dom.tabIndex = 0;
            dom.dataset.assetPath = attrs.path || '';
            dom.dataset.align = attrs.align || 'center';
            dom.dataset.widthPct = String(attrs.widthPct || 0.32);
            dom.dataset.type = 'poster-image';
            const img = document.createElement('img');
            img.draggable = false;
            img.src = attrs.src || richAssetUrl(attrs.path);
            img.alt = attrs.alt || 'inline image';
            dom.appendChild(img);

            const toolbar = document.createElement('div');
            toolbar.className = 'rich-image-mini-toolbar';
            [['left', '左'], ['center', '中'], ['right', '右']].forEach(([align, label]) => {
              const b = document.createElement('button');
              b.type = 'button'; b.textContent = label; b.title = `${label}对齐`;
              b.addEventListener('mousedown', e => { e.preventDefault(); e.stopPropagation(); updateAttrs({ align }); });
              toolbar.appendChild(b);
            });
            const del = document.createElement('button');
            del.type = 'button'; del.textContent = '删'; del.title = '删除图片';
            del.addEventListener('mousedown', e => { e.preventDefault(); e.stopPropagation(); deleteNode(); });
            toolbar.appendChild(del);
            dom.appendChild(toolbar);

            ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'].forEach(dir => {
              const h = document.createElement('span');
              h.className = `rich-image-handle rich-image-handle-${dir}`;
              h.dataset.dir = dir;
              h.addEventListener('pointerdown', startResize);
              dom.appendChild(h);
            });

            function applyAttrsToDom() {
              const pct = Math.max(0.08, Math.min(1, Number(attrs.widthPct || 0.32)));
              dom.style.width = `${Math.round(pct * 10000) / 100}%`;
              dom.dataset.widthPct = String(pct);
              dom.dataset.align = attrs.align || 'center';
              dom.style.marginLeft = attrs.align === 'left' ? '0' : '6px';
              dom.style.marginRight = attrs.align === 'right' ? '0' : '6px';
              img.src = attrs.src || richAssetUrl(attrs.path);
              img.alt = attrs.alt || 'inline image';
              if (attrs.path) dom.dataset.assetPath = attrs.path;
            }

            function updateAttrs(next) {
              attrs = normalizePosterImageAttrs({ ...attrs, ...next });
              applyAttrsToDom();
              if (typeof getPos === 'function') {
                editor.commands.command(({ tr, dispatch }) => {
                  const pos = getPos();
                  if (typeof pos !== 'number') return false;
                  if (dispatch) dispatch(tr.setNodeMarkup(pos, undefined, attrs));
                  return true;
                });
              }
              syncTiptapEditorData(editor);
            }

            function deleteNode() {
              if (typeof getPos !== 'function') return;
              editor.commands.command(({ tr, dispatch }) => {
                const pos = getPos();
                if (typeof pos !== 'number') return false;
                if (dispatch) dispatch(tr.delete(pos, pos + node.nodeSize));
                return true;
              });
              syncTiptapEditorData(editor);
            }

            function startResize(event) {
              event.preventDefault(); event.stopPropagation();
              dom.classList.add('selected', 'resizing');
              const dir = event.currentTarget.dataset.dir || 'se';
              const editorEl = dom.closest('.rich-editor');
              const maxW = Math.max(120, editorEl?.clientWidth || dom.parentElement?.clientWidth || 720);
              const startX = event.clientX, startY = event.clientY;
              const startW = dom.getBoundingClientRect().width;
              const imgRect = img.getBoundingClientRect();
              const ratio = imgRect.width && imgRect.height ? imgRect.width / imgRect.height : 1.6;
              const minW = Math.min(120, maxW * 0.2);
              const onMove = ev => {
                const dx = ev.clientX - startX;
                const dy = ev.clientY - startY;
                let delta = 0;
                if (dir.includes('e')) delta += dx;
                if (dir.includes('w')) delta -= dx;
                if (dir.includes('s')) delta += dy * ratio;
                if (dir.includes('n')) delta -= dy * ratio;
                if (dir.length === 2) delta = delta / 1.35;
                const nextW = Math.max(minW, Math.min(maxW, startW + delta));
                const pct = Math.max(0.08, Math.min(1, nextW / maxW));
                attrs.widthPct = pct;
                dom.style.width = `${Math.round(pct * 10000) / 100}%`;
                dom.dataset.widthPct = String(pct);
              };
              const onUp = () => {
                document.removeEventListener('pointermove', onMove);
                document.removeEventListener('pointerup', onUp);
                dom.classList.remove('resizing');
                updateAttrs({ widthPct: attrs.widthPct });
              };
              document.addEventListener('pointermove', onMove);
              document.addEventListener('pointerup', onUp, { once: true });
            }

            dom.__deleteNode = deleteNode;
            dom.addEventListener('mousedown', e => { e.stopPropagation(); selectRichImage(dom); floatingRich.editor = dom.closest('.rich-editor'); floatingRich.tiptapEditor = editor; });
            dom.addEventListener('keydown', e => { if (['Backspace', 'Delete'].includes(e.key)) { e.preventDefault(); deleteNode(); } });
            applyAttrsToDom();
            return {
              dom,
              selectNode() { dom.classList.add('selected'); },
              deselectNode() { dom.classList.remove('selected'); },
              update(updatedNode) { attrs = normalizePosterImageAttrs(updatedNode.attrs || {}); applyAttrsToDom(); return updatedNode.type.name === 'posterImage'; },
              destroy() {},
            };
          };
        },
      });
    }

    function tiptapExtensions(T) {
      if (tiptapExtensionsCache) return tiptapExtensionsCache;
      // FIX: 问题1 - TextStyle 的 global attributes 不会稳定渲染到 DOM，直接扩展 TextStyle 输出 style。
      const CustomTextStyle = T.TextStyle.extend({
        addAttributes() {
          return {
            ...this.parent?.(),
            fontSize: {
              default: null,
              parseHTML: element => element.style.fontSize || null,
              renderHTML: attributes => {
                if (!attributes.fontSize) return {};
                return { style: `font-size: ${attributes.fontSize}` };
              },
            },
            fontFamily: {
              default: null,
              parseHTML: element => element.style.fontFamily || null,
              renderHTML: attributes => {
                if (!attributes.fontFamily) return {};
                return { style: `font-family: ${attributes.fontFamily}` };
              },
            },
          };
        },
      });
      tiptapExtensionsCache = [
        T.StarterKit,
        T.Underline,
        CustomTextStyle,
        T.Color.configure({ types: ['textStyle'] }),
        T.Highlight.configure({ multicolor: true }),
        T.TextAlign.configure({ types: ['heading', 'paragraph'] }),
        createPosterImageExtension(T),
      ];
      return tiptapExtensionsCache;
    }

    function initialTiptapContent(target, key) {
      // FIX: 问题2 - 初始化只使用一个来源；JSON 存在时不再混合 HTML 回退，避免图片重复。
      const json = target?.[currentRichFieldJsonName(key)] || (key === 'content' ? (target?.editor_json || target?.content_editor_json) : null);
      if (json && typeof json === 'object' && json.type === 'doc') return normalizeEditorJsonImages(json);
      const html = target?.[`${key}_html`] || '';
      const text = target?.[key] || '';
      return legacyHtmlToEditorJson(html, text);
    }

    function refreshMountedTiptapEditorsFromData() {
      // FIX: 问题4 - 外部整体替换 brief 后手动同步一次，不使用 watch，避免输入循环和光标跳动。
      tiptapEditorEls.forEach(el => {
        const editor = tiptapEditors.get(el);
        const ctx = editor && !editor.isDestroyed ? getTiptapContext(editor) : null;
        if (!editor || !ctx?.target || !ctx.key) return;
        const next = initialTiptapContent(ctx.target, ctx.key);
        try {
          const current = JSON.stringify(normalizeEditorJsonImages(editor.getJSON()));
          const incoming = JSON.stringify(normalizeEditorJsonImages(next));
          if (current !== incoming) editor.commands.setContent(next, false);
        } catch (e) {
          editor.commands.setContent(next, false);
        }
      });
    }

    function flushAllTiptapEditorsToData() {
      // FIX: 问题3/4 - 保存、生成、预览前把所有独立 TipTap 实例写回各自 target/key，避免主模块和子模块互相覆盖或丢失。
      tiptapEditorEls.forEach(el => {
        const editor = tiptapEditors.get(el);
        if (!editor || editor.isDestroyed) return;
        syncTiptapEditorData(editor);
      });
    }

    async function ensureTiptapEditor(el, target, key, slot = 'body') {
      if (!el || !target || !key) return null;
      const existing = tiptapEditors.get(el);
      if (existing) {
        existing.__richContext = { target, key, slot, el };
        if (existing.options?.editorProps) existing.options.editorProps.richContext = existing.__richContext;
        if (typeof existing.peUpdateContext === 'function') existing.peUpdateContext(existing.__richContext);
        if (typeof existing.peSetExternalContent === 'function' && (el.__richBoundTarget !== target || el.__richBoundKey !== key)) {
          existing.peSetExternalContent(target, key);
        }
        return existing;
      }

      const context = { target, key, slot, el };
      if (window.IEG_POSTER_EDITOR_ISOLATED?.create) {
        // FIX: 新编辑器隔离 - legacy 只负责传入 target/key，不再实例化旧扩展，避免全局 Tiptap 原型污染和旧 .ProseMirror CSS 影响。
        const isolatedEditor = window.IEG_POSTER_EDITOR_ISOLATED.create({
          el,
          target,
          key,
          slot,
          onUpdate(editor) { syncTiptapEditorData(editor); },
          onFocus(editor) {
            floatingRich.editor = el;
            floatingRich.tiptapEditor = editor;
            floatingRich.tiptapSelection = { from: editor.state.selection.from, to: editor.state.selection.to };
            positionFloatingRichToolbar();
          },
          onSelectionUpdate(editor) {
            floatingRich.editor = el;
            floatingRich.tiptapEditor = editor;
            floatingRich.tiptapSelection = { from: editor.state.selection.from, to: editor.state.selection.to };
            positionFloatingRichToolbar();
          },
        });
        if (isolatedEditor) {
          isolatedEditor.__richContext = context;
          tiptapEditors.set(el, isolatedEditor);
          tiptapEditorEls.add(el);
          el.__tiptapEditor = isolatedEditor;
          el.__richBoundTarget = target;
          el.__richBoundKey = key;
          el.__richBoundSlot = slot;
          return isolatedEditor;
        }
      }

      let T = null;
      try {
        T = await (window.TIPTAP_READY || Promise.resolve(null));
      } catch (e) { T = null; }
      if (!T?.Editor) return null;
      // Fallback only: kept for startup resilience if isolated runtime fails to load.
      el.innerHTML = '';
      const editor = new T.Editor({
        element: el,
        extensions: tiptapExtensions(T),
        content: initialTiptapContent(target, key),
        editorProps: {
          richContext: context,
          attributes: { class: 'tiptap-prosemirror-content' },
          handlePaste(view, event) {
            const files = Array.from(event.clipboardData?.files || []).filter(f => /^image\//.test(f.type));
            if (!files.length) return false;
            event.preventDefault();
            uploadImageFilesIntoTiptap(files, editor);
            return true;
          },
        },
        onCreate({ editor }) { syncTiptapEditorData(editor); },
        onUpdate({ editor }) { syncTiptapEditorData(editor); },
        onFocus({ editor }) { floatingRich.editor = el; floatingRich.tiptapEditor = editor; floatingRich.tiptapSelection = { from: editor.state.selection.from, to: editor.state.selection.to }; positionFloatingRichToolbar(); },
        onSelectionUpdate({ editor }) { floatingRich.editor = el; floatingRich.tiptapEditor = editor; floatingRich.tiptapSelection = { from: editor.state.selection.from, to: editor.state.selection.to }; positionFloatingRichToolbar(); },
      });
      editor.__richContext = context;
      tiptapEditors.set(el, editor);
      tiptapEditorEls.add(el);
      el.__tiptapEditor = editor;
      el.classList.add('tiptap-ready');
      el.setAttribute('contenteditable', 'false');
      return editor;
    }

    async function ensureBoundRichEditor(el, bindingValue) {
      // FIX: 问题1/3/4 - 每个 DOM 宿主在挂载时就绑定自己的 target/key，不再依赖点击后懒创建，避免旧 DOM 和 Vue 数据不同步。
      const target = bindingValue?.target;
      const key = bindingValue?.key;
      const slot = bindingValue?.slot || richSlotOfEditor(el);
      if (!el || !target || !key) return null;
      const existing = tiptapEditors.get(el);
      if (existing && !existing.isDestroyed) {
        const targetChanged = el.__richBoundTarget !== target || el.__richBoundKey !== key;
        existing.__richContext = { target, key, slot, el };
        existing.options.editorProps.richContext = existing.__richContext;
        if (targetChanged) {
          el.__richBoundTarget = target;
          el.__richBoundKey = key;
          el.__richBoundSlot = slot;
          existing.commands.setContent(initialTiptapContent(target, key), false);
        }
        return existing;
      }
      el.__richBoundTarget = target;
      el.__richBoundKey = key;
      el.__richBoundSlot = slot;
      return ensureTiptapEditor(el, target, key, slot);
    }

    window.__IEG_ENSURE_RICH_EDITOR__ = ensureBoundRichEditor;
    window.__IEG_FLUSH_RICH_EDITORS__ = flushAllTiptapEditorsToData;
    window.__IEG_RICH_DEBUG__ = () => {
      const editor = activeTiptapEditor();
      const ctx = editor ? getTiptapContext(editor) : null;
      return {
        hasEditor: !!editor,
        selection: floatingRich.tiptapSelection,
        slot: floatingRich.slot,
        key: ctx?.key || '',
        html: editor && !editor.isDestroyed ? editor.getHTML() : '',
        json: editor && !editor.isDestroyed ? editor.getJSON() : null,
      };
    };
    window.__IEG_RICH_APPLY__ = (command, value = null) => applyFloatingRichCommand(command, value);

    function selectRichImage(node) {
      const editorEl = node?.closest?.('.rich-editor');
      if (!editorEl) return;
      editorEl.querySelectorAll('.rich-image-resizer.selected').forEach(x => {
        if (x !== node) x.classList.remove('selected');
      });
      node.classList.add('selected');
      floatingRich.editor = editorEl;
      floatingRich.tiptapEditor = tiptapEditors.get(editorEl) || floatingRich.tiptapEditor || null;
      positionFloatingRichToolbar();
    }

    function handleRichEditorKeydown(event) {
      const editorEl = event.target?.closest?.('.rich-editor');
      if (!editorEl) return;
      if (!['Backspace', 'Delete'].includes(event.key)) return;
      const tEditor = tiptapEditors.get(editorEl);
      const selectedImg = editorEl.querySelector('.rich-image-resizer.selected, .rich-image-resizer.ProseMirror-selectednode');
      if (!selectedImg) return;
      event.preventDefault();
      if (tEditor && selectedImg.__deleteNode) selectedImg.__deleteNode();
      else { selectedImg.remove(); editorEl.dispatchEvent(new Event('input', { bubbles: true })); }
    }

    function syncEditableText(target, key, event) {
      if (!target || !key) return;
      const editorEl = event?.target?.closest?.('.rich-editor') || event?.target;
      const tEditor = editorEl ? tiptapEditors.get(editorEl) : null;
      floatingRich.target = target;
      floatingRich.key = key;
      floatingRich.editor = editorEl || floatingRich.editor;
      if (tEditor) {
        syncTiptapEditorData(tEditor);
        return;
      }
      target[key] = editorEl?.innerText || '';
      target[`${key}_html`] = editorEl?.innerHTML || '';
      const json = legacyHtmlToEditorJson(target[`${key}_html`], target[key]);
      target[currentRichFieldJsonName(key)] = json;
      if (key === 'content') {
        target.editor_json = json;
        target.content_editor_json = json;
      }
      mergeRichEditorImages(target, editorEl);
      saveRichSelection({ currentTarget: editorEl, target: editorEl });
      markPosterPreviewDirty();
    }

    function richHtml(target, key) {
      if (!target || !key) return '';
      if (key === 'title' && target[key] === '子模块小标题') return '';
      const html = target[`${key}_html`];
      if (html) return html;
      return escapeHtmlText(target[key] || '').replace(/\n/g, '<br>');
    }

    function activateRichEditor(event, target, key, slot = 'body') {
      floatingRich.target = target || null;
      floatingRich.key = key || '';
      floatingRich.slot = slot || 'body';
      const el = event?.currentTarget || event?.target || null;
      floatingRich.editor = el;
      const cfg = slot === 'title' ? {} : (target || {});
      floatingRich.font_family = cfg.font_family || floatingRich.font_family || 'default';
      floatingRich.font_size = Number(cfg.font_size || floatingRich.font_size || 24);
      floatingRich.text_color = cfg.text_color && cfg.text_color !== 'auto' ? cfg.text_color : '#111827';
      ensureTiptapEditor(el, target, key, slot).then(editor => {
        if (editor) {
          floatingRich.tiptapEditor = editor;
          editor.commands.focus();
        } else {
          saveRichSelection(event);
        }
        positionFloatingRichToolbar();
      });
      saveRichSelection(event);
      positionFloatingRichToolbar();
    }

    function richSelectionInsideEditor(range = null) {
      const editor = floatingRich.editor;
      const r = range || floatingRich.range;
      if (!editor || !r) return false;
      return editor.contains(r.startContainer) && editor.contains(r.endContainer);
    }

    function saveRichSelection(event = null) {
      const editor = event?.currentTarget || floatingRich.editor;
      if (editor) floatingRich.editor = editor;
      if (activeTiptapEditor()) { positionFloatingRichToolbar(); return; }
      const sel = window.getSelection?.();
      if (!sel || !sel.rangeCount) return;
      const range = sel.getRangeAt(0);
      if (floatingRich.editor && !richSelectionInsideEditor(range)) return;
      floatingRich.range = range.cloneRange();
      positionFloatingRichToolbar();
    }

    function restoreRichSelection() {
      if (activeTiptapEditor()) return true;
      if (!floatingRich.editor || !floatingRich.range || !richSelectionInsideEditor()) return false;
      floatingRich.editor.focus?.();
      const sel = window.getSelection?.();
      if (!sel) return false;
      sel.removeAllRanges();
      sel.addRange(floatingRich.range.cloneRange());
      return true;
    }

    function dispatchRichInput() {
      const tEditor = activeTiptapEditor();
      if (tEditor) syncTiptapEditorData(tEditor);
      const editor = floatingRich.editor || document.activeElement;
      editor?.dispatchEvent?.(new Event('input', { bubbles: true }));
      editor?.dispatchEvent?.(new Event('change', { bubbles: true }));
      markPosterPreviewDirty();
    }

    function richSelectionRect() {
      const sel = window.getSelection?.();
      if (sel?.rangeCount && !sel.isCollapsed) {
        const rect = sel.getRangeAt(0).getBoundingClientRect();
        if (rect && (rect.width || rect.height)) return rect;
      }
      return floatingRich.editor?.getBoundingClientRect?.() || null;
    }

    function positionFloatingRichToolbar() {
      if (!floatingRich.editor) {
        floatingRich.visible = false;
        return;
      }
      const rect = richSelectionRect();
      if (!rect) {
        floatingRich.visible = false;
        return;
      }
      const estimatedWidth = floatingRich.slot === 'title' ? 420 : 560;
      const estimatedHeight = 44;
      const topAbove = rect.top - estimatedHeight - 8;
      floatingRich.top = Math.max(8, topAbove > 8 ? topAbove : rect.bottom + 8);
      floatingRich.left = Math.min(
        Math.max(8, rect.left + rect.width / 2 - estimatedWidth / 2),
        Math.max(8, window.innerWidth - estimatedWidth - 8),
      );
      floatingRich.visible = true;
    }

    function hideFloatingRichToolbar() {
      floatingRich.visible = false;
    }

    function fontFamilyCss(value) {
      const familyMap = {
        default: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif',
        pingfang: '"PingFang SC", -apple-system, BlinkMacSystemFont, sans-serif',
        source_han_sans: '"Source Han Sans SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif',
        inter: 'Inter, "SF Pro Text", -apple-system, BlinkMacSystemFont, sans-serif',
      };
      return familyMap[value] || familyMap.default;
    }

    function applyTiptapCommand(editor, command, value = null) {
      if (!editor || editor.isDestroyed) return false;
      if (floatingRich.tiptapSelection && editor.state?.doc) {
        const maxPos = editor.state.doc.content.size;
        const from = Math.max(0, Math.min(maxPos, floatingRich.tiptapSelection.from));
        const to = Math.max(from, Math.min(maxPos, floatingRich.tiptapSelection.to));
        try { editor.commands.setTextSelection({ from, to }); } catch (e) {}
      }
      const chain = editor.chain().focus();
      let ok = false;
      if (command === 'bold') ok = chain.toggleBold().run();
      else if (command === 'italic') ok = chain.toggleItalic().run();
      else if (command === 'underline') ok = chain.toggleUnderline().run();
      else if (command === 'fontSize') {
        const fontSize = `${Math.max(12, Math.min(120, Number(value || floatingRich.font_size || 24)))}px`;
        // FIX: 隔离编辑器命令 - 优先调用 peFontSize 注册的 setFontSize，避免旧 textStyle mark 名称污染新实例。
        ok = typeof chain.setFontSize === 'function'
          ? chain.setFontSize(fontSize).run()
          : chain.setMark('textStyle', { fontSize }).run();
      }
      else if (command === 'fontFamily') {
        const family = fontFamilyCss(value || floatingRich.font_family);
        // FIX: 隔离编辑器命令 - 优先调用 peFontFamily 注册的 setFontFamily。
        ok = typeof chain.setFontFamily === 'function'
          ? chain.setFontFamily(family).run()
          : chain.setMark('textStyle', { fontFamily: family }).run();
      }
      else if (command === 'foreColor') {
        const color = normalizeRichColor(value, floatingRich.text_color || '#111827');
        ok = typeof chain.setColor === 'function'
          ? chain.setColor(color).run()
          : chain.setMark('textStyle', { color }).run();
      }
      else if (command === 'hiliteColor') {
        if (value === 'transparent') ok = typeof chain.unsetHighlight === 'function' ? chain.unsetHighlight().run() : chain.setMark('highlight', { color: null }).run();
        else ok = chain.setHighlight({ color: normalizeRichColor(value, floatingRich.highlight_color || '#FFF3A3') }).run();
      }
      else if (command === 'justifyLeft') ok = chain.setTextAlign('left').run();
      else if (command === 'justifyCenter') ok = chain.setTextAlign('center').run();
      else if (command === 'justifyRight') ok = chain.setTextAlign('right').run();
      else return false;
      if (!ok) return false;
      floatingRich.tiptapSelection = { from: editor.state.selection.from, to: editor.state.selection.to };
      syncTiptapEditorData(editor);
      positionFloatingRichToolbar();
      return true;
    }

    function applyFloatingRichCommand(command, value = null) {
      if (command === 'image') return;
      const tEditor = activeTiptapEditor();
      if (tEditor && applyTiptapCommand(tEditor, command, value)) return;
      if (!restoreRichSelection()) {
        dispatchRichInput();
        return;
      }
      if (command === 'fontFamily') {
        setRichFontFamily(floatingRich.target, value || floatingRich.font_family);
        return;
      }
      if (command === 'fontSize') {
        setRichFontSize(floatingRich.target, value || floatingRich.font_size);
        return;
      }
      if (command === 'foreColor') {
        richInlineStyle({ color: value || floatingRich.text_color });
        return;
      }
      if (command === 'hiliteColor') {
        richInlineStyle({ backgroundColor: value || floatingRich.highlight_color });
        return;
      }
      richCommand(command, value);
    }

    function insertRichNodesAtCursor(nodes = []) {
      if (!restoreRichSelection()) return;
      const sel = window.getSelection?.();
      if (!sel || !sel.rangeCount) return;
      const range = sel.getRangeAt(0);
      range.deleteContents();
      nodes.forEach(node => {
        range.insertNode(node);
        range.setStartAfter(node);
        range.collapse(true);
      });
      sel.removeAllRanges();
      sel.addRange(range);
      floatingRich.range = range.cloneRange();
      dispatchRichInput();
      positionFloatingRichToolbar();
    }

    function inlineImageNode(asset, fileName = '') {
      const wrap = document.createElement('span');
      wrap.className = 'rich-image-resizer';
      wrap.contentEditable = 'false';
      wrap.title = '点击选中，拖动四角或四边调整图片尺寸，按 Delete 删除';
      wrap.tabIndex = 0;
      wrap.style.width = '32%';
      if (asset?.path) wrap.dataset.assetPath = asset.path;
      wrap.dataset.widthPct = '0.32';
      wrap.dataset.align = 'center';
      const img = document.createElement('img');
      img.src = asset?.url || richAssetUrl(asset?.path);
      img.alt = fileName || asset?.name || 'inline image';
      wrap.appendChild(img);
      return wrap;
    }

    async function uploadImageFilesIntoTiptap(files, editor) {
      if (!files?.length || !editor) return;
      floatingRich.uploadingImage = true;
      try {
        for (const file of files) {
          try {
            const fd = new FormData();
            fd.append('file', file);
            fd.append('session_id', currentProject.value?.id || sessionId.value || 'default');
            fd.append('asset_type', 'module_content_image');
            fd.append('asset_label', '正文内嵌图片');
            const r = await fetch('/api/upload', { method: 'POST', body: fd });
            const j = await r.json();
            if (!r.ok || !j.path) throw new Error(j.error || ('HTTP ' + r.status));
            const imageNode = {
              type: 'posterImage',
              attrs: normalizePosterImageAttrs({ src: j.url || richAssetUrl(j.path), path: j.path, alt: j.filename || file.name, widthPct: 0.32, align: 'center' }),
            };
            const pos = editor.state?.selection?.to ?? editor.state?.doc?.content?.size ?? 0;
            // FIX: 问题3 - 行内图片前后补分隔符，保证能像 Word 一样与文字/多图混排。
            const inserted = editor.chain().focus().insertContentAt(pos, [
              { type: 'text', text: '\u200B' },
              imageNode,
              { type: 'text', text: ' ' },
            ]).run();
            if (!inserted) throw new Error('编辑器拒绝插入图片节点');
            syncTiptapEditorData(editor);
          } catch (e) {
            showToast(`${file.name} 上传失败：${e}`, 'error');
          }
        }
      } finally {
        floatingRich.uploadingImage = false;
      }
    }

    async function ensureActiveRichTiptapEditor() {
      let editor = activeTiptapEditor();
      if (editor && !editor.isDestroyed) return editor;
      const el = floatingRich.editor;
      if (!el || !floatingRich.target || !floatingRich.key) return null;
      editor = await ensureTiptapEditor(el, floatingRich.target, floatingRich.key, floatingRich.slot || 'body');
      if (editor && !editor.isDestroyed) {
        floatingRich.tiptapEditor = editor;
        editor.commands.focus();
        return editor;
      }
      return null;
    }

    async function uploadImageFilesIntoFallbackEditor(files) {
      if (!files?.length || floatingRich.slot === 'title') return;
      floatingRich.uploadingImage = true;
      try {
        for (const file of files) {
          try {
            const fd = new FormData();
            fd.append('file', file);
            fd.append('session_id', currentProject.value?.id || sessionId.value || 'default');
            fd.append('asset_type', 'module_content_image');
            fd.append('asset_label', '正文内嵌图片');
            const r = await fetch('/api/upload', { method: 'POST', body: fd });
            const j = await r.json();
            if (!r.ok || !j.path) throw new Error(j.error || ('HTTP ' + r.status));
            insertRichNodesAtCursor([
              inlineImageNode({ name: j.filename || file.name, path: j.path, url: j.url }, file.name),
              document.createTextNode(' '),
            ]);
          } catch (e) {
            showToast(`${file.name} 上传失败：${e}`, 'error');
          }
        }
      } finally {
        floatingRich.uploadingImage = false;
      }
    }

    async function uploadImageFilesIntoRichEditor(files) {
      if (!files?.length || floatingRich.slot === 'title') return;
      const editor = await ensureActiveRichTiptapEditor();
      if (editor) {
        await uploadImageFilesIntoTiptap(files, editor);
        return;
      }
      await uploadImageFilesIntoFallbackEditor(files);
    }

    async function uploadInlineRichImage(event) {
      const files = Array.from(event?.target?.files || []);
      if (event?.target) event.target.value = '';
      await uploadImageFilesIntoRichEditor(files);
    }

    function pickInlineRichImage() {
      if (floatingRich.uploadingImage || floatingRich.slot === 'title') return;
      if (!floatingRich.editor || !floatingRich.target || !floatingRich.key) {
        showToast('请先点击正文编辑区域，再插入图片', 'error');
        return;
      }
      saveRichSelection({ currentTarget: floatingRich.editor, target: floatingRich.editor });
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.multiple = true;
      input.style.position = 'fixed';
      input.style.left = '-9999px';
      input.style.top = '-9999px';
      input.addEventListener('change', async () => {
        const files = Array.from(input.files || []);
        input.remove();
        if (!files.length) return;
        await uploadImageFilesIntoRichEditor(files);
      }, { once: true });
      document.body.appendChild(input);
      input.click();
    }

    function richCommand(command, value = null) {
      const tEditor = activeTiptapEditor();
      if (tEditor && applyTiptapCommand(tEditor, command, value)) return;
      restoreRichSelection();
      try { document.execCommand(command, false, value); } catch (e) {}
      saveRichSelection();
      dispatchRichInput();
      positionFloatingRichToolbar();
    }

    function richInlineStyle(styleMap = {}) {
      const tEditor = activeTiptapEditor();
      if (tEditor) {
        if (styleMap.color) applyTiptapCommand(tEditor, 'foreColor', styleMap.color);
        if (styleMap.backgroundColor) applyTiptapCommand(tEditor, 'hiliteColor', styleMap.backgroundColor);
        if (styleMap.fontSize) applyTiptapCommand(tEditor, 'fontSize', parseFloat(styleMap.fontSize));
        if (styleMap.fontFamily) tEditor.chain().focus().setMark('textStyle', { fontFamily: styleMap.fontFamily }).run();
        syncTiptapEditorData(tEditor);
        return;
      }
      const sel = window.getSelection?.();
      if (!sel || !sel.rangeCount || sel.isCollapsed) {
        dispatchRichInput();
        return;
      }
      const range = sel.getRangeAt(0);
      const span = document.createElement('span');
      Object.assign(span.style, styleMap);
      try {
        span.appendChild(range.extractContents());
        range.insertNode(span);
        sel.removeAllRanges();
        const next = document.createRange();
        next.selectNodeContents(span);
        sel.addRange(next);
        floatingRich.range = next.cloneRange();
        dispatchRichInput();
        positionFloatingRichToolbar();
      } catch (e) {}
    }

    function setRichFontFamily(cfg, value) {
      if (cfg && cfg !== floatingRich.target) cfg.font_family = value;
      const tEditor = activeTiptapEditor();
      if (tEditor && applyTiptapCommand(tEditor, 'fontFamily', value)) return;
      if (floatingRich.editor) richInlineStyle({ fontFamily: fontFamilyCss(value) });
    }

    function setRichFontSize(cfg, value) {
      const n = Math.max(12, Math.min(120, Number(value || 32)));
      if (cfg && cfg !== floatingRich.target) cfg.font_size = n;
      const tEditor = activeTiptapEditor();
      if (tEditor && applyTiptapCommand(tEditor, 'fontSize', n)) return;
      if (floatingRich.editor) richInlineStyle({ fontSize: `${n}px` });
    }

    function setRichAlign(cfg, value) {
      if (cfg) cfg.text_align = value || 'left';
      richCommand(value === 'center' ? 'justifyCenter' : value === 'right' ? 'justifyRight' : 'justifyLeft');
    }

    function setRichToggle(cfg, key, activeValue, inactiveValue = 'normal') {
      if (!cfg) return;
      cfg[key] = cfg[key] === activeValue ? inactiveValue : activeValue;
      if (key === 'font_weight') richCommand('bold');
      if (key === 'font_style') richCommand('italic');
      if (key === 'text_decoration') richCommand('underline');
      markPosterPreviewDirty();
    }

    function allModuleOptions() {
      const currentKeys = new Set((posterStrategy.value?.module_plan || []).map(m => m.script_key));
      const currentScene = posterStrategy.value?.scene?.id;
      const sceneModules = [];
      if (currentScene && posterStrategies.default) {
        const defaults = [posterStrategies.default, posterStrategy.value].filter(Boolean);
        for (const item of defaults) {
          for (const m of item.module_plan || []) {
            if (['module.m11_person_cards_row', 'module.m12_avatar_wall'].includes(m.script_key)) continue;
            if (!currentKeys.has(m.script_key)) sceneModules.push(m);
          }
        }
      }
      const registry = posterStrategies.module_registry?.module_capabilities || {};
      const registryOptions = Object.keys(registry)
        .filter(k => !currentKeys.has(k))
        .filter(k => !['module.m11_person_cards_row', 'module.m12_avatar_wall'].includes(k))
        .filter(k => k !== 'module.guest_profile_deep')
        .filter(k => !(k === 'module.guest_profile_deep' && currentKeys.has('module.faculty_grid')))
        .filter(k => !(k === 'module.faculty_grid' && currentKeys.has('module.guest_profile_deep')))
        .map(k => ({
          script_key: k,
          name: MODULE_NAME_LABELS[k] || '自定义模块',
          display_name: MODULE_NAME_LABELS[k] || '自定义模块',
          purpose: registry[k].notes || '',
          component: registry[k].renderer || 'lead_paragraph',
          status: registry[k].status,
          status_label: registry[k].status_label,
          capability: registry[k],
        }));
      const seen = new Set();
      return [...sceneModules, ...registryOptions].filter(m => {
        if (!m.script_key || seen.has(m.script_key)) return false;
        seen.add(m.script_key);
        return true;
      });
    }

    function addStrategyModule() {
      if (!posterStrategy.value) return;
      const options = allModuleOptions();
      const selected = options.find(m => m.script_key === moduleAddKey.value);
      const module = selected || {
        id: `CUSTOM-${Date.now().toString().slice(-6)}`,
        name: '自定义模块',
        purpose: '补充本张海报需要的信息',
        component: 'lead_paragraph',
        script_key: `module.custom_${Date.now().toString().slice(-6)}`,
        required: false,
        status: 'needs_enhancement',
        status_label: '',
      };
      posterStrategy.value.module_plan.push(hydrateStrategyModule(module, posterStrategy.value.module_plan.length));
      moduleAddKey.value = '';
      markPosterPreviewDirty();
    }

    function removeStrategyModule(idx) {
      const modules = posterStrategy.value?.module_plan || [];
      if (idx < 0 || idx >= modules.length) return;
      modules.splice(idx, 1);
      markPosterPreviewDirty();
    }

    function moveStrategyModule(idx, delta) {
      const modules = posterStrategy.value?.module_plan || [];
      const next = idx + delta;
      if (next < 0 || next >= modules.length) return;
      const item = modules.splice(idx, 1)[0];
      modules.splice(next, 0, item);
      markPosterPreviewDirty();
    }

    function handleModuleAutofillFiles(event) {
      const files = Array.from(event.target.files || []);
      event.target.value = '';
      for (const f of files) {
        moduleAutofill.files.push(f);
        moduleAutofill.fileMetas.push(compactFileMeta(f));
      }
    }

    async function uploadFilesToCopyKb(files) {
      if (!currentProject.value || !files?.length) return;
      kb.uploading = true;
      let okCount = 0;
      try {
        for (const f of files) {
          const fd = new FormData();
          fd.append('file', f);
          fd.append('scope', 'function');
          fd.append('project_id', currentProject.value.id);
          fd.append('function_id', 'poster_brief');
          fd.append('kb_type', 'copy');
          try {
            const r = await fetch('/api/kb/upload', { method: 'POST', body: fd });
            const j = await r.json();
            if (!r.ok || j.error) throw new Error(j.error || ('HTTP ' + r.status));
            okCount++;
          } catch (e) {
            showToast(`${f.name} 知识库上传失败：${e}`, 'error');
          }
        }
      } finally {
        kb.uploading = false;
        await fetchKbDocs();
      }
      if (okCount) showToast(`已上传 ${okCount} 份文案资料`);
    }

    async function handleCopyAssistantFiles(event) {
      const files = Array.from(event.target.files || []);
      event.target.value = '';
      if (!files.length) return;
      for (const f of files) {
        moduleAutofill.files.push(f);
        moduleAutofill.fileMetas.push(compactFileMeta(f));
      }
      copyChat.history.push({ role: 'user', content: `已上传 ${files.length} 份文案/资料` });
      copyChat.history.push({ role: 'assistant', content: '资料已放入本次文案识别队列，并归档到海报文案知识库。你可以让我识别已有文案，也可以让我基于这些资料生成一版新文案。' });
      scrollCopyChatToBottom();
      await uploadFilesToCopyKb(files);
    }

    function removeModuleAutofillFile(idx) {
      moduleAutofill.files.splice(idx, 1);
      moduleAutofill.fileMetas.splice(idx, 1);
    }

    async function uploadAutofillImageAssets() {
      const uploaded = [];
      for (const file of moduleAutofill.files) {
        const ext = (file.name.split('.').pop() || '').toLowerCase();
        if (!['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'svg'].includes(ext)) continue;
        const existing = moduleAutofill.imageAssets.find(a => a.name === file.name);
        if (existing) {
          uploaded.push(existing);
          continue;
        }
        const fd = new FormData();
        fd.append('file', file);
        fd.append('session_id', `${currentProject.value?.id || 'project'}-${currentPosterFunctionProject.value?.id || 'poster'}`);
        fd.append('asset_type', 'module_content_image');
        fd.append('asset_label', file.name);
        const r = await fetch('/api/upload', { method: 'POST', body: fd });
        const j = await r.json();
        if (!r.ok || !j.path) throw new Error(`${file.name} 图片上传失败：${j.error || ('HTTP ' + r.status)}`);
        const asset = {
          name: file.name,
          path: j.path,
          url: j.url,
          asset_type: j.asset_type || 'module_content_image',
          asset_type_label: j.asset_type_label || '模块内容图',
          asset_label: j.asset_label || file.name,
        };
        moduleAutofill.imageAssets.push(asset);
        uploaded.push(asset);
      }
      return uploaded;
    }

    function findModuleForAutofill(update) {
      const modules = posterStrategy.value?.module_plan || [];
      const byId = modules.find(m => m.id === update.module_id);
      if (byId) return byId;
      const title = String(update.module_title || '').trim();
      if (!title) return null;
      return modules.find(m => String(m.module_config?.module_title || m.name || '').trim() === title)
        || modules.find(m => String(m.module_config?.module_title || m.name || '').includes(title) || title.includes(String(m.module_config?.module_title || m.name || '')));
    }

    function applyModuleAutofillUpdates(updates) {
      const imageByName = new Map(moduleAutofill.imageAssets.map(a => [a.name, a]));
      let changed = 0;
      for (const update of updates || []) {
        const module = findModuleForAutofill(update);
        if (!module) continue;
        module.module_config = module.module_config || {};
        ensureStructuredModuleConfig(module);
        const cfg = module.module_config;
        if (update.module_title) cfg.module_title = update.module_title;
        if (update.content) cfg.content = update.content;
        if (Array.isArray(update.subsections) && update.subsections.length) {
          cfg.subsections = update.subsections.map(x => ({ title: x.title || '', text: x.text || '' }));
        }
        if (Array.isArray(update.list_items) && update.list_items.length) {
          cfg.list_items = update.list_items.map(x => String(x || ''));
        }
        if (Array.isArray(update.headers) && Array.isArray(update.rows) && update.headers.length && update.rows.length) {
          cfg.headers = update.headers;
          cfg.rows = update.rows;
        }
        if (Array.isArray(update.items) && update.items.length) {
          cfg.items = update.items.map(x => ({ ...x }));
        }
        if (Array.isArray(update.submodules) && update.submodules.length) {
          cfg.submodules = update.submodules.map(x => ({ ...x }));
        }
        if (Array.isArray(update.actions) && update.actions.length) {
          cfg.actions = update.actions.map(x => ({ text: x.text || '', hint: x.hint || '', color: x.color || '' }));
        }
        if (Array.isArray(update.contacts) && update.contacts.length) {
          cfg.contacts = update.contacts.map(x => ({ label: x.label || '', value: x.value || '' }));
        }
        if (Array.isArray(update.people_groups) && update.people_groups.length) {
          cfg.faculty_mode = 'avatar_wall';
          cfg.submodules = update.people_groups.map(g => ({
            title: g.title || cfg.module_title || module.name,
            columns: g.columns || 5,
            items: (g.items || []).map(p => ({ name: p.name || '', org: p.org || p.title || '', avatar: p.avatar || '' })),
          }));
        }
        if (update.speaker && (update.speaker.name || update.speaker.title || update.speaker.sections)) {
          cfg.faculty_mode = 'speaker_card';
          cfg.speaker = {
            name: update.speaker.name || '',
            title: update.speaker.title || '',
            avatar: update.speaker.avatar || '',
            sections: (update.speaker.sections || []).map(s => ({ title: s.title || '', text: s.text || '' })),
          };
        }
        if (Array.isArray(update.images) && update.images.length) {
          cfg.images = cfg.images || [];
          for (const img of update.images) {
            const asset = imageByName.get(img.name);
            if (asset && !cfg.images.some(x => x.path === asset.path)) {
              cfg.images.push({ ...asset, asset_label: img.asset_label || asset.asset_label || asset.name });
            }
          }
        }
        changed++;
      }
      return changed;
    }

    const COPY_DRAFT_STRUCTURED_KEYS = [
      'subsections', 'list_items', 'headers', 'rows', 'people_groups',
      'speaker', 'items', 'submodules', 'actions', 'contacts', 'images',
    ];

    function prepareCopyDraftUpdate(update) {
      const u = JSON.parse(JSON.stringify(update || {}));
      const details = {};
      for (const key of COPY_DRAFT_STRUCTURED_KEYS) {
        if (u[key] !== undefined) details[key] = u[key];
      }
      u._open = true;
      u._details = details;
      return u;
    }

    function moduleCopyDraftLabel(update) {
      const m = findModuleForAutofill(update);
      const code = m ? moduleTypeCodeLabel(m) : (update.script_key || '');
      return `${update.module_title || m?.module_config?.module_title || m?.name || '模块文案'}${code ? ` · ${code}` : ''}`;
    }

    function normalizedCopyDraftUpdates() {
      const draft = moduleAutofill.copyDraft;
      if (!draft) return [];
      return (draft.updates || []).map(u => {
        const out = { ...u };
        delete out._open;
        const details = out._details || {};
        delete out._details;
        if (details && typeof details === 'object' && !Array.isArray(details)) {
          Object.assign(out, details);
        }
        return out;
      });
    }

    function copyUpdateFromStrategyModule(module) {
      if (!module || isTitleVisualModule(module) || isLogoVisualModule(module)) return null;
      const cfg = module.module_config || {};
      const update = {
        module_id: module.id,
        script_key: module.script_key,
        module_title: cfg.module_title || module.name || module.display_name || '模块',
        content: cfg.content || '',
      };
      if (Array.isArray(cfg.subsections) && cfg.subsections.length) {
        update.subsections = cfg.subsections.map(s => ({ title: s.title || '', text: s.text || '' }));
      }
      if (Array.isArray(cfg.list_items) && cfg.list_items.length) update.list_items = cfg.list_items.map(x => String(x || ''));
      if (Array.isArray(cfg.headers) && cfg.headers.length) update.headers = cfg.headers.map(x => String(x || ''));
      if (Array.isArray(cfg.rows) && cfg.rows.length) update.rows = cfg.rows.map(r => Array.isArray(r) ? r.map(x => String(x || '')) : []);
      if (Array.isArray(cfg.items) && cfg.items.length) update.items = cfg.items.map(x => ({ ...x }));
      if (Array.isArray(cfg.submodules) && cfg.submodules.length) {
        update.submodules = cfg.submodules.map(x => ({ ...x }));
        if (specialModuleKind(module) === 'faculty_lineup') {
          update.people_groups = cfg.submodules.map(g => ({
            title: g.title || '',
            columns: g.columns || 5,
            items: (g.items || []).map(p => ({ name: p.name || '', org: p.org || p.title || '', avatar: p.avatar || '' })),
          }));
        }
      }
      if (cfg.speaker && (cfg.speaker.name || cfg.speaker.title || (cfg.speaker.sections || []).length)) {
        update.speaker = {
          name: cfg.speaker.name || '',
          title: cfg.speaker.title || '',
          avatar: cfg.speaker.avatar || '',
          sections: (cfg.speaker.sections || []).map(s => ({ title: s.title || '', text: s.text || '' })),
        };
      }
      if (Array.isArray(cfg.actions) && cfg.actions.length) update.actions = cfg.actions.map(a => ({ ...a }));
      if (Array.isArray(cfg.contacts) && cfg.contacts.length) update.contacts = cfg.contacts.map(c => ({ ...c }));
      if (Array.isArray(cfg.images) && cfg.images.length) update.images = cfg.images.map(img => ({ ...img }));
      return update;
    }

    function updateHasCopyContent(update) {
      if (!update) return false;
      return !!(
        update.content
        || (update.subsections || []).some(s => s.title || s.text)
        || (update.list_items || []).length
        || (update.headers || []).length
        || (update.rows || []).length
        || (update.people_groups || []).length
        || (update.speaker && (update.speaker.name || update.speaker.title || (update.speaker.sections || []).length))
        || (update.items || []).length
        || (update.submodules || []).length
        || (update.actions || []).length
        || (update.contacts || []).length
      );
    }

    async function restoreCopyDraftForCurrentPoster() {
      if (!currentProject.value || !currentPosterFunctionProject.value) return;
      if (!posterStrategy.value && currentPosterFunctionProject.value.poster_strategy) {
        posterStrategy.value = hydratePosterStrategy(currentPosterFunctionProject.value.poster_strategy);
      }
      let saved = null;
      const artifactId = currentPosterFunctionProject.value.copy_artifact_id;
      if (artifactId) {
        try {
          const r = await fetch(`/api/projects/${currentProject.value.id}/artifacts/${artifactId}`);
          const j = await r.json();
          if (r.ok) saved = j;
        } catch (e) { /* 没有历史文案也允许从模块恢复 */ }
      }
      const savedJson = saved?.output?.json || {};
      const savedUpdates = Array.isArray(savedJson.updates) ? savedJson.updates : (Array.isArray(savedJson.module_copy) ? savedJson.module_copy : []);
      const moduleUpdates = (posterStrategy.value?.module_plan || [])
        .map(copyUpdateFromStrategyModule)
        .filter(Boolean);
      const savedById = new Map(savedUpdates.map(u => [u.module_id || u.id || u.script_key || u.module_title, u]));
      const merged = moduleUpdates.map(u => {
        const key = u.module_id || u.script_key || u.module_title;
        return updateHasCopyContent(u) ? u : { ...(savedById.get(key) || {}), ...u };
      });
      if (!merged.length && savedUpdates.length) merged.push(...savedUpdates);
      moduleAutofill.copyDraft = {
        title: savedJson.title || currentPosterFunctionProject.value.name || '',
        subtitle: savedJson.subtitle || copyImport.subtitleText || '',
        targetProjectId: currentProject.value.id,
        targetFunctionProjectId: currentPosterFunctionProject.value.id,
        targetName: currentPosterFunctionProject.value.name,
        updates: merged.map(prepareCopyDraftUpdate),
        notes: savedJson.notes || [],
        modulesOpen: false,
        readableMarkdown: '',
      };
      moduleAutofill.copyDraft.readableMarkdown = copyDraftToMarkdown();
      moduleAutofill.copySavedArtifact = saved?.meta || (artifactId ? { id: artifactId, title: `${currentPosterFunctionProject.value.name || '海报子项目'} 文案稿` } : null);
      moduleAutofill.notes = moduleAutofill.copyDraft.notes || [];
    }

    function copyDraftMCode(update) {
      const key = String(update?.script_key || findModuleForAutofill(update)?.script_key || '');
      const mm = key.match(/^module\.m(\d+)_/);
      return mm ? Number(mm[1]) : 0;
    }

    function copyDraftNeedsImage(update) {
      const code = copyDraftMCode(update);
      return [6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 20, 21, 25].includes(code);
    }

    function copyDraftImagePlaceholder(update) {
      const details = update?._details || {};
      const hasImages = Array.isArray(details.images) && details.images.length;
      const hasSpeakerAvatar = details.speaker && details.speaker.avatar;
      const hasPeopleAvatar = Array.isArray(details.people_groups) && details.people_groups.some(g => (g.items || []).some(p => p.avatar));
      const hasCourseImage = Array.isArray(details.items) && details.items.some(x => x.image);
      return copyDraftNeedsImage(update) && !hasImages && !hasSpeakerAvatar && !hasPeopleAvatar && !hasCourseImage;
    }

    function ensureCopyDraftTable(update) {
      update._details = update._details || {};
      update._details.headers = Array.isArray(update._details.headers) && update._details.headers.length ? update._details.headers : ['字段', '内容'];
      update._details.rows = Array.isArray(update._details.rows) && update._details.rows.length ? update._details.rows : [['', '']];
    }

    function addCopyDraftTableRow(update) {
      ensureCopyDraftTable(update);
      update._details.rows.push(Array(update._details.headers.length).fill(''));
    }

    function addCopyDraftTableCol(update) {
      ensureCopyDraftTable(update);
      update._details.headers.push('新列');
      update._details.rows.forEach(r => r.push(''));
    }

    function removeCopyDraftTableRow(update, idx) {
      update?._details?.rows?.splice(idx, 1);
    }

    function addCopyDraftSubsection(update) {
      update._details = update._details || {};
      update._details.subsections = Array.isArray(update._details.subsections) ? update._details.subsections : [];
      update._details.subsections.push({ title: '小标题', text: '' });
    }

    function addCopyDraftAction(update) {
      update._details = update._details || {};
      update._details.actions = Array.isArray(update._details.actions) ? update._details.actions : [];
      update._details.actions.push({ text: '按钮文案', hint: '', color: '' });
    }

    function copyDraftToMarkdown() {
      const draft = moduleAutofill.copyDraft;
      if (!draft) return '';
      const lines = [];
      lines.push(`# ${draft.title || currentPosterFunctionProject.value?.name || currentProject.value?.name || '海报文案'}`);
      if (draft.subtitle) lines.push('', `> ${draft.subtitle}`);
      lines.push('', `对应项目：${currentProject.value?.name || ''}`);
      lines.push(`对应海报子项目：${draft.targetName || currentPosterFunctionProject.value?.name || ''}`);
      for (const update of normalizedCopyDraftUpdates()) {
        lines.push('', `## ${update.module_title || update.module_id || '模块'}`);
        if (update.content) lines.push('', update.content);
        if (Array.isArray(update.subsections)) {
          update.subsections.forEach(s => {
            lines.push('', `### ${s.title || '小标题'}`);
            if (s.text) lines.push('', s.text);
          });
        }
        if (Array.isArray(update.headers) && Array.isArray(update.rows) && update.headers.length) {
          lines.push('', `| ${update.headers.join(' | ')} |`);
          lines.push(`| ${update.headers.map(() => '---').join(' | ')} |`);
          update.rows.forEach(r => lines.push(`| ${update.headers.map((_, i) => r?.[i] || '').join(' | ')} |`));
        }
        if (Array.isArray(update.people_groups)) {
          update.people_groups.forEach(g => {
            lines.push('', `### ${g.title || '人员分组'}`);
            (g.items || []).forEach(p => lines.push(`- ${p.name || '姓名'} ${p.org ? `｜${p.org}` : ''}${p.avatar ? '' : ' 【图片】'}`));
          });
        }
        if (update.speaker) {
          lines.push('', `### ${update.speaker.name || '讲师'} ${update.speaker.title ? `｜${update.speaker.title}` : ''} ${update.speaker.avatar ? '' : '【图片】'}`.trim());
          (update.speaker.sections || []).forEach(s => lines.push('', `#### ${s.title || '介绍'}`, s.text || ''));
        }
        if (Array.isArray(update.items)) {
          update.items.forEach(item => lines.push('', `### ${item.title || '卡片'}`, `${item.image ? '' : '【图片】'}${item.text || ''}`.trim()));
        }
        if (Array.isArray(update.actions)) update.actions.forEach(a => lines.push('', `【按钮】${a.text || ''} ${a.hint || ''}`.trim()));
        if (copyDraftImagePlaceholder(update)) lines.push('', '【图片】');
      }
      return lines.join('\n');
    }

    function syncCopyDraftReadableFromModules() {
      if (!moduleAutofill.copyDraft) return;
      moduleAutofill.copyDraft.readableMarkdown = copyDraftToMarkdown();
      showToast('已按模块结构重排完整文案');
    }

    function scrollCopyChatToBottom() {
      nextTick(() => {
        const el = copyChatMessagesEl.value;
        if (el) el.scrollTop = el.scrollHeight;
      });
    }

    function clearCopyChat() {
      copyChat.history.splice(0);
      copyChat.input = '';
      saveCurrentProjectAssistantMemory();
    }

    async function sendCopyChatMessage() {
      const text = copyChat.input.trim();
      if (!text || copyChat.busy || !currentProject.value || !currentPosterFunctionProject.value) return;
      if (!modelConfigured('llm')) {
        showToast('请先配置大语言模型 API Key', 'error');
        openSettings();
        return;
      }
      copyChat.input = '';
      copyChat.history.push({ role: 'user', content: text });
      rememberProjectFeatureUserMessage('copywriter', text);
      scrollCopyChatToBottom();
      if (!moduleAutofill.copyDraft) {
        moduleAutofill.copyRequirement = text;
        const wantsRecognize = moduleAutofill.files.length && /(识别|已有|原文|上传|忠实|按文件|按资料)/.test(text);
        copyChat.busy = true;
        try {
          if (wantsRecognize) {
            await runModuleAutofill();
            copyChat.history.push({ role: 'assistant', content: '已根据上传资料识别并生成模块文案草稿，你可以继续让我修改。' });
          } else {
            await runModuleCopyGenerate();
            copyChat.history.push({ role: 'assistant', content: '已根据当前海报子项目模块和知识库生成文案草稿，你可以继续让我修改。' });
          }
        } finally {
          copyChat.busy = false;
          scrollCopyChatToBottom();
          saveCurrentProjectAssistantMemory();
        }
        return;
      }
      copyChat.busy = true;
      try {
        const r = await fetch(`/api/projects/${currentProject.value.id}/function-projects/poster_brief/${currentPosterFunctionProject.value.id}/copy-chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: text,
            title: moduleAutofill.copyDraft.title || '',
            subtitle: moduleAutofill.copyDraft.subtitle || '',
            readable_markdown: moduleAutofill.copyDraft.readableMarkdown || copyDraftToMarkdown(),
            updates: normalizedCopyDraftUpdates(),
            history: projectScopedAssistantHistory(copyChat.history.slice(0, -1)),
          }),
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || j.error || ('HTTP ' + r.status));
        if (j.title !== undefined) moduleAutofill.copyDraft.title = j.title || moduleAutofill.copyDraft.title;
        if (j.subtitle !== undefined) moduleAutofill.copyDraft.subtitle = j.subtitle || '';
        if (j.readable_markdown) moduleAutofill.copyDraft.readableMarkdown = j.readable_markdown;
        if (Array.isArray(j.updates) && j.updates.length) {
          moduleAutofill.copyDraft.updates = j.updates.map(prepareCopyDraftUpdate);
        }
        moduleAutofill.copySavedArtifact = null;
        copyChat.history.push({ role: 'assistant', content: j.reply || '已按你的要求修改当前文案。' });
      } catch (e) {
        copyChat.history.push({ role: 'assistant', content: '修改失败：' + e });
      } finally {
        copyChat.busy = false;
        scrollCopyChatToBottom();
        saveCurrentProjectAssistantMemory();
      }
    }

    function downloadTextFile(filename, content, mime = 'text/plain;charset=utf-8') {
      const blob = new Blob([content], { type: mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }

    function exportModuleCopyDraftMd() {
      downloadTextFile(`${currentPosterFunctionProject.value?.name || '海报文案'}.md`, moduleAutofill.copyDraft?.readableMarkdown || copyDraftToMarkdown(), 'text/markdown;charset=utf-8');
    }

    function exportModuleCopyDraftWord() {
      const md = moduleAutofill.copyDraft?.readableMarkdown || copyDraftToMarkdown();
      const html = `<!doctype html><html><head><meta charset="utf-8"><title>海报文案</title></head><body><pre style="font-family:Microsoft YaHei,Arial,sans-serif;white-space:pre-wrap;line-height:1.7">${md.replace(/[&<>]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[ch]))}</pre></body></html>`;
      downloadTextFile(`${currentPosterFunctionProject.value?.name || '海报文案'}.doc`, html, 'application/msword;charset=utf-8');
    }

    async function runModuleCopyGenerate() {
      if (!currentProject.value || !currentPosterFunctionProject.value || !posterStrategy.value) {
        showToast('请先选择一个海报子项目', 'error');
        return;
      }
      if (!modelConfigured('llm')) {
        showToast('请先配置大语言模型 API Key', 'error');
        openSettings();
        return;
      }
      moduleAutofill.copyGenerating = true;
      moduleAutofill.notes = [];
      try {
        const r = await fetch(`/api/projects/${currentProject.value.id}/function-projects/poster_brief/${currentPosterFunctionProject.value.id}/generate-copy`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_strategy: currentPosterStrategyPayload(),
            module_plan: currentPosterStrategyPayload().module_plan || [],
            requirement: moduleAutofill.copyRequirement || '',
            overwrite_mode: moduleAutofill.overwriteMode || 'fill_empty',
          }),
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || j.error || ('HTTP ' + r.status));
        moduleAutofill.copyDraft = {
          title: j.title || '',
          subtitle: j.subtitle || '',
          targetProjectId: currentProject.value.id,
          targetFunctionProjectId: currentPosterFunctionProject.value.id,
          targetName: currentPosterFunctionProject.value.name,
          updates: (j.updates || []).map(prepareCopyDraftUpdate),
          notes: j.notes || [],
          modulesOpen: false,
          readableMarkdown: '',
        };
        moduleAutofill.copyDraft.readableMarkdown = j.readable_markdown || copyDraftToMarkdown();
        moduleAutofill.copySavedArtifact = null;
        clearCopyChat();
        moduleAutofill.notes = j.notes || [];
        showToast(`已生成 ${moduleAutofill.copyDraft.updates.length} 个模块文案草稿，请确认后填入`);
      } catch (e) {
        showToast('生成模块文案失败：' + e, 'error');
      } finally {
        moduleAutofill.copyGenerating = false;
      }
    }

    function clearModuleCopyDraft() {
      moduleAutofill.copyDraft = null;
      moduleAutofill.copySavedArtifact = null;
      clearCopyChat();
    }

    async function saveModuleCopyDraftArtifact(updates) {
      const r = await fetch(`/api/projects/${currentProject.value.id}/function-projects/poster_brief/${currentPosterFunctionProject.value.id}/copy-artifact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: moduleAutofill.copyDraft.title || currentPosterFunctionProject.value.name,
          subtitle: moduleAutofill.copyDraft.subtitle || '',
          markdown: moduleAutofill.copyDraft.readableMarkdown || copyDraftToMarkdown(),
          module_markdown: copyDraftToMarkdown(),
          updates,
          notes: moduleAutofill.copyDraft.notes || moduleAutofill.notes || [],
        }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || j.error || ('HTTP ' + r.status));
      moduleAutofill.copySavedArtifact = j.artifact || null;
      await fetchProject(currentProject.value.id);
      if (j.function_project) {
        currentPosterFunctionProject.value = {
          ...j.function_project,
          poster_strategy: j.function_project.poster_strategy ? hydratePosterStrategy(j.function_project.poster_strategy) : currentPosterFunctionProject.value?.poster_strategy,
        };
      }
      return j.artifact;
    }

    async function applyModuleCopyDraft() {
      if (!moduleAutofill.copyDraft) return;
      if (moduleAutofill.copyDraft.targetProjectId !== currentProject.value?.id
          || moduleAutofill.copyDraft.targetFunctionProjectId !== currentPosterFunctionProject.value?.id) {
        showToast('当前文案草稿不属于这个项目/海报子项目，禁止跨项目填入', 'error');
        return;
      }
      moduleAutofill.copyApplying = true;
      try {
        const updates = normalizedCopyDraftUpdates();
        const changed = applyModuleAutofillUpdates(updates);
        if (moduleAutofill.copyDraft.subtitle) {
          copyImport.subtitleText = moduleAutofill.copyDraft.subtitle;
        }
        await saveProjectPosterStrategy();
        skillStream.posterUrl = '';
        skillStream.lastArtifact = null;
        skillStream.done = false;
        skillStream.posterPreviewDirty = changed > 0;
        await saveModuleCopyDraftArtifact(updates);
        showToast(`已保存文案稿，并填入 ${changed} 个生图模块，正在生成当前预览`);
        setDetailNav('poster_brief');
        await generatePosterFromModules();
      } catch (e) {
        showToast('保存文案并填入模块失败：' + e, 'error');
      } finally {
        moduleAutofill.copyApplying = false;
      }
    }

    function goPosterBriefAfterCopy() {
      if (!currentPosterFunctionProject.value) {
        showToast('请先选择对应的海报子项目', 'error');
        return;
      }
      setDetailNav('poster_brief');
    }

    async function runModuleAutofill() {
      if (!currentProject.value || !currentPosterFunctionProject.value || !posterStrategy.value) {
        showToast('请先选择一个海报子项目', 'error');
        return;
      }
      if (!moduleAutofill.files.length) {
        showToast('请先上传要识别的文案资料', 'error');
        return;
      }
      if (!modelConfigured('llm')) {
        showToast('请先配置大语言模型 API Key', 'error');
        openSettings();
        return;
      }
      moduleAutofill.running = true;
      moduleAutofill.notes = [];
      try {
        await uploadAutofillImageAssets();
        const fd = new FormData();
        moduleAutofill.files.forEach(f => fd.append('files', f));
        fd.append('module_plan_json', JSON.stringify(currentPosterStrategyPayload().module_plan || []));
        const r = await fetch(`/api/projects/${currentProject.value.id}/function-projects/poster_brief/${currentPosterFunctionProject.value.id}/autofill-modules`, {
          method: 'POST',
          body: fd,
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || j.error || ('HTTP ' + r.status));
        const updates = Array.isArray(j.updates) ? j.updates : [];
        moduleAutofill.copyDraft = {
          title: j.title || currentPosterFunctionProject.value.name || currentProject.value.name || '海报文案',
          subtitle: j.subtitle || copyImport.subtitleText || '',
          targetProjectId: currentProject.value.id,
          targetFunctionProjectId: currentPosterFunctionProject.value.id,
          targetName: currentPosterFunctionProject.value.name,
          updates: updates.map(prepareCopyDraftUpdate),
          notes: j.notes || [],
          modulesOpen: false,
          readableMarkdown: '',
        };
        moduleAutofill.copyDraft.readableMarkdown = j.readable_markdown || copyDraftToMarkdown();
        moduleAutofill.copySavedArtifact = null;
        const changed = applyModuleAutofillUpdates(updates);
        moduleAutofill.notes = j.notes || [];
        showToast(`已识别 ${updates.length} 个模块，生成了可编辑文案草稿`);
      } catch (e) {
        showToast('识别文案自动填写失败：' + e, 'error');
      } finally {
        moduleAutofill.running = false;
      }
    }

    function moduleTitleRequired(m) {
      return !isTitleVisualModule(m) && !isLogoVisualModule(m) && !['subtitle_text'].includes(m.component);
    }

    function isTitleVisualModule(m) {
      const component = m?.component || '';
      const scriptKey = m?.script_key || '';
      return ['hero_strip', 'series_identity'].includes(component)
        || scriptKey === 'module.tm1_tm13_visual_layer'
        || ['module.series_identity', 'module.series_identity_feedback'].includes(scriptKey);
    }

    function isLogoVisualModule(m) {
      const component = m?.component || '';
      const scriptKey = m?.script_key || '';
      return ['top_logo_bar', 'footer_logobar'].includes(component)
        || scriptKey === 'module.logo_endorsement';
    }

    function moduleImageKey(m) {
      return m.id || m.script_key || m.name;
    }

    async function uploadStrategyModuleImages(event, module) {
      const files = Array.from(event.target.files || []);
      event.target.value = '';
      if (!files.length || !module) return;
      const key = moduleImageKey(module);
      moduleImageUploading[key] = true;
      module.module_config = module.module_config || {};
      module.module_config.images = module.module_config.images || [];
      let ok = 0;
      for (const file of files) {
        try {
          const fd = new FormData();
          fd.append('file', file);
          fd.append('session_id', currentProject.value?.id || sessionId.value || 'default');
          fd.append('asset_type', 'module_content_image');
          fd.append('asset_label', module.module_config.module_title || module.name || '模块图片');
          const r = await fetch('/api/upload', { method: 'POST', body: fd });
          const j = await r.json();
          if (!r.ok || !j.path) throw new Error(j.error || ('HTTP ' + r.status));
          module.module_config.images.push({
            name: j.filename || file.name,
            path: j.path,
            url: j.url,
            asset_type: j.asset_type,
            asset_type_label: j.asset_type_label,
            asset_label: j.asset_label || '',
          });
          if (!module.module_config.image) module.module_config.image = j.path;
          ok++;
        } catch (e) {
          showToast(`${file.name} 上传失败：${e}`, 'error');
        }
      }
      moduleImageUploading[key] = false;
      if (ok) showToast(`已给「${module.name}」上传 ${ok} 张图片`);
      if (ok) markPosterPreviewDirty();
    }

    async function uploadModuleImageForTarget(event, module, target, key = 'image') {
      const files = Array.from(event.target.files || []);
      event.target.value = '';
      if (!files.length || !module || !target) return;
      const moduleKey = moduleImageKey(module);
      moduleImageUploading[moduleKey] = true;
      module.module_config = module.module_config || {};
      module.module_config.images = module.module_config.images || [];
      target.images = Array.isArray(target.images) ? target.images : [];
      let ok = 0;
      try {
        for (const file of files) {
          try {
            const fd = new FormData();
            fd.append('file', file);
            fd.append('session_id', currentProject.value?.id || sessionId.value || 'default');
            const assetType = key === 'avatar'
              ? 'person_avatar'
              : key === 'module_frame_path'
                ? 'module_frame'
                : key === 'title_decoration_path'
                  ? 'section_title_decoration'
                  : 'module_content_image';
            fd.append('asset_type', assetType);
            fd.append('asset_label', target.name || target.title || module.module_config.module_title || module.name || '模块图片');
            const r = await fetch('/api/upload', { method: 'POST', body: fd });
            const j = await r.json();
            if (!r.ok || !j.path) throw new Error(j.error || ('HTTP ' + r.status));
            const item = {
              name: j.filename || file.name,
              path: j.path,
              url: j.url,
              asset_type: j.asset_type,
              asset_type_label: j.asset_type_label,
              asset_label: j.asset_label || '',
            };
            module.module_config.images.push(item);
            target.images.push(item);
            if (!target[key]) target[key] = item.path;
            if (key === 'module_frame_path') {
              module.module_config.module_frame_mode = 'upload';
            }
            ok++;
          } catch (e) {
            showToast(`${file.name} 上传失败：${e}`, 'error');
          }
        }
        markPosterPreviewDirty();
        if (ok) showToast(`已上传并绑定 ${ok} 张图片`);
      } finally {
        moduleImageUploading[moduleKey] = false;
      }
    }

    function removeStrategyModuleImage(module, idx) {
      const imgs = module?.module_config?.images || [];
      if (idx >= 0) {
        const [removed] = imgs.splice(idx, 1);
        clearImageReference(module?.module_config, removed?.path);
      }
      markPosterPreviewDirty();
    }

    function clearImageReference(target, path) {
      if (!target || !path || typeof target !== 'object') return;
      for (const key of ['image', 'image_path', 'avatar', 'qr_image', 'module_frame_path', 'title_decoration_path']) {
        if (target[key] === path) {
          target[key] = '';
          if (key === 'module_frame_path' && target.module_frame_mode === 'upload') target.module_frame_mode = 'generated';
        }
      }
      for (const value of Object.values(target)) {
        if (Array.isArray(value)) {
          value.forEach(item => clearImageReference(item, path));
        } else if (value && typeof value === 'object') {
          clearImageReference(value, path);
        }
      }
    }

    function moduleImageOptions(module) {
      return module?.module_config?.images || [];
    }

    function setImageFromOption(target, value, key = 'image') {
      if (!target) return;
      target[key] = value || '';
      markPosterPreviewDirty();
    }

    function addAvatarGroup(module) {
      ensureStructuredModuleConfig(module);
      module.module_config.submodules.push({ title: '新分组', columns: 3, items: [] });
      markPosterPreviewDirty();
    }

    function removeAvatarGroup(module, groupIdx) {
      module?.module_config?.submodules?.splice(groupIdx, 1);
      markPosterPreviewDirty();
    }

    function addAvatarPerson(group) {
      group.items = group.items || [];
      group.items.push({ name: '姓名', org: '部门/身份', avatar: '' });
      markPosterPreviewDirty();
    }

    function removeAvatarPerson(group, personIdx) {
      group?.items?.splice(personIdx, 1);
      markPosterPreviewDirty();
    }

    function addCourseItem(module) {
      ensureStructuredModuleConfig(module);
      module.module_config.items.push({
        title: '课程/讲师标题',
        layout: 'left_image_right_text',
        text: '',
        image: '',
        actions: [],
      });
      markPosterPreviewDirty();
    }

    function removeCourseItem(module, itemIdx) {
      module?.module_config?.items?.splice(itemIdx, 1);
      markPosterPreviewDirty();
    }

    function addSpeakerSection(module) {
      ensureStructuredModuleConfig(module);
      module.module_config.speaker.sections.push({ title: '新段落', text: '' });
      markPosterPreviewDirty();
    }

    function removeSpeakerSection(module, sectionIdx) {
      module?.module_config?.speaker?.sections?.splice(sectionIdx, 1);
      markPosterPreviewDirty();
    }

    function addAction(target) {
      target.actions = target.actions || [];
      target.actions.push({ text: '立即报名', placement: 'inside_bottom_center', color: '' });
      markPosterPreviewDirty();
    }

    function removeAction(target, actionIdx) {
      target?.actions?.splice(actionIdx, 1);
      markPosterPreviewDirty();
    }

    function addRatingItem(target) {
      target.items = target.items || [];
      target.items.push({ label: '评分项', score: 4.8, max: 5 });
      markPosterPreviewDirty();
    }

    function removeRatingItem(target, itemIdx) {
      target?.items?.splice(itemIdx, 1);
      markPosterPreviewDirty();
    }

    function addQuoteItem(module) {
      ensureStructuredModuleConfig(module);
      module.module_config.items.push({ text: '这里填写原文反馈', author: '反馈人' });
      markPosterPreviewDirty();
    }

    function removeQuoteItem(module, itemIdx) {
      module?.module_config?.items?.splice(itemIdx, 1);
      markPosterPreviewDirty();
    }

    function addTextSubsection(module) {
      ensureStructuredModuleConfig(module);
      module.module_config.subsections = module.module_config.subsections || [];
      module.module_config.subsections.push({ title: '', text: '' });
      markPosterPreviewDirty();
    }

    function removeTextSubsection(module, sectionIdx) {
      module?.module_config?.subsections?.splice(sectionIdx, 1);
      markPosterPreviewDirty();
    }

    function addTextListItem(module) {
      ensureStructuredModuleConfig(module);
      module.module_config.list_items = module.module_config.list_items || [];
      module.module_config.list_items.push('姓名 / 部门 / 说明');
      markPosterPreviewDirty();
    }

    function removeTextListItem(module, itemIdx) {
      module?.module_config?.list_items?.splice(itemIdx, 1);
      markPosterPreviewDirty();
    }

    function addFeedbackSubmodule(module, form = 'image_text_split') {
      ensureStructuredModuleConfig(module);
      const sub = form === 'rating_bars'
        ? { title: '评分', layout_form: 'rating_bars', items: [{ label: '评分项', score: 4.8, max: 5 }] }
        : form === 'image_grid'
          ? { title: '图片成果', layout_form: 'image_grid', images: [], columns: 3, aspect_ratio: 0.62 }
          : { title: '图文反馈', layout_form: 'image_text_split', layout: 'left_image_right_text', text: '', image: '', actions: [] };
      module.module_config.submodules.push(sub);
      markPosterPreviewDirty();
    }

    function removeFeedbackSubmodule(module, subIdx) {
      module?.module_config?.submodules?.splice(subIdx, 1);
      markPosterPreviewDirty();
    }

    function addQaItem(module) {
      ensureStructuredModuleConfig(module);
      module.module_config.items.push({ q: '问题', a: '' });
      markPosterPreviewDirty();
    }

    function removeQaItem(module, itemIdx) {
      module?.module_config?.items?.splice(itemIdx, 1);
      markPosterPreviewDirty();
    }

    function addTimelinePart(module) {
      ensureStructuredModuleConfig(module);
      module.module_config.parts.push({ label: `Part ${module.module_config.parts.length + 1}`, time: '', format: '', topic: '', output: '' });
      markPosterPreviewDirty();
    }

    function removeTimelinePart(module, partIdx) {
      module?.module_config?.parts?.splice(partIdx, 1);
      markPosterPreviewDirty();
    }

    function addTableRow(module) {
      ensureStructuredModuleConfig(module);
      const cols = module.module_config.headers.length || 1;
      module.module_config.rows.push(Array(cols).fill(''));
      markPosterPreviewDirty();
    }

    function removeTableRow(module, rowIdx) {
      module?.module_config?.rows?.splice(rowIdx, 1);
      markPosterPreviewDirty();
    }

    function addTableColumn(module) {
      ensureStructuredModuleConfig(module);
      module.module_config.headers.push('新列');
      module.module_config.rows.forEach(r => r.push(''));
      markPosterPreviewDirty();
    }

    function removeTableColumn(module, colIdx) {
      if (!module?.module_config?.headers || module.module_config.headers.length <= 1) return;
      module.module_config.headers.splice(colIdx, 1);
      (module.module_config.rows || []).forEach(r => r.splice(colIdx, 1));
      markPosterPreviewDirty();
    }

    function titleLayerLabel(type) {
      return {
        global_bg: '全局底图',
        global_bg_decoration: '全局底图装饰元素',
        hero_bg: '头部底图',
        main_wordart: '主标题艺术字',
        subtitle_wordart: '副标题艺术字',
        subtitle_decoration: '副标题艺术字装饰',
        section_title_decoration: '模块标题装饰图',
        module_frame: '模块素材框',
        module_content_image: '模块内容图',
        logo_color: 'Logo',
        logo_black: 'Logo 黑色',
        logo_white: 'Logo 白色',
        contact_qr: '联系人二维码',
        person_avatar: '人员头像图',
      }[type] || type;
    }

    function isPosterImageFile(file) {
      const ext = (file?.name || '').split('.').pop().toLowerCase();
      return ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'svg'].includes(ext) || String(file?.type || '').startsWith('image/');
    }

    function posterVisualName(file) {
      return `${file?.webkitRelativePath || ''} ${file?.name || ''}`.toLowerCase();
    }

    function inferPosterVisualAsset(file) {
      const name = posterVisualName(file);
      if (/白logo|白色logo|white[\s_-]*logo|logo[\s_-]*white/.test(name)) return { type: 'logo_white', label: 'Logo 白色' };
      if (/黑logo|黑色logo|black[\s_-]*logo|logo[\s_-]*black/.test(name)) return { type: 'logo_black', label: 'Logo 黑色' };
      if (/彩logo|彩色logo|color[\s_-]*logo|logo/.test(name)) return { type: 'logo_color', label: 'Logo 彩色' };
      if (/二维码|qr|qrcode/.test(name)) return { type: 'contact_qr', label: '联系人二维码' };
      if (/头像|headshot|avatar|讲师|嘉宾|学员/.test(name)) return { type: 'person_avatar', label: '人员头像图' };
      if (/模块.*(标题|装饰)|标题.*装饰|section.*title|title.*deco/.test(name)) return { type: 'section_title_decoration', label: '模块标题装饰图' };
      if (/副标题.*(装饰|点缀)|subtitle.*deco/.test(name)) return { type: 'subtitle_decoration', label: '副标题艺术字装饰' };
      if (/副标题|subtitle/.test(name)) return { type: 'subtitle_wordart', label: '副标题艺术字' };
      if (/主标题|标题艺术字|艺术字|wordart|title[\s_-]*art/.test(name)) return { type: 'main_wordart', label: '主标题艺术字' };
      if (/头部|头图|页眉|header|hero/.test(name)) return { type: 'hero_bg', label: '头部底图' };
      if (/全局.*装饰|底图.*装饰|背景.*装饰|global.*deco|background.*deco/.test(name)) return { type: 'global_bg_decoration', label: '全局底图装饰元素' };
      if (/全局|底图|背景|background|global|(?:^|[\s_.-])bg(?:$|[\s_.-])/.test(name)) return { type: 'global_bg', label: '全局底图' };
      if (/底框|素材框|卡框|frame|card/.test(name)) return { type: 'module_frame', label: '模块素材框' };
      if (/风格|样式|style/.test(name)) return { type: 'module_content_image', label: '风格素材' };
      if (/参考|视觉|reference|ref/.test(name)) return { type: 'module_content_image', label: '视觉参考' };
      return { type: 'module_content_image', label: '视觉参考' };
    }

    function titleVisualBucket(assetType) {
      return ['global_bg', 'hero_bg', 'main_wordart', 'subtitle_wordart', 'module_frame', 'logo_color', 'logo_black', 'logo_white'].includes(assetType)
        ? assetType
        : null;
    }

    async function uploadPosterVisualAssetFile(file, assetType, assetLabel) {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('session_id', currentProject.value?.id || sessionId.value || 'default');
      fd.append('asset_type', assetType || 'module_content_image');
      fd.append('asset_label', assetLabel || titleLayerLabel(assetType));
      const r = await fetch('/api/upload', { method: 'POST', body: fd });
      const j = await r.json();
      if (!r.ok || !j.path) throw new Error(j.error || ('HTTP ' + r.status));
      const item = {
        name: j.filename || file.name,
        path: j.path,
        url: j.url,
        asset_type: j.asset_type || assetType,
        asset_type_label: j.asset_type_label || titleLayerLabel(assetType),
        asset_label: j.asset_label || assetLabel || titleLayerLabel(assetType),
      };
      const bucket = titleVisualBucket(item.asset_type);
      if (bucket) {
        copyImport.visualLayerUploads[bucket] = copyImport.visualLayerUploads[bucket] || [];
        const existingIdx = copyImport.visualLayerUploads[bucket].findIndex(a => a.path === item.path);
        if (existingIdx >= 0) copyImport.visualLayerUploads[bucket].splice(existingIdx, 1, item);
        else copyImport.visualLayerUploads[bucket].push(item);
        if (item.asset_type === 'module_frame') {
          (posterStrategy.value?.module_plan || []).forEach(m => {
            if (isTitleVisualModule(m) || isLogoVisualModule(m)) return;
            m.module_config = m.module_config || {};
            if (!m.module_config.module_frame_path) {
              m.module_config.module_frame_path = item.path;
              m.module_config.module_frame_mode = 'upload';
            }
          });
        }
      }
      const assetIdx = copyImport.visualAssets.findIndex(a => a.path === item.path && a.asset_type === item.asset_type);
      if (assetIdx >= 0) copyImport.visualAssets.splice(assetIdx, 1, item);
      else copyImport.visualAssets.push(item);
      return item;
    }

    async function uploadTitleVisualLayer(event, assetType) {
      const files = Array.from(event.target.files || []);
      event.target.value = '';
      if (!files.length) return;
      copyImport.visualAssetsUploading = true;
      let ok = 0;
      for (const file of files) {
        try {
          const item = await uploadPosterVisualAssetFile(file, assetType, titleLayerLabel(assetType));
          await applyVisualLayerColorsFromAsset(item);
          ok++;
        } catch (e) {
          showToast(`${file.name} 上传失败：${e}`, 'error');
        }
      }
      copyImport.visualAssetsUploading = false;
      if (ok) showToast(`已上传 ${ok} 个${titleLayerLabel(assetType)}`);
      if (ok) markPosterPreviewDirty();
    }

    function removeTitleVisualLayer(assetType, idx) {
      const arr = copyImport.visualLayerUploads[assetType] || [];
      const [removed] = arr.splice(idx, 1);
      if (removed) {
        const i = copyImport.visualAssets.findIndex(a => a.path === removed.path);
        if (i >= 0) copyImport.visualAssets.splice(i, 1);
        if (assetType === 'module_frame') {
          (posterStrategy.value?.module_plan || []).forEach(m => clearImageReference(m.module_config, removed.path));
        }
        markPosterPreviewDirty();
      }
    }

    function registerAssistantVisualAsset(item) {
      if (!item?.path) return;
      const bucket = titleVisualBucket(item.asset_type);
      if (bucket) {
        copyImport.visualLayerUploads[bucket] = copyImport.visualLayerUploads[bucket] || [];
        const idx = copyImport.visualLayerUploads[bucket].findIndex(a => a.path === item.path);
        if (idx >= 0) copyImport.visualLayerUploads[bucket].splice(idx, 1, item);
        else copyImport.visualLayerUploads[bucket].push(item);
      }
      const allIdx = copyImport.visualAssets.findIndex(a => a.path === item.path && a.asset_type === item.asset_type);
      if (allIdx >= 0) copyImport.visualAssets.splice(allIdx, 1, item);
      else copyImport.visualAssets.push(item);
    }

    function hasAnyModuleImage(cfg) {
      return !!(cfg?.image || cfg?.qr_image || cfg?.module_frame_path || (Array.isArray(cfg?.images) && cfg.images.length));
    }

    function collectPosterMissingAssets() {
      const missing = [];
      for (const m of posterStrategy.value?.module_plan || []) {
        if (isTitleVisualModule(m) || isLogoVisualModule(m)) continue;
        const cfg = m.module_config || {};
        const title = cfg.module_title || m.name || '未命名模块';
        const kind = specialModuleKind(m);
        const code = moduleMCode(m);
        if (['image_text', 'image_grid'].includes(kind) && !hasAnyModuleImage(cfg)) {
          missing.push(`${title} 缺少图片素材`);
        }
        if (code === 25 && !cfg.qr_image && !(cfg.images || []).length) {
          missing.push(`${title} 缺少二维码图片`);
        }
        if (kind === 'faculty_lineup') {
          if (['speaker_card', 'mixed'].includes(cfg.faculty_mode) && cfg.speaker && !cfg.speaker.avatar) {
            missing.push(`${title} 的讲师头像缺失`);
          }
          if (['avatar_wall', 'mixed'].includes(cfg.faculty_mode)) {
            for (const group of cfg.submodules || []) {
              for (const person of group.items || []) {
                if (person.name && !person.avatar) missing.push(`${title}：${person.name} 缺少头像`);
              }
            }
          }
        }
        if (kind === 'course_list') {
          for (const item of cfg.items || []) {
            if ((item.title || item.text) && !item.image && !(cfg.images || []).length) {
              missing.push(`${title}：${item.title || '课程卡片'} 缺少配图`);
            }
          }
        }
        if (kind === 'feedback_flow') {
          for (const sub of cfg.submodules || []) {
            if (['image_text_split', 'image_grid'].includes(sub.layout_form) && !sub.image && !(sub.images || []).length && !(cfg.images || []).length) {
              missing.push(`${title}：${sub.title || '图文子模块'} 缺少图片素材`);
            }
          }
        }
      }
      return [...new Set(missing)];
    }

    async function generatePosterFromModules(options = {}) {
      const auto = !!options.auto;
      if (detailNav.value !== 'poster_brief') {
        if (!auto) showToast('请先进入海报生成功能', 'error');
        return;
      }
      if (skillRunning.value || skillStream.streaming) {
        if (auto) schedulePosterAutoPreview();
        return;
      }
      skillStream.posterUrl = '';
      skillStream.lastArtifact = null;
      skillStream.done = false;
      skillStream.error = '';
      if (posterPreviewRenderTimer) {
        clearTimeout(posterPreviewRenderTimer);
        posterPreviewRenderTimer = null;
      }
      if (posterStrategySaveTimer) {
        clearTimeout(posterStrategySaveTimer);
        posterStrategySaveTimer = null;
      }
      const missingAssets = collectPosterMissingAssets();
      if (missingAssets.length) {
        skillStream.posterPreviewDirty = true;
        skillStream.error = `缺少素材，无法生成：${missingAssets.slice(0, 8).join('；')}${missingAssets.length > 8 ? `；另有 ${missingAssets.length - 8} 项` : ''}`;
        if (!auto) showToast('缺少素材，已停止生成', 'error');
        return;
      }
      if (currentProject.value && posterStrategy.value) {
        await saveProjectPosterStrategy({ silent: auto });
      }
      Object.keys(skillForm).forEach(k => delete skillForm[k]);
      skillForm.use_latest_copy = false;
      skillForm.extra = [
        copyImport.extra || '',
        '请严格按照当前模块编排、标题、正文和图片素材生成海报。用户已在模块中填写的内容必须优先使用，不要复用旧文案产物。'
      ].filter(Boolean).join('\n');
      skillForm.global_bg_prompt = copyImport.globalBgPrompt || '';
      skillForm.hero_bg_prompt = copyImport.heroBgPrompt || '';
      skillForm.wordart_prompt = copyImport.wordartPrompt || '';
      skillForm.subtitle_text = copyImport.subtitleText || '';
      skillForm.title_visual_config = titleVisualPayload();
      skillForm.generate_visual_assets = true;
      skillForm.visual_assets = [
        ...copyImport.visualAssets.map(a => ({
          path: a.path,
          name: a.name,
          asset_type: a.asset_type,
          asset_type_label: a.asset_type_label,
          asset_label: a.asset_label || '',
        })),
        ...(posterStrategy.value?.module_plan || []).flatMap(m => (m.module_config?.images || []).map(img => ({
          ...img,
          module_id: m.id,
          module_name: m.name,
          module_title: m.module_config?.module_title || m.name,
        }))),
      ];
      await runSkill('poster_brief');
    }

    async function fetchSkillsRegistry() {
      try {
        const r = await fetch('/api/skills');
        const j = await r.json();
        skillsRegistry.value = j.skills || {};
      } catch (e) { /* 静默 */ }
    }

    function resetSkillForm(skillName) {
      // 清空旧表单值
      Object.keys(skillForm).forEach(k => delete skillForm[k]);
      const meta = skillsRegistry.value[skillName];
      if (!meta) return;
      for (const f of meta.form || []) {
        skillForm[f.key] = f.default !== undefined ? JSON.parse(JSON.stringify(f.default))
          : (f.type === 'bool' ? false : (f.type === 'number' ? 0 : ''));
      }
    }

    function resetSkillStream() {
      skillStream.streaming = false;
      skillStream.done = false;
      skillStream.error = '';
      skillStream.text = '';
      skillStream.progress = [];
      skillStream.lastArtifact = null;
      skillStream.posterUrl = '';
      skillStream.posterPreviewDirty = false;
    }

    function markPosterPreviewDirty() {
      if (detailNav.value !== 'poster_brief') return;
      posterEditDirty.value = true;
      skillStream.done = false;
      skillStream.posterPreviewDirty = true;
      schedulePosterStrategyAutosave();
    }

    function schedulePosterAutoPreview() {
      return;
      if (!currentProject.value || !posterStrategy.value || !currentPosterFunctionProject.value) return;
      if (detailNav.value !== 'poster_brief') return;
      if (posterPreviewRenderTimer) clearTimeout(posterPreviewRenderTimer);
      posterPreviewRenderTimer = setTimeout(async () => {
        posterPreviewRenderTimer = null;
        if (detailNav.value !== 'poster_brief' || !skillStream.posterPreviewDirty) return;
        if (skillRunning.value || skillStream.streaming) {
          schedulePosterAutoPreview();
          return;
        }
        await generatePosterFromModules({ auto: true });
      }, 1800);
    }

    function schedulePosterStrategyAutosave() {
      if (!currentProject.value || !posterStrategy.value || !currentPosterFunctionProject.value) return;
      if (posterStrategySaveTimer) clearTimeout(posterStrategySaveTimer);
      posterStrategySaveTimer = setTimeout(async () => {
        try {
          skillStream.autoSaving = true;
          await saveProjectPosterStrategy({ silent: true });
        } catch (e) {
          skillStream.error = '自动保存模块失败：' + e;
        } finally {
          skillStream.autoSaving = false;
        }
      }, 900);
    }

    // 调 skill SSE 流
    async function runSkill(skill) {
      if (skillRunning.value) return;
      if (!currentProject.value) return;
      const pid = currentProject.value.id;

      resetSkillStream();
      skillRunning.value = true;
      skillStream.streaming = true;
      runningJob.value = { skill, cancellable: false };

      let buf = '';
      try {
        const resp = await fetch(`/api/projects/${pid}/skills/${skill}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ params: { ...skillForm, project_strategy: currentPosterStrategyPayload() } }),
        });
        if (!resp.ok) {
          const errText = await resp.text();
          skillStream.error = `HTTP ${resp.status}: ${errText.slice(0, 400)}`;
          return;
        }
        const reader = resp.body.getReader();
        const decoder = new TextDecoder('utf-8');

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });

          // 按 SSE 分隔（\n\n）切
          const parts = buf.split('\n\n');
          buf = parts.pop() || '';   // 最后一段可能未完整，留下次拼
          for (const p of parts) {
            const line = p.trim();
            if (!line.startsWith('data:')) continue;
            const payload = line.slice(5).trim();
            try {
              const ev = JSON.parse(payload);
              await _handleSseEvent(ev, skill, pid);
            } catch (e) {
              console.warn('SSE parse failed:', payload, e);
            }
          }
        }
      } catch (e) {
        skillStream.error = '连接中断：' + e;
      } finally {
        skillRunning.value = false;
        skillStream.streaming = false;
        runningJob.value = null;
        // 刷新项目（拉新 artifact）
        if (currentProject.value) await fetchProject(currentProject.value.id);
      }
    }

    async function _handleSseEvent(ev, skill, pid) {
      const t = ev.type;
      if (t === 'token') {
        skillStream.text += ev.data || '';
      } else if (t === 'progress') {
        skillStream.progress.push(ev.data);
      } else if (t === 'json') {
        // 文案/海报 brief 的结构化结果，暂存到 stream.text 显示用 JSON 美化版
        try {
          skillStream.text = JSON.stringify(ev.data, null, 2);
        } catch (e) { /* 保留原 token 累积 */ }
      } else if (t === 'artifact') {
        skillStream.lastArtifact = ev.data;
        skillStream.done = true;
        // 海报生成类 skill：找 poster.png 文件，构造预览 URL
        if (['poster_brief', 'poster_copy_import'].includes(skill) && ev.data?.files?.includes('poster.png')) {
          // 用 cover.jpg 优先（小），否则 poster.png
          const fname = ev.data.files.includes('cover.jpg') ? 'cover.jpg' : 'poster.png';
          skillStream.posterUrl = `/api/projects/${pid}/artifacts/${ev.data.id}/file?name=${fname}&t=${Date.now()}`;
        }
      } else if (t === 'error') {
        skillStream.error = ev.data || '未知错误';
      } else if (t === 'done') {
        skillStream.done = true;
      } else if (t === 'started') {
        // ignore
      }
    }

    // 文案产物 → 编辑器（H4 联动）
    function applyCopyToEditor(artifact) {
      if (!artifact) return;
      const pid = currentProject.value?.id;
      if (!pid) return;
      // 把 artifact id 存入 sessionStorage，编辑器读取后取 output.json 应用
      sessionStorage.setItem('apply_copy', JSON.stringify({
        pid, artifact_id: artifact.id, ts: Date.now(),
      }));
      view.value = 'editor';
      showToast('已跳转编辑器，将合并文案');
    }

    // 海报 brief → 编辑器（H5 联动）
    async function applyBriefToEditor(artifact) {
      if (!artifact) return;
      const pid = currentProject.value?.id;
      if (!pid) return;
      try {
        // 拉 brief.json 内容
        const r = await fetch(`/api/projects/${pid}/artifacts/${artifact.id}`);
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const j = await r.json();
        const brief = j.output?.json;
        if (!brief || typeof brief !== 'object') {
          showToast('该产物没有 brief.json，无法进编辑器', 'error');
          return;
        }
        sessionStorage.setItem('apply_brief', JSON.stringify({
          pid, artifact_id: artifact.id, brief, ts: Date.now(),
        }));
        view.value = 'editor';
        showToast('已跳转编辑器，将载入 brief');
      } catch (e) {
        showToast('载入失败：' + e, 'error');
      }
    }

    function viewArtifact(a) {
      // 临时：复用 skill stream 区显示历史产物的 markdown
      const pid = currentProject.value?.id;
      if (!pid) return;
      resetSkillStream();
      fetch(`/api/projects/${pid}/artifacts/${a.id}`)
        .then(r => r.json())
        .then(j => {
          skillStream.lastArtifact = a;
          skillStream.text = j.output?.markdown || JSON.stringify(j.output?.json || j, null, 2);
          skillStream.done = true;
          if (['poster_brief', 'poster_copy_import'].includes(a.skill) && a.files?.includes('poster.png')) {
            const fname = a.files.includes('cover.jpg') ? 'cover.jpg' : 'poster.png';
            skillStream.posterUrl = `/api/projects/${pid}/artifacts/${a.id}/file?name=${fname}&t=${Date.now()}`;
          }
        })
        .catch(e => { skillStream.error = '加载失败：' + e; });
    }

    function getSkillArtifacts(skill) {
      const arts = currentProject.value?.artifacts || [];
      if (skill === 'poster_brief') {
        return arts.filter(a => ['poster_brief', 'poster_copy_import'].includes(a.skill));
      }
      return arts.filter(a => a.skill === skill);
    }

    function posterBriefPreviewUrl() {
      if (skillStream.posterUrl) return skillStream.posterUrl;
      return '';
    }

    function latestPosterArtifact() {
      if (skillStream.lastArtifact?.files?.includes('poster.png')) return skillStream.lastArtifact;
      return getSkillArtifacts('poster_brief').find(a => a.files?.includes('poster.png')) || null;
    }

    function posterArtifactFileUrl(name = 'poster.png') {
      const art = latestPosterArtifact();
      if (!currentProject.value?.id || !art?.id) return '';
      return `/api/projects/${currentProject.value.id}/artifacts/${art.id}/file?name=${name}`;
    }

    function posterExportUrl(kind = 'png') {
      return posterArtifactFileUrl(kind === 'pdf' ? 'poster.pdf' : 'poster.png');
    }

    function openPosterLightbox(url = '') {
      const target = posterArtifactFileUrl('poster.png') || url || posterBriefPreviewUrl();
      if (!target) return;
      posterLightbox.url = target;
      posterLightbox.zoom = 100;
      posterLightbox.show = true;
    }

    function closePosterLightbox() {
      posterLightbox.show = false;
    }

    function openPosterFull(url) {
      if (url) window.open(url, '_blank');
    }

    function setDetailNav(tab) {
      const prev = detailNav.value;
      if (prev === 'poster_brief' && tab !== 'poster_brief') {
        if (posterPreviewRenderTimer) {
          clearTimeout(posterPreviewRenderTimer);
          posterPreviewRenderTimer = null;
        }
        if (posterStrategySaveTimer) {
          clearTimeout(posterStrategySaveTimer);
          posterStrategySaveTimer = null;
        }
      }
      detailNav.value = tab;
      // 切到 kb 时刷新文档列表
      if (tab === 'kb') fetchKbDocs();
      if (tab === 'copywriter') {
        fetchPosterFunctionProjects();
        restoreCopyDraftForCurrentPoster();
      }
      if (tab === 'poster_brief' && prev !== 'poster_brief') {
        resetPosterGenerationWorkspace();
      }
      // 切到 skill 能力页：重置表单 + 清空流
      if (skillsRegistry.value[tab]) {
        resetSkillForm(tab);
        resetSkillStream();
      }
    }
    function cancelRunningJob() {
      runningJob.value = null;
      showToast('已取消');
    }

    // 4 个能力的元信息（先硬编码，H2 阶段从 /api/skills 拉）
    const SKILL_META = {
      copywriter: { label: '海报文案', sub: '结合项目背景自动生成各板块文案', icon: '✍️' },
      poster_brief: { label: '海报生图', sub: '基于文案、模块和视觉素材生成海报图片', icon: '🎨' },
      poster_copy_import: { label: '文案识别成图', sub: '上传已有文案，识别结构并生成海报', icon: '📄' },
      poster_render: { label: '海报渲染', sub: '编辑器渲染产物', icon: '🖼️' },
      interview_outline: { label: '访谈提纲', sub: '对齐受访者、目的、时长', icon: '🎤' },
      ppt_outline: { label: 'PPT 大纲', sub: '生成结构化 markdown 大纲', icon: '📊' },
      design_brief: { label: '设计阐释', sub: '已并入文案/海报', icon: '🧭' },
    };
    function skillLabelOf(s) { return SKILL_META[s]?.label || s; }
    function skillSubOf(s) { return SKILL_META[s]?.sub || ''; }
    function skillIconOf(s) { return SKILL_META[s]?.icon || '✨'; }

    // 封面 + 新建项目模态
    const covers = ref([]);
    const newProjectModal = reactive({
      show: false, busy: false, dragging: false,
      uploadedDocs: [],     // 当前会话上传的文档
      pendingFiles: [],
      extracting: false,
      coverBusy: false,
    });
    const newProjectForm = reactive({
      name: '', description: '', status: 'in_progress',
      owner_name: '', cover_id: null,
      cover_theme: '#2563EB',
      tags: [],
      project_type: 'A',
      scene: 'S1',
      poster_strategy: null,
      function_projects: [],
    });
    const projectEditModal = reactive({
      show: false,
      busy: false,
      coverBusy: false,
      name: '',
      description: '',
      status: 'in_progress',
      owner_name: '',
      cover_id: null,
      cover_theme: '#2563EB',
    });

    // ========== 知识库（v0.3） ==========
    const kb = reactive({ docs: [], uploading: false });

    async function fetchKbDocs() {
      try {
        const r = await fetch('/api/kb');
        const j = await r.json();
        kb.docs = j.docs || [];
      } catch (e) { /* 静默 */ }
    }

    async function handleKbUpload(event, scope, projectId, options = {}) {
      const files = Array.from(event.target.files || []);
      if (files.length === 0) return;
      kb.uploading = true;
      let okCount = 0, failCount = 0;
      for (const f of files) {
        const fd = new FormData();
        fd.append('file', f);
        fd.append('scope', scope || 'global');
        if (projectId) fd.append('project_id', projectId);
        if (options.function_id) fd.append('function_id', options.function_id);
        if (options.kb_type) fd.append('kb_type', options.kb_type);
        try {
          const r = await fetch('/api/kb/upload', { method: 'POST', body: fd });
          const j = await r.json();
          if (!r.ok || j.error) {
            failCount++;
            showToast(`${f.name} 失败：${j.error || ('HTTP ' + r.status)}`, 'error');
          } else {
            okCount++;
          }
        } catch (e) {
          failCount++;
          showToast(`${f.name} 上传失败：${e}`, 'error');
        }
      }
      kb.uploading = false;
      event.target.value = '';  // 清掉 input，方便再次选同名文件
      await fetchKbDocs();
      if (okCount) showToast(`已上传 ${okCount} 份文档${failCount ? ` · ${failCount} 失败` : ''}`);
    }

    async function autoFillPosterVisualAssetsFromFiles(files) {
      const imageFiles = (files || []).filter(isPosterImageFile);
      if (!imageFiles.length) return 0;
      copyImport.visualAssetsUploading = true;
      let ok = 0;
      for (const file of imageFiles) {
        const inferred = inferPosterVisualAsset(file);
        try {
          await uploadPosterVisualAssetFile(file, inferred.type, inferred.label);
          ok++;
        } catch (e) {
          showToast(`${file.name} 视觉素材归类失败：${e}`, 'error');
        }
      }
      copyImport.visualAssetsUploading = false;
      if (ok) showToast(`已自动归入 ${ok} 个海报视觉素材`);
      return ok;
    }

    async function handlePosterProjectKbUpload(event) {
      const files = Array.from(event.target.files || []);
      if (!files.length) return;
      await autoFillPosterVisualAssetsFromFiles(files);
      await handleKbUpload(event, 'project', currentProject.value?.id);
    }

    async function uploadFilesToProjectKb(files, projectId) {
      if (!projectId || !files?.length) return 0;
      kb.uploading = true;
      let okCount = 0;
      try {
        for (const file of files) {
          const fd = new FormData();
          fd.append('file', file);
          fd.append('scope', 'project');
          fd.append('project_id', projectId);
          try {
            const r = await fetch('/api/kb/upload', { method: 'POST', body: fd });
            const j = await r.json();
            if (!r.ok || j.error) throw new Error(j.error || ('HTTP ' + r.status));
            okCount++;
          } catch (e) {
            showToast(`${file.name} 项目知识库上传失败：${e}`, 'error');
          }
        }
      } finally {
        kb.uploading = false;
        await fetchKbDocs();
      }
      return okCount;
    }

    async function placeHomeAssistantAttachments(targetNav, projectId) {
      const metas = homeAssistant.attachments.splice(0);
      const files = metas.map(m => m.file).filter(Boolean);
      if (!files.length || !projectId) return;
      homeAssistant.uploadingAttachment = true;
      try {
        let placed = 0;
        if (targetNav === 'poster_brief') {
          placed += await autoFillPosterVisualAssetsFromFiles(files);
          placed += await uploadFilesToProjectKb(files, projectId);
          chat.history.push({
            role: 'assistant',
            content: `首页助手转交的 ${files.length} 个附件已归入本项目。图片已优先匹配到海报视觉素材，其余资料保存在项目知识库。`,
          });
        } else if (targetNav === 'copywriter') {
          for (const file of files) {
            moduleAutofill.files.push(file);
            moduleAutofill.fileMetas.push(compactFileMeta(file));
          }
          await uploadFilesToCopyKb(files);
          copyChat.history.push({
            role: 'assistant',
            content: `首页助手转交的 ${files.length} 个附件已进入当前海报文案资料队列，并归档到本项目的海报文案知识库。`,
          });
          placed += files.length;
        } else {
          placed += await uploadFilesToProjectKb(files, projectId);
        }
        if (placed) {
          homeAssistant.messages.push({ role: 'assistant', content: `已把 ${files.length} 个附件放入当前项目，不会与其他项目共用。` });
        }
      } finally {
        homeAssistant.uploadingAttachment = false;
      }
    }

    function handleCopyImportFileSelect(event) {
      const file = (event.target.files || [])[0];
      event.target.value = '';
      if (!file) return;
      copyImport.file = file;
      copyImport.fileName = file.name;
      copyImport.doc = null;
      showToast(`已选择文案文件：${file.name}`);
    }

    function assetTypeOptions() {
      return schemas.asset_types || [];
    }

    function assetTypeLabel(value) {
      const item = assetTypeOptions().find(x => x.value === value);
      return item?.label || value || '图片素材';
    }

    async function uploadCopyVisualAssets(event) {
      const files = Array.from(event.target.files || []);
      event.target.value = '';
      if (!files.length) return;
      copyImport.visualAssetsUploading = true;
      let ok = 0;
      for (const file of files) {
        try {
          const fd = new FormData();
          fd.append('file', file);
          fd.append('session_id', currentProject.value?.id || sessionId.value || 'default');
          fd.append('asset_type', copyImport.visualAssetType || 'module_content_image');
          fd.append('asset_label', copyImport.visualAssetLabel || assetTypeLabel(copyImport.visualAssetType));
          const r = await fetch('/api/upload', { method: 'POST', body: fd });
          const j = await r.json();
          if (!r.ok || !j.path) throw new Error(j.error || ('HTTP ' + r.status));
          copyImport.visualAssets.push({
            name: j.filename || file.name,
            path: j.path,
            url: j.url,
            asset_type: j.asset_type || copyImport.visualAssetType,
            asset_type_label: j.asset_type_label || assetTypeLabel(copyImport.visualAssetType),
            asset_label: j.asset_label || copyImport.visualAssetLabel || '',
          });
          ok++;
        } catch (e) {
          showToast(`${file.name} 上传失败：${e}`, 'error');
        }
      }
      copyImport.visualAssetsUploading = false;
      if (ok) showToast(`已上传 ${ok} 个视觉素材`);
    }

    function removeCopyVisualAsset(idx) {
      copyImport.visualAssets.splice(idx, 1);
    }

    async function runCopyImportUpload() {
      const file = copyImport.file;
      if (!file || !currentProject.value) {
        showToast('请先选择文案文件', 'error');
        return;
      }
      if (!modelConfigured('llm')) {
        showToast('请先配置大语言模型 API Key', 'error');
        openSettings();
        return;
      }

      copyImport.uploading = true;
      try {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('scope', 'function');
        fd.append('project_id', currentProject.value.id);
        fd.append('function_id', 'poster_brief');
        fd.append('kb_type', 'copy');
        const r = await fetch('/api/kb/upload', { method: 'POST', body: fd });
        const j = await r.json();
        if (!r.ok || j.error) throw new Error(j.error || ('HTTP ' + r.status));

        copyImport.doc = j;
        await fetchKbDocs();

        Object.keys(skillForm).forEach(k => delete skillForm[k]);
        skillForm.doc_id = j.id;
        skillForm.doc_scope = 'function';
        skillForm.project_id = currentProject.value.id;
        skillForm.function_id = 'poster_brief';
        skillForm.kb_type = 'copy';
        skillForm.extra = copyImport.extra || '';
        skillForm.global_bg_prompt = copyImport.globalBgPrompt || '';
        skillForm.hero_bg_prompt = copyImport.heroBgPrompt || '';
        skillForm.wordart_prompt = copyImport.wordartPrompt || '';
        skillForm.subtitle_text = copyImport.subtitleText || '';
        skillForm.title_visual_config = titleVisualPayload();
        skillForm.visual_assets = copyImport.visualAssets.map(a => ({
          path: a.path,
          name: a.name,
          asset_type: a.asset_type,
          asset_type_label: a.asset_type_label,
          asset_label: a.asset_label || '',
        }));
        skillForm.project_strategy = currentPosterStrategyPayload();
        await runSkill('poster_copy_import');
      } catch (e) {
        showToast('文案识别成图失败：' + e, 'error');
      } finally {
        copyImport.uploading = false;
      }
    }


    async function deleteKbDoc(d) {
      if (!confirm(`删除「${d.filename}」？AI 检索会失去这部分知识。`)) return;
      try {
        const params = new URLSearchParams({ scope: d.scope });
        if (d.project_id) params.append('project_id', d.project_id);
        if (d.function_id) params.append('function_id', d.function_id);
        if (d.kb_type) params.append('kb_type', d.kb_type);
        const r = await fetch('/api/kb/' + d.id + '?' + params, { method: 'DELETE' });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        await fetchKbDocs();
        showToast('已删除');
      } catch (e) {
        showToast('删除失败：' + e, 'error');
      }
    }

    function kbIcon(format) {
      const m = {
        txt: '📄', md: '📝', markdown: '📝', json: '🧩', html: '🌐', htm: '🌐',
        pdf: '📕', docx: '📘', pptx: '📊',
        csv: '📈', tsv: '📈', xlsx: '📗', xls: '📗',
        png: '🖼️', jpg: '🖼️', jpeg: '🖼️', webp: '🖼️', gif: '🖼️', bmp: '🖼️', svg: '🎨',
      };
      return m[format] || '📄';
    }

    function formatBytes(n) {
      if (!n) return '0';
      if (n < 1024) return n + ' B';
      if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
      return (n / 1024 / 1024).toFixed(1) + ' MB';
    }

    function setNavTab(tab) {
      navTab.value = tab;
      // 切到非 projects 时，强制切回 list view（detail 是 projects 的子视图）
      if (tab !== 'projects' && view.value === 'detail') {
        view.value = 'list';
      }
      // 切到 knowledge 拉文档列表
      if (tab === 'knowledge') fetchKbDocs();
    }

    function openNewProject() {
      newProjectForm.name = '';
      newProjectForm.description = '';
      newProjectForm.status = 'in_progress';
      newProjectForm.owner_name = '';
      newProjectForm.cover_id = null;
      newProjectForm.cover_theme = '#2563EB';
      newProjectForm.tags = [];
      newProjectForm.project_type = 'A';
      newProjectForm.scene = '';
      newProjectForm.poster_strategy = null;
      newProjectForm.function_projects = [];
      newProjectModal.uploadedDocs = [];
      newProjectModal.pendingFiles = [];
      newProjectModal.extracting = false;
      newProjectModal.coverBusy = false;
      newProjectModal.show = true;
    }

    function compactFileMeta(file) {
      return {
        id: `pending_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
        filename: file.name,
        size: file.size,
        format: (file.name.split('.').pop() || '').toLowerCase(),
        chunks_count: 0,
        file,
      };
    }

    function handleHomeAssistantAttachment(event) {
      const files = Array.from(event.target.files || []);
      event.target.value = '';
      if (!files.length) return;
      for (const file of files) {
        homeAssistant.attachments.push(compactFileMeta(file));
      }
      homeAssistant.messages.push({
        role: 'assistant',
        content: `已添加 ${files.length} 个附件。发送需求后，我会按目标项目和功能归档，不会进入其他项目。`,
      });
    }

    function removeHomeAssistantAttachment(index) {
      homeAssistant.attachments.splice(index, 1);
    }

    function toggleHomeVoiceInput() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        homeAssistant.messages.push({ role: 'assistant', content: '当前浏览器不支持语音输入，可以继续使用文字输入。' });
        return;
      }
      if (homeAssistant.recognition) {
        homeAssistant.recognition.stop();
        homeAssistant.recognition = null;
        homeAssistant.listening = false;
        return;
      }
      const recognition = new SpeechRecognition();
      recognition.lang = 'zh-CN';
      recognition.interimResults = true;
      recognition.continuous = false;
      recognition.onstart = () => { homeAssistant.listening = true; };
      recognition.onresult = event => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0]?.transcript || '';
        }
        if (transcript.trim()) homeAssistant.input = transcript.trim();
      };
      recognition.onerror = event => {
        homeAssistant.messages.push({ role: 'assistant', content: `语音输入失败：${event.error || '浏览器未授权'}` });
      };
      recognition.onend = () => {
        homeAssistant.listening = false;
        homeAssistant.recognition = null;
      };
      homeAssistant.recognition = recognition;
      recognition.start();
    }

    // 模态内文件上传：新项目未创建前只暂存在前端，创建后写入项目知识库
    async function uploadNpFiles(files) {
      if (!files || files.length === 0) return;
      for (const f of files) {
        const item = compactFileMeta(f);
        newProjectModal.pendingFiles.push(f);
        newProjectModal.uploadedDocs.push(item);
      }
    }

    function handleNpUpload(event) {
      const files = Array.from(event.target.files || []);
      uploadNpFiles(files);
      event.target.value = '';
    }

    function handleNpDrop(event) {
      newProjectModal.dragging = false;
      const files = Array.from(event.dataTransfer.files || []);
      uploadNpFiles(files);
    }

    async function removeNpDoc(d) {
      const i = newProjectModal.uploadedDocs.findIndex(x => x.id === d.id);
      if (i >= 0) newProjectModal.uploadedDocs.splice(i, 1);
      if (d.file) {
        const fi = newProjectModal.pendingFiles.indexOf(d.file);
        if (fi >= 0) newProjectModal.pendingFiles.splice(fi, 1);
      }
    }

    async function aiExtractFromDocs() {
      if (newProjectModal.pendingFiles.length === 0) {
        showToast('先上传至少一份文档', 'error');
        return;
      }
      newProjectModal.extracting = true;
      try {
        const fd = new FormData();
        newProjectModal.pendingFiles.forEach(f => fd.append('files', f));
        const r = await fetch('/api/kb/recognize-project-files', { method: 'POST', body: fd });
        const j = await r.json();
        if (!r.ok) {
          showToast(j.detail || j.error || ('HTTP ' + r.status), 'error');
          return;
        }
        applyRecognizedStrategyToNewProject(j);
        showToast('已识别项目类型、场景和模块编排，可继续修改');
      } catch (e) {
        showToast('知识库识别失败：' + e, 'error');
      } finally {
        newProjectModal.extracting = false;
      }
    }

    function applyRecognizedStrategyToNewProject(strategy) {
      if (!strategy) return;
      const ptype = strategy.project_type?.id || strategy.recognition?.project_type;
      const scene = strategy.scene?.id || strategy.recognition?.scene;
      if (ptype) newProjectForm.project_type = ptype;
      if (scene) newProjectForm.scene = scene;
      newProjectForm.poster_strategy = hydratePosterStrategy(strategy);
      newProjectForm.function_projects = (strategy.function_projects || []).map(x => ({
        ...x,
        poster_strategy: hydratePosterStrategy(x.poster_strategy),
      }));
      if (!newProjectForm.name && strategy.scene?.label) {
        newProjectForm.name = strategy.scene.label.replace(/^S\\w+\\s*·\\s*/, '') + '项目';
      }
      if (!newProjectForm.description && strategy.scene?.goal) {
        newProjectForm.description = strategy.scene.goal;
      }
    }

    async function cancelNewProject() {
      newProjectModal.show = false;
      newProjectModal.uploadedDocs = [];
      newProjectModal.pendingFiles = [];
    }

    async function submitNewProject() {
      const name = newProjectForm.name.trim();
      if (!name) return;
      newProjectModal.busy = true;
      try {
        if (!newProjectForm.cover_id) {
          await generateProjectCover('new', { silent: true });
        }
        const r = await fetch('/api/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name,
            description: newProjectForm.description.trim(),
            status: newProjectForm.status,
            owner: newProjectForm.owner_name.trim()
              ? { name: newProjectForm.owner_name.trim(), initial: newProjectForm.owner_name.trim()[0] }
              : undefined,
            cover_id: newProjectForm.cover_id,
            project_type: newProjectForm.project_type,
            scene: '',
            poster_strategy: null,
          }),
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const created = await r.json();
        for (const f of newProjectModal.pendingFiles) {
          try {
            const fd = new FormData();
            fd.append('file', f);
            fd.append('scope', 'project');
            fd.append('project_id', created.id);
            await fetch('/api/kb/upload', { method: 'POST', body: fd });
          } catch (e) {
            showToast(`${f.name} 写入项目知识库失败：${e}`, 'error');
          }
        }
        await fetchProjects();
        fetchKbDocs();
        newProjectModal.show = false;
        newProjectModal.uploadedDocs = [];
        newProjectModal.pendingFiles = [];
        showToast('已创建项目');
        await goDetail(created.id);
      } catch (e) {
        showToast('创建失败：' + e, 'error');
      } finally {
        newProjectModal.busy = false;
      }
    }

    async function fetchPosterFunctionProjects() {
      if (!currentProject.value?.id) return;
      posterFunctionProjectsLoading.value = true;
      try {
        const r = await fetch(`/api/projects/${currentProject.value.id}/function-projects/poster_brief`);
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || j.error || ('HTTP ' + r.status));
        posterFunctionProjects.value = (j.items || []).map(item => ({
          ...item,
          poster_strategy: item.poster_strategy ? hydratePosterStrategy(item.poster_strategy) : null,
        }));
        const validIds = new Set(posterFunctionProjects.value.map(item => item.id));
        selectedPosterFunctionProjectIds.value = selectedPosterFunctionProjectIds.value.filter(id => validIds.has(id));
        if (currentPosterFunctionProject.value) {
          const fresh = posterFunctionProjects.value.find(x => x.id === currentPosterFunctionProject.value.id);
          currentPosterFunctionProject.value = fresh || null;
        }
        if (!currentPosterFunctionProject.value && posterFunctionProjects.value.length === 1) {
          loadPosterFunctionProject(posterFunctionProjects.value[0]);
        }
      } catch (e) {
        showToast('加载海报功能项目失败：' + e, 'error');
      } finally {
        posterFunctionProjectsLoading.value = false;
      }
    }

    function loadPosterFunctionProject(item) {
      if (!item) return;
      currentPosterFunctionProject.value = item;
      posterEditDirty.value = false;
      posterFunctionNameEditing.value = false;
      posterFunctionNameBeforeEdit.value = item.name || '';
      if (item.poster_strategy) {
        posterStrategy.value = hydratePosterStrategy(item.poster_strategy);
        posterStrategySelection.project_type = posterStrategy.value?.project_type?.id || item.project_type || posterStrategySelection.project_type;
        posterStrategySelection.scene = posterStrategy.value?.scene?.id || item.scene || posterStrategySelection.scene;
        applyTitleVisualConfig(posterStrategy.value?.title_visual_config || {});
      }
      resetSkillStream();
      if (detailNav.value === 'copywriter') restoreCopyDraftForCurrentPoster();
    }

    async function requestLoadPosterFunctionProject(item) {
      if (!item) return;
      if (currentPosterFunctionProject.value?.id === item.id) return;
      if (posterEditDirty.value) {
        const choice = await askChoice({
          title: '切换海报子项目？',
          message: '当前海报子项目有未保存编辑。切换前是否保存当前内容？',
          primaryLabel: '保存并切换',
          secondaryLabel: '不保存直接切换',
        });
        if (choice === 'primary') {
          await saveCurrentPosterEdit();
        }
      }
      loadPosterFunctionProject(item);
    }

    function startPosterFunctionNameEdit() {
      if (!currentPosterFunctionProject.value) return;
      posterFunctionNameBeforeEdit.value = currentPosterFunctionProject.value.name || '';
      posterFunctionNameEditing.value = true;
      setTimeout(() => {
        const el = document.querySelector('.strategy-title-input');
        if (el) {
          el.focus();
          el.select?.();
        }
      }, 0);
    }

    async function finishPosterFunctionNameEdit() {
      if (!currentPosterFunctionProject.value) return;
      const nextName = (currentPosterFunctionProject.value.name || '').trim();
      if (!nextName) {
        currentPosterFunctionProject.value.name = posterFunctionNameBeforeEdit.value || '未命名海报子项目';
      }
      posterFunctionNameEditing.value = false;
      if ((currentPosterFunctionProject.value.name || '') !== posterFunctionNameBeforeEdit.value) {
        try {
          await saveProjectPosterStrategy();
        } catch (e) {
          currentPosterFunctionProject.value.name = posterFunctionNameBeforeEdit.value;
        }
      }
    }

    function cancelPosterFunctionNameEdit() {
      if (currentPosterFunctionProject.value) {
        currentPosterFunctionProject.value.name = posterFunctionNameBeforeEdit.value;
      }
      posterFunctionNameEditing.value = false;
    }

    async function createPosterFunctionProjects(pid, items) {
      if (!pid || !items?.length) return [];
      const r = await fetch(`/api/projects/${pid}/function-projects/poster_brief`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || j.error || ('HTTP ' + r.status));
      return j.items || [];
    }

    async function createPosterFunctionProjectFromSelection(projectType, sceneKey) {
      if (!currentProject.value) return;
      try {
        if (posterEditDirty.value) {
          await saveCurrentPosterEdit();
        }
        const r = await fetch('/api/poster-strategies/resolve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ project_type: projectType, scene: sceneKey }),
        });
        const strategyJson = await r.json();
        if (!r.ok) throw new Error(strategyJson.detail || strategyJson.error || ('HTTP ' + r.status));
        const strategy = hydratePosterStrategy(strategyJson);
        const sceneLabel = strategy.scene?.label?.replace(/^S\w+\s*·\s*/, '') || '海报项目';
        const created = await createPosterFunctionProjects(currentProject.value.id, [{
          name: `${sceneLabel} ${posterFunctionProjects.value.length + 1}`,
          description: strategy.scene?.goal || '',
          project_type: strategy.project_type?.id || projectType || 'A',
          scene: strategy.scene?.id || sceneKey || 'S1',
          poster_strategy: strategy,
          source: { mode: 'strategy_change_new_project' },
        }]);
        await fetchPosterFunctionProjects();
        const item = posterFunctionProjects.value.find(x => x.id === created[0]?.id);
        if (item) loadPosterFunctionProject(item);
        showToast('已新建海报子项目，当前编辑内容未被覆盖');
      } catch (e) {
        showToast('新建海报子项目失败：' + e, 'error');
      }
    }

    function allowedPosterFunctionCreateScenes() {
      const type = posterStrategies.project_types.find(t => t.id === posterFunctionCreate.project_type);
      const keys = type?.allowed_scenes || [];
      return keys.map(k => ({ key: k, ...(posterStrategies.scenes[k] || {}) }));
    }

    async function resolvePosterFunctionCreateStrategy() {
      try {
        const r = await fetch('/api/poster-strategies/resolve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_type: posterFunctionCreate.project_type,
            scene: posterFunctionCreate.scene,
          }),
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || j.error || ('HTTP ' + r.status));
        posterFunctionCreate.strategy = hydratePosterStrategy(j);
        if (!posterFunctionCreate.name.trim()) {
          const sceneLabel = j.scene?.label?.replace(/^S\w+\s*·\s*/, '') || '海报项目';
          posterFunctionCreate.name = `${sceneLabel} ${posterFunctionProjects.value.length + 1}`;
        }
      } catch (e) {
        showToast('解析海报子项目类型失败：' + e, 'error');
      }
    }

    async function selectPosterFunctionCreateType(typeId) {
      posterFunctionCreate.project_type = typeId;
      const type = posterStrategies.project_types.find(t => t.id === typeId);
      if (type && !type.allowed_scenes.includes(posterFunctionCreate.scene)) {
        posterFunctionCreate.scene = type.allowed_scenes[0];
      }
      posterFunctionCreate.name = '';
      await resolvePosterFunctionCreateStrategy();
    }

    async function selectPosterFunctionCreateScene(sceneKey) {
      posterFunctionCreate.scene = sceneKey;
      posterFunctionCreate.name = '';
      await resolvePosterFunctionCreateStrategy();
    }

    function posterFunctionCreateTypeMeta(typeId) {
      const map = {
        A: { icon: 'A', title: 'A 型', tone: '#2563EB', visual: '蓝图型' },
        B: { icon: 'B', title: 'B 型', tone: '#7C3AED', visual: '成长型' },
        C: { icon: 'C', title: 'C 型', tone: '#0891B2', visual: '成果型' },
      };
      return map[typeId] || { icon: typeId || 'T', title: `${typeId || '-'} 型`, tone: '#2563EB', visual: '自定义' };
    }

    function posterFunctionCreateSceneMeta(sceneKey) {
      const idx = Number(String(sceneKey || '').match(/\d+/)?.[0] || 1);
      const colors = ['#2563EB', '#7C3AED', '#0891B2', '#F97316', '#059669', '#DB2777', '#4F46E5', '#0F766E'];
      const icons = ['开', '招', '课', '评', '果', '荣', '宣', '复'];
      return {
        color: colors[(idx - 1) % colors.length],
        icon: icons[(idx - 1) % icons.length],
      };
    }

    async function openPosterFunctionCreate() {
      posterFunctionCreate.show = true;
      posterFunctionCreate.busy = false;
      posterFunctionCreate.project_type = currentPosterFunctionProject.value?.project_type
        || posterStrategy.value?.project_type?.id
        || 'A';
      const type = posterStrategies.project_types.find(t => t.id === posterFunctionCreate.project_type);
      const currentScene = currentPosterFunctionProject.value?.scene || posterStrategy.value?.scene?.id || 'S1';
      posterFunctionCreate.scene = type?.allowed_scenes?.includes(currentScene) ? currentScene : (type?.allowed_scenes?.[0] || 'S1');
      posterFunctionCreate.name = '';
      posterFunctionCreate.strategy = null;
      await resolvePosterFunctionCreateStrategy();
    }

    function cancelPosterFunctionCreate() {
      posterFunctionCreate.show = false;
      posterFunctionCreate.busy = false;
    }

    async function createBlankPosterFunctionProject() {
      if (!currentProject.value) return;
      const strategy = posterFunctionCreate.strategy || posterStrategy.value || posterStrategies.default;
      posterFunctionCreate.busy = true;
      try {
        const created = await createPosterFunctionProjects(currentProject.value.id, [{
          name: posterFunctionCreate.name.trim() || `新海报项目 ${posterFunctionProjects.value.length + 1}`,
          description: strategy?.scene?.goal || '',
          project_type: strategy?.project_type?.id || 'A',
          scene: strategy?.scene?.id || 'S1',
          poster_strategy: strategy,
          source: { mode: 'manual' },
        }]);
        await fetchPosterFunctionProjects();
        const item = posterFunctionProjects.value.find(x => x.id === created[0]?.id);
        if (item) loadPosterFunctionProject(item);
        posterFunctionCreate.show = false;
        showToast('已创建海报子项目');
      } catch (e) {
        showToast('创建海报子项目失败：' + e, 'error');
      } finally {
        posterFunctionCreate.busy = false;
      }
    }

    async function deletePosterFunctionProject(item) {
      if (!currentProject.value || !item) return;
      if (!confirm(`删除海报子项目「${item.name}」？`)) return;
      try {
        const r = await fetch(`/api/projects/${currentProject.value.id}/function-projects/poster_brief/${item.id}`, { method: 'DELETE' });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        if (currentPosterFunctionProject.value?.id === item.id) currentPosterFunctionProject.value = null;
        await fetchPosterFunctionProjects();
        showToast('已删除海报子项目');
      } catch (e) {
        showToast('删除失败：' + e, 'error');
      }
    }

    function isPosterFunctionProjectSelected(item) {
      return !!item && selectedPosterFunctionProjectIds.value.includes(item.id);
    }

    function togglePosterFunctionProjectSelection(item) {
      if (!item?.id) return;
      if (selectedPosterFunctionProjectIds.value.includes(item.id)) {
        selectedPosterFunctionProjectIds.value = selectedPosterFunctionProjectIds.value.filter(id => id !== item.id);
      } else {
        selectedPosterFunctionProjectIds.value = [...selectedPosterFunctionProjectIds.value, item.id];
      }
    }

    function selectAllPosterFunctionProjects() {
      selectedPosterFunctionProjectIds.value = posterFunctionProjects.value.map(item => item.id);
    }

    function clearPosterFunctionProjectSelection() {
      selectedPosterFunctionProjectIds.value = [];
    }

    async function deleteSelectedPosterFunctionProjects() {
      if (!currentProject.value) return;
      const ids = [...new Set(selectedPosterFunctionProjectIds.value)];
      if (!ids.length) {
        showToast('请先选择要删除的海报子项目', 'error');
        return;
      }
      if (!confirm(`确认批量删除 ${ids.length} 个海报子项目？模块编排和草稿会一并移除。`)) return;
      try {
        for (const id of ids) {
          const r = await fetch(`/api/projects/${currentProject.value.id}/function-projects/poster_brief/${id}`, { method: 'DELETE' });
          if (!r.ok) throw new Error('HTTP ' + r.status);
        }
        if (ids.includes(currentPosterFunctionProject.value?.id)) {
          currentPosterFunctionProject.value = null;
          posterStrategy.value = null;
        }
        selectedPosterFunctionProjectIds.value = [];
        await fetchPosterFunctionProjects();
        showToast(`已删除 ${ids.length} 个海报子项目`);
      } catch (e) {
        showToast('批量删除失败：' + e, 'error');
      }
    }

    async function autoFillCurrentPosterModulesFromKb() {
      if (!currentProject.value || !currentPosterFunctionProject.value || !posterStrategy.value) return 0;
      if (!modelConfigured('llm')) return 0;
      const payload = currentPosterStrategyPayload();
      const r = await fetch(`/api/projects/${currentProject.value.id}/function-projects/poster_brief/${currentPosterFunctionProject.value.id}/generate-copy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_strategy: payload,
          module_plan: payload.module_plan || [],
          requirement: '基于项目知识库自动填写当前海报模块内容。必须忠实使用知识库原文和结构，不自由扩写；图片素材按已上传的视觉素材和文件名关系匹配到合适模块。',
          overwrite_mode: 'fill_empty',
        }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || j.error || ('HTTP ' + r.status));
      const changed = applyModuleAutofillUpdates(j.updates || []);
      if (j.subtitle) copyImport.subtitleText = j.subtitle;
      await saveProjectPosterStrategy();
      return changed;
    }

    async function recognizeCurrentProjectKb() {
      if (!currentProject.value) return;
      try {
        const r = await fetch('/api/kb/recognize-project', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ project_id: currentProject.value.id }),
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || j.error || ('HTTP ' + r.status));
        const items = (j.function_projects || []).map(x => ({
          ...x,
          poster_strategy: hydratePosterStrategy(x.poster_strategy),
        }));
        if (items.length) {
          const created = await createPosterFunctionProjects(currentProject.value.id, items);
          await fetchPosterFunctionProjects();
          let filled = 0;
          let fillFailed = 0;
          if (modelConfigured('llm')) {
            for (const createdItem of created) {
              const item = posterFunctionProjects.value.find(x => x.id === createdItem.id);
              if (!item) continue;
              loadPosterFunctionProject(item);
              try {
                filled += await autoFillCurrentPosterModulesFromKb();
              } catch (err) {
                fillFailed++;
              }
            }
          }
          const first = posterFunctionProjects.value.find(x => x.id === created[0]?.id) || posterFunctionProjects.value[0];
          if (first) loadPosterFunctionProject(first);
          if (!modelConfigured('llm')) {
            showToast(`已识别并创建 ${items.length} 个海报子项目；LLM 未配置，暂未自动填写模块内容`);
          } else {
            showToast(`已识别并创建 ${items.length} 个海报子项目，并自动填写 ${filled} 个模块${fillFailed ? ` · ${fillFailed} 个子项目填写失败` : ''}`);
          }
        } else {
          posterStrategy.value = hydratePosterStrategy(j);
          posterStrategySelection.project_type = j.project_type?.id || j.recognition?.project_type || posterStrategySelection.project_type;
          posterStrategySelection.scene = j.scene?.id || j.recognition?.scene || posterStrategySelection.scene;
          await saveProjectPosterStrategy();
          let filled = 0;
          if (modelConfigured('llm')) {
            try {
              filled = await autoFillCurrentPosterModulesFromKb();
            } catch (err) {
              showToast('模块内容自动填写失败：' + err, 'error');
            }
          }
          showToast(modelConfigured('llm')
            ? `已根据项目知识库识别并生成模块编排，自动填写 ${filled} 个模块`
            : '已根据项目知识库识别并生成模块编排；LLM 未配置，暂未自动填写模块内容');
        }
      } catch (e) {
        showToast('项目知识库识别失败：' + e, 'error');
      }
    }

    async function saveProjectPosterStrategy(options = {}) {
      if (!currentProject.value || !posterStrategy.value) return;
      const silent = !!options.silent;
      const forceSave = !!options.force;
      if (!forceSave) {
        posterEditDirty.value = true;
        markPosterPreviewDirty();
        return;
      }
      try {
        const payload = currentPosterStrategyPayload();
        const url = currentPosterFunctionProject.value
          ? `/api/projects/${currentProject.value.id}/function-projects/poster_brief/${currentPosterFunctionProject.value.id}`
          : '/api/projects/' + currentProject.value.id;
        const body = currentPosterFunctionProject.value
          ? {
              poster_strategy: payload,
              project_type: payload?.project_type?.id,
              scene: payload?.scene?.id,
              name: currentPosterFunctionProject.value.name,
              description: currentPosterFunctionProject.value.description,
            }
          : {
              poster_strategy: payload,
              project_type: payload?.project_type?.id,
              scene: payload?.scene?.id,
            };
        const r = await fetch(url, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        posterEditDirty.value = false;
        if (currentPosterFunctionProject.value && !silent) {
          const saved = await r.json();
          currentPosterFunctionProject.value = {
            ...saved,
            poster_strategy: saved.poster_strategy ? hydratePosterStrategy(saved.poster_strategy) : null,
          };
          await fetchPosterFunctionProjects();
        } else if (!currentPosterFunctionProject.value && !silent) {
          await fetchProject(currentProject.value.id);
        }
        if (!silent) showToast(currentPosterFunctionProject.value ? '模块编排已保存到海报子项目' : '模块编排已保存到项目');
      } catch (e) {
        if (!silent) showToast('保存模块编排失败：' + e, 'error');
        throw e;
      }
    }

    async function saveCurrentPosterEdit() {
      if (!currentProject.value || !posterStrategy.value) return;
      try {
        skillStream.autoSaving = true;
        await saveProjectPosterStrategy({ force: true });
      } finally {
        skillStream.autoSaving = false;
      }
    }

    function projectDetailBannerStyle(project) {
      const tone = project?.cover_tone || '#2563EB';
      if (project?.cover_url) {
        return {
          backgroundImage: `linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,.76) 26%, #FFFFFF 48%), url("${project.cover_url}")`,
          backgroundColor: '#FFFFFF',
        };
      }
      return {
        backgroundImage: `linear-gradient(90deg, ${tone} 0%, rgba(255,255,255,.86) 30%, #FFFFFF 54%)`,
        backgroundColor: '#FFFFFF',
      };
    }

    function toggleMenu(pid) {
      menuOpenFor.value = menuOpenFor.value === pid ? null : pid;
    }

    function toggleDetailStatusMenu() {
      detailStatusMenuOpen.value = !detailStatusMenuOpen.value;
    }

    async function changeStatus(p, newStatus) {
      if (p.status === newStatus) {
        menuOpenFor.value = null;
        return;
      }
      try {
        const r = await fetch('/api/projects/' + p.id, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus }),
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        // 列表里更新
        p.status = newStatus;
        // 当前详情同步
        if (currentProject.value && currentProject.value.id === p.id) {
          currentProject.value.status = newStatus;
        }
        // 重拉列表（统计卡刷新）
        fetchProjects();
        showToast('已更新状态');
      } catch (e) {
        showToast('更新失败：' + e, 'error');
      } finally {
        menuOpenFor.value = null;
      }
    }

    // 计算属性：过滤后的项目
    const filteredProjects = computed(() => {
      let arr = projects.value;
      // 搜索过滤
      const q = searchQuery.value.trim().toLowerCase();
      if (q) {
        arr = arr.filter(p =>
          (p.name || '').toLowerCase().includes(q) ||
          (p.description || '').toLowerCase().includes(q) ||
          (p.owner?.name || '').toLowerCase().includes(q)
        );
      }
      // tab 过滤
      if (filterTab.value === 'week_updated') {
        const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
        arr = arr.filter(p => new Date(p.updated_at || p.created_at || 0).getTime() >= weekAgo);
      } else if (filterTab.value !== 'all') {
        arr = arr.filter(p => p.status === filterTab.value);
      }
      return arr;
    });

    // 首页统一项目橱窗：进行中、待启动、已归档都按筛选条件进入同一网格
    const activeProjects = computed(() => {
      return filteredProjects.value;
    });
    const archivedProjects = computed(() => {
      if (filterTab.value === 'in_progress' || filterTab.value === 'pending') return [];
      return filteredProjects.value.filter(p => p.status === 'archived');
    });

    function tabCount(key) {
      if (key === 'all') return projects.value.length;
      if (key === 'week_updated') return projectStats.week_updated || projects.value.filter(p => {
        const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
        return new Date(p.updated_at || p.created_at || 0).getTime() >= weekAgo;
      }).length;
      return projects.value.filter(p => p.status === key).length;
    }

    function homeAssistantTargetNav(text) {
      if (homeAssistant.mode === 'poster') {
        if (/文案|copy|写|生成稿|改稿/i.test(text)) return 'copywriter';
        return 'poster_brief';
      }
      if (homeAssistant.mode === 'report') return 'overview';
      if (homeAssistant.mode !== 'project') return homeAssistant.mode;
      if (/海报.*文案|文案.*海报|文案|copy/i.test(text)) return 'copywriter';
      if (/海报|生图|出图|图片|poster/i.test(text)) return 'poster_brief';
      if (/访谈|interview/i.test(text)) return 'interview_outline';
      if (/研究|报告|report/i.test(text)) return 'overview';
      if (/ppt|幻灯|课件/i.test(text)) return 'ppt_outline';
      if (/知识库|资料|素材/i.test(text)) return 'kb';
      return 'overview';
    }

    function findProjectByAssistantText(text) {
      const q = text.trim().toLowerCase();
      if (!q) return null;
      return projects.value.find(p => q.includes(String(p.name || '').toLowerCase()))
        || projects.value.find(p => String(p.name || '').toLowerCase().includes(q))
        || projects.value.find(p => q.includes(String(p.owner?.name || '').toLowerCase()));
    }

    async function sendHomeAssistant() {
      const text = homeAssistant.input.trim();
      const attachmentMetas = homeAssistant.attachments.map(f => ({
        filename: f.filename,
        size: f.size,
        format: f.format,
      }));
      if ((!text && !attachmentMetas.length) || homeAssistant.busy) return;
      homeAssistant.input = '';
      homeAssistant.pendingPrompt = text || `请读取并安排 ${attachmentMetas.length} 个附件`;
      homeAssistant.messages.push({
        role: 'user',
        content: text || `上传了 ${attachmentMetas.length} 个附件，请判断应该进入哪个项目/功能。`,
      });
      if (!modelConfigured('llm')) {
        homeAssistant.reply = '需要先配置 LLM，才能用 AI 助手理解并跳转。';
        homeAssistant.messages.push({ role: 'assistant', content: homeAssistant.reply });
        openSettings();
        return;
      }
      homeAssistant.busy = true;
      try {
        const routeMessage = text || `请读取并安排这些附件：${attachmentMetas.map(f => f.filename).join('、')}`;
        const r = await fetch('/api/home-assistant/route', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            mode: 'auto',
            message: routeMessage,
            projects: projects.value.map(p => ({
              id: p.id,
              name: p.name,
              status: p.status,
              owner: p.owner,
              updated_at: p.updated_at,
            })),
            attachments: attachmentMetas,
          }),
        });
        const action = await r.json();
        if (!r.ok) throw new Error(action.detail || action.error || ('HTTP ' + r.status));
        await applyHomeAssistantAction(action);
      } catch (e) {
        homeAssistant.reply = 'AI 助手理解失败：' + e;
        homeAssistant.messages.push({ role: 'assistant', content: homeAssistant.reply });
      } finally {
        homeAssistant.busy = false;
      }
    }

    async function applyHomeAssistantAction(action) {
      const intent = action?.intent || 'ask_clarify';
      const targetFunction = action?.target_function || 'overview';
      if (intent === 'create_project') {
        openNewProject();
        if (action.project_name) newProjectForm.name = action.project_name;
        if (action.owner_name) newProjectForm.owner_name = action.owner_name;
        if (['A', 'B', 'C'].includes(action.project_type)) newProjectForm.project_type = action.project_type;
        if (/^#[0-9a-fA-F]{6}$/.test(action.theme_color || '')) newProjectForm.cover_theme = action.theme_color;
        if (homeAssistant.attachments.length) {
          const pending = homeAssistant.attachments.splice(0);
          for (const item of pending) {
            if (item.file) {
              newProjectModal.pendingFiles.push(item.file);
              newProjectModal.uploadedDocs.push(compactFileMeta(item.file));
            }
          }
        }
        if (action.project_name || action.owner_name || action.theme_color || action.project_type) {
          newProjectModal.aiDraftPrompt = homeAssistant.pendingPrompt;
        }
        homeAssistant.reply = action.reply || '已打开新建项目面板。';
        homeAssistant.messages.push({ role: 'assistant', content: homeAssistant.reply });
        return;
      }
      if (intent === 'filter_recent') {
        filterTab.value = 'week_updated';
        homeAssistant.reply = action.reply || '已切到本周更新项目。';
        homeAssistant.messages.push({ role: 'assistant', content: homeAssistant.reply });
        return;
      }
      if ((intent === 'open_project' || intent === 'open_project_function') && action.target_project_id) {
        await goDetail(action.target_project_id);
        setDetailNav(targetFunction === 'report' ? 'overview' : targetFunction);
        await placeHomeAssistantAttachments(detailNav.value, action.target_project_id);
        await forwardHomeAssistantPromptToFeature(detailNav.value, homeAssistant.pendingPrompt);
        homeAssistant.reply = action.reply || `已进入${skillLabelOf(detailNav.value)}。`;
        homeAssistant.messages.push({ role: 'assistant', content: homeAssistant.reply });
        return;
      }
      homeAssistant.reply = action.reply || '我还需要你补充要打开哪个项目或要创建什么项目。';
      homeAssistant.messages.push({ role: 'assistant', content: homeAssistant.reply });
    }

    async function forwardHomeAssistantPromptToFeature(targetNav, prompt) {
      const text = (prompt || '').trim();
      if (!text) return;
      rememberProjectAssistantHandoff(targetNav, text);
      await nextTick();
      if (targetNav === 'poster_brief') {
        chat.history.push({ role: 'assistant', content: `已接收首页助手转交的需求：${text}` });
        chat.input = text;
        nextTick(() => sendMessage());
        saveCurrentProjectAssistantMemory();
        return;
      }
      if (targetNav === 'copywriter') {
        copyChat.history.push({ role: 'assistant', content: `已接收首页助手转交的需求：${text}` });
        copyChat.input = text;
        scrollCopyChatToBottom();
        if (currentPosterFunctionProject.value) {
          nextTick(() => sendCopyChatMessage());
        }
        saveCurrentProjectAssistantMemory();
        return;
      }
      if (['interview_outline', 'ppt_outline', 'kb', 'overview'].includes(targetNav)) {
        showToast('已带着首页助手需求进入当前功能');
        saveCurrentProjectAssistantMemory();
      }
    }

    const platformKbDocs = computed(() => kb.docs.filter(d => d.scope === 'global'));

    // 项目级文档：只读 scope=project，本项目内部不混入平台通用或功能知识库
    const projectKbDocs = computed(() => {
      if (!currentProject.value) return [];
      const pid = currentProject.value.id;
      return kb.docs.filter(d => d.scope === 'project' && d.project_id === pid);
    });

    function functionKbDocs(functionId, kbType) {
      if (!currentProject.value) return [];
      const pid = currentProject.value.id;
      return kb.docs.filter(d =>
        d.scope === 'function' &&
        d.project_id === pid &&
        d.function_id === functionId &&
        d.kb_type === kbType
      );
    }

    const posterCopyKbDocs = computed(() => functionKbDocs('poster_brief', 'copy'));
    const posterImageKbDocs = computed(() => functionKbDocs('poster_brief', 'image'));

    function ownerColorClass(name) {
      if (!name) return 'avatar-c0';
      let hash = 0;
      for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) & 0xffff;
      return 'avatar-c' + (hash % 6);
    }

    function relativeTime(iso) {
      if (!iso) return '-';
      const d = new Date(iso);
      const diff = (Date.now() - d.getTime()) / 1000;
      if (diff < 60) return '刚刚';
      if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前';
      if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前';
      if (diff < 86400 * 7) return Math.floor(diff / 86400) + ' 天前';
      if (diff < 86400 * 30) return Math.floor(diff / 86400 / 7) + ' 周前';
      const pad = n => String(n).padStart(2, '0');
      return `${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())}`;
    }

    function skillIcon(skill) { return SKILL_ICON[skill] || '✨'; }
    function skillIconClass(skill) {
      return skill === 'design_brief' ? 'brief'
        : skill === 'copywriter' ? 'copy'
        : ['poster_render', 'poster_brief', 'poster_copy_import'].includes(skill) ? 'render' : '';
    }

    // 占位提示（编辑信息 / 保存为模板等 v0.3 才做）
    function alert(msg) { showToast(msg, 'success'); }

    // 设置抽屉
    const settingsOpen = ref(false);
    const config = reactive({
      deepseek_api_key_masked: '',
      deepseek_api_key_set: false,
      deepseek_base_url: '',
      deepseek_model: '',
      llm_provider: 'deepseek',
      llm_api_key_masked: '',
      llm_api_key_set: false,
      llm_base_url: '',
      llm_model: '',
      image_provider: 'openai',
      image_api_key_masked: '',
      image_api_key_set: false,
      image_base_url: '',
      image_model: '',
      llm_presets: {},
      image_presets: {},
      key_from_env: false,
      image_key_from_env: false,
    });
    const settingsDraft = reactive({
      llm_api_key: '',
      llm_provider: 'deepseek',
      llm_base_url: '',
      llm_model: '',
      image_api_key: '',
      image_provider: 'openai',
      image_base_url: '',
      image_model: '',
      // old aliases kept for compatibility
      deepseek_api_key: '',
      deepseek_base_url: '',
      deepseek_model: '',
    });
    const settingsTest = reactive({ busy: false, result: null });
    const settingsSaving = ref(false);

    async function fetchConfig() {
      try {
        const r = await fetch('/api/config');
        const j = await r.json();
        Object.assign(config, j);
      } catch (e) { /* 静默 */ }
    }

    function modelConfigured(kind) {
      if (kind === 'image') {
        return !!(config.image_api_key_set || config.image_key_from_env || config.image_provider === 'comfyui');
      }
      return !!(config.llm_api_key_set || config.deepseek_api_key_set || config.key_from_env);
    }

    function modelStatusText(kind) {
      if (kind === 'image') {
        const label = config.image_provider || '生图';
        const model = config.image_model || '未选模型';
        return `${modelConfigured('image') ? '生图已配置' : '生图未配置'} · ${label} / ${model}`;
      }
      const label = config.llm_provider || 'LLM';
      const model = config.llm_model || config.deepseek_model || '未选模型';
      return `${modelConfigured('llm') ? 'LLM已配置' : 'LLM未配置'} · ${label} / ${model}`;
    }

    function allModelStatusText() {
      return `${modelStatusText('llm')} ｜ ${modelStatusText('image')}`;
    }

    async function openSettings() {
      await fetchConfig();
      settingsDraft.llm_api_key = '';  // 始终空，留空 = 不变
      settingsDraft.llm_provider = config.llm_provider || 'deepseek';
      settingsDraft.llm_base_url = config.llm_base_url || config.deepseek_base_url || '';
      settingsDraft.llm_model = config.llm_model || config.deepseek_model || '';
      settingsDraft.image_api_key = '';
      settingsDraft.image_provider = config.image_provider || 'openai';
      settingsDraft.image_base_url = config.image_base_url || '';
      settingsDraft.image_model = config.image_model || '';
      settingsDraft.deepseek_api_key = '';
      settingsDraft.deepseek_base_url = settingsDraft.llm_base_url;
      settingsDraft.deepseek_model = settingsDraft.llm_model;
      settingsTest.result = null;
      settingsOpen.value = true;
    }

    function closeSettings() { settingsOpen.value = false; }

    function presetList(kind) {
      const src = kind === 'image' ? (config.image_presets || {}) : (config.llm_presets || {});
      return Object.entries(src).map(([value, meta]) => ({ value, ...(meta || {}) }));
    }

    function applyModelPreset(kind) {
      if (kind === 'image') {
        const meta = (config.image_presets || {})[settingsDraft.image_provider] || {};
        if (meta.base_url !== undefined) settingsDraft.image_base_url = meta.base_url || '';
        if (meta.model !== undefined) settingsDraft.image_model = meta.model || '';
      } else {
        const meta = (config.llm_presets || {})[settingsDraft.llm_provider] || {};
        if (meta.base_url !== undefined) settingsDraft.llm_base_url = meta.base_url || '';
        if (meta.model !== undefined) settingsDraft.llm_model = meta.model || '';
      }
    }

    async function testImageSettings() {
      settingsTest.busy = true;
      settingsTest.result = null;
      try {
        const r = await fetch('/api/config/image-test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_api_key: settingsDraft.image_api_key || undefined,
            image_provider: settingsDraft.image_provider,
            image_base_url: settingsDraft.image_base_url || undefined,
            image_model: settingsDraft.image_model || undefined,
          }),
        });
        settingsTest.result = await r.json();
      } catch (e) {
        settingsTest.result = { ok: false, error: String(e) };
      } finally {
        settingsTest.busy = false;
      }
    }

    async function testSettings() {
      settingsTest.busy = true;
      settingsTest.result = null;
      try {
        const r = await fetch('/api/config/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            // 如果用户填了新 key，用新 key 测；否则用已存的 key（后端会读 config）
            llm_api_key: settingsDraft.llm_api_key || undefined,
            llm_provider: settingsDraft.llm_provider,
            llm_base_url: settingsDraft.llm_base_url || undefined,
            llm_model: settingsDraft.llm_model || undefined,
          }),
        });
        settingsTest.result = await r.json();
      } catch (e) {
        settingsTest.result = { ok: false, error: String(e) };
      } finally {
        settingsTest.busy = false;
      }
    }

    async function saveSettings() {
      settingsSaving.value = true;
      try {
        const r = await fetch('/api/config', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            llm_api_key: settingsDraft.llm_api_key,  // 空字符串 = 不变
            llm_provider: settingsDraft.llm_provider,
            llm_base_url: settingsDraft.llm_base_url,
            llm_model: settingsDraft.llm_model,
            image_api_key: settingsDraft.image_api_key,
            image_provider: settingsDraft.image_provider,
            image_base_url: settingsDraft.image_base_url,
            image_model: settingsDraft.image_model,
            // old aliases kept for older backend fields
            deepseek_api_key: settingsDraft.llm_api_key,
            deepseek_base_url: settingsDraft.llm_base_url,
            deepseek_model: settingsDraft.llm_model,
          }),
        });
        const j = await r.json();
        Object.assign(config, j);
        showToast('已保存');
        // 刷新 chat health 状态
        checkChatHealth();
      } catch (e) {
        showToast('保存失败：' + e, 'error');
      } finally {
        settingsSaving.value = false;
      }
    }

    async function fetchProjects() {
      try {
        const r = await fetch('/api/projects');
        const j = await r.json();
        projects.value = j.projects || [];
        if (j.stats) Object.assign(projectStats, j.stats);
      } catch (e) {
        showToast('加载项目列表失败：' + e, 'error');
      }
    }

    async function fetchCovers() {
      try {
        const r = await fetch('/api/covers');
        const j = await r.json();
        covers.value = j.covers || [];
      } catch (e) { /* silent */ }
    }

    async function generateProjectCover(target = 'new', opts = {}) {
      const form = target === 'edit' ? projectEditModal : newProjectForm;
      const modal = target === 'edit' ? projectEditModal : newProjectModal;
      const name = (form.name || '').trim();
      if (!name) {
        if (!opts.silent) showToast('先填写项目名称', 'error');
        return null;
      }
      modal.coverBusy = true;
      try {
        const r = await fetch('/api/covers/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name,
            description: (form.description || '').trim(),
            project_type: form.project_type || currentProject.value?.project_type || '',
            scene: form.scene || currentProject.value?.scene || '',
            theme_color: form.cover_theme || '#2563EB',
          }),
        });
        const cover = await r.json();
        if (!r.ok || !cover?.id) throw new Error(cover.detail || cover.error || ('HTTP ' + r.status));
        covers.value = [cover, ...covers.value.filter(c => c.id !== cover.id)];
        form.cover_id = cover.id;
        if (!opts.silent) showToast('已生成项目封面');
        return cover;
      } catch (e) {
        if (!opts.silent) showToast('封面生成失败：' + e, 'error');
        return null;
      } finally {
        modal.coverBusy = false;
      }
    }

    async function uploadProjectCover(event, target = 'new') {
      const file = event.target.files?.[0];
      event.target.value = '';
      if (!file) return;
      const form = target === 'edit' ? projectEditModal : newProjectForm;
      const modal = target === 'edit' ? projectEditModal : newProjectModal;
      modal.coverBusy = true;
      try {
        const fd = new FormData();
        fd.append('file', file);
        const r = await fetch('/api/covers/upload', { method: 'POST', body: fd });
        const cover = await r.json();
        if (!r.ok || !cover?.id) throw new Error(cover.detail || cover.error || ('HTTP ' + r.status));
        covers.value = [cover, ...covers.value.filter(c => c.id !== cover.id)];
        form.cover_id = cover.id;
        showToast('已上传项目封面');
      } catch (e) {
        showToast('封面上传失败：' + e, 'error');
      } finally {
        modal.coverBusy = false;
      }
    }

    async function fetchProject(pid) {
      try {
        const r = await fetch('/api/projects/' + pid);
        if (!r.ok) throw new Error('HTTP ' + r.status);
        currentProject.value = await r.json();
      } catch (e) {
        showToast('加载项目失败：' + e, 'error');
        currentProject.value = null;
      }
    }

    function goList() {
      saveCurrentProjectAssistantMemory();
      view.value = 'list';
      fetchProjects();
    }

    async function goDetail(pid) {
      saveCurrentProjectAssistantMemory();
      view.value = 'detail';
      detailNav.value = 'overview';   // 重置到概览
      await fetchProject(pid);
      loadProjectAssistantMemory(pid);
      fetchKbDocs();   // 拉知识库（detail 页用 projectKbDocs 过滤）
    }

    function openEditorForProject() {
      // 进入海报渲染编辑器视图（编辑器内部状态保持不动）
      // 关联当前项目（保存按钮要用）
      if (currentProject.value) {
        editorContext.pid = currentProject.value.id;
        editorContext.source_artifact_id = null;
        restoreDraft({ resetIfMissing: true });
      }
      view.value = 'editor';
    }

    function openSkill(skill) {
      // 没配 key：直接弹设置
      if (!modelConfigured('llm')) {
        alert('请先配置大语言模型 API Key（点击右上角 ⚙️）。');
        openSettings();
        return;
      }
      // 阶段 C/D 实施前，先用占位提示
      const label = skill === 'design_brief' ? '设计阐释（阶段 C）'
        : skill === 'copywriter' ? '文案生成（阶段 D）'
        : skill;
      alert(`「${label}」功能正在做，下一阶段就上线。\n\n现在能用的：\n• 海报渲染卡 → 编辑器内的 AI 助手对话面板（使用当前 LLM 配置）\n• ⚙️ 设置抽屉 → 测试 LLM 连通`);
    }

    async function newProjectPrompt() {
      const name = prompt('项目名称（必填）：');
      if (!name || !name.trim()) return;
      const description = prompt('项目简介（可选）：') || '';
      try {
        const r = await fetch('/api/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: name.trim(), description: description.trim() }),
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const data = await r.json();
        await fetchProjects();
        showToast('已创建项目');
        // 直接进新项目详情
        currentProject.value = data;
        view.value = 'detail';
      } catch (e) {
        showToast('创建失败：' + e, 'error');
      }
    }

    async function confirmDeleteProject(p) {
      if (!confirm(`删除项目「${p.name}」？此操作不可撤销。`)) return;
      try {
        const r = await fetch('/api/projects/' + p.id, { method: 'DELETE' });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        showToast('已删除');
        await fetchProjects();
        if (currentProject.value?.id === p.id) goList();
      } catch (e) {
        showToast('删除失败：' + e, 'error');
      }
    }

    function openProjectEdit() {
      if (!currentProject.value) return;
      projectEditModal.name = currentProject.value.name || '';
      projectEditModal.description = currentProject.value.description || '';
      projectEditModal.status = currentProject.value.status || 'in_progress';
      projectEditModal.owner_name = currentProject.value.owner?.name || '';
      projectEditModal.cover_id = currentProject.value.cover_id || null;
      projectEditModal.cover_theme = currentProject.value.cover_tone || '#2563EB';
      projectEditModal.busy = false;
      projectEditModal.coverBusy = false;
      projectEditModal.show = true;
    }

    function cancelProjectEdit() {
      projectEditModal.show = false;
      projectEditModal.busy = false;
      projectEditModal.coverBusy = false;
    }

    async function submitProjectEdit() {
      if (!currentProject.value || !projectEditModal.name.trim()) return;
      projectEditModal.busy = true;
      try {
        const r = await fetch('/api/projects/' + currentProject.value.id, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: projectEditModal.name.trim(),
            description: projectEditModal.description.trim(),
            status: projectEditModal.status,
            owner: projectEditModal.owner_name.trim()
              ? { name: projectEditModal.owner_name.trim(), initial: projectEditModal.owner_name.trim()[0] }
              : undefined,
            cover_id: projectEditModal.cover_id,
          }),
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        await fetchProject(currentProject.value.id);
        await fetchProjects();
        projectEditModal.show = false;
        showToast('项目信息已更新');
      } catch (e) {
        showToast('编辑信息保存失败：' + e, 'error');
      } finally {
        projectEditModal.busy = false;
      }
    }

    function formatTs(s) {
      if (!s) return '-';
      // ISO → 月-日 时:分
      try {
        const d = new Date(s);
        const pad = n => String(n).padStart(2, '0');
        return `${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
      } catch (e) { return s; }
    }

    const SKILL_LABEL = {
      design_brief: '设计阐释',
      copywriter: '文案生成',
      poster_render: '海报渲染',
    };
    function skillLabel(s) { return SKILL_LABEL[s] || s; }

    // ========== 编辑器原有数据（以下保持不动） ==========
    const schemas = reactive({ canvas: [], sections: {}, section_types: [] });
    const templates = ref([]);
    const skillUploads = ref([]);
    const sessionId = ref('');
    const selectedTemplate = ref('');
    const rendering = ref(false);

    // 选中状态
    const selectedKind = ref('canvas');  // 'canvas' | 'section'
    const selectedIdx = ref(-1);

    // brief 数据
    const brief = reactive({
      scene: 'S3',
      logo_position: 'none',
      canvas: {
        width: 1440,
        bg_colors: ['#1A0A3D', '#0D0520'],
        palette_strategy: 'named:cyber_neon',
        pattern: 'none',
        glow: false,
      },
      decorations: { density: 'none' },
      background_decorations: null,
      sections: [],
    });

    // 底层装饰简化配置
    const bgDecoConfig = reactive({ count: 18, alpha: 0.55 });
    const bgDecoText = ref('');

    // 弹窗
    const modal = reactive({
      show: false, loading: false, title: '',
      pngUrl: '', pdfUrl: '', error: '', duration: 0,
    });

    // toast
    const toast = reactive({ text: '', kind: 'success' });
    function showToast(text, kind = 'success') {
      toast.text = text;
      toast.kind = kind;
      setTimeout(() => { toast.text = ''; }, 2500);
    }

    // 实时预览
    const preview = reactive({ url: '', error: '', duration: 0 });
    const previewStatus = ref('idle');  // idle | busy | live | error
    const autoPreview = ref(true);
    let previewDebounceTimer = null;
    let previewInflight = false;
    let previewQueued = false;
    const PREVIEW_DEBOUNCE_MS = 400;

    async function renderPreview() {
      if (view.value !== 'editor') return;
      flushAllTiptapEditorsToData();
      // 没 sections 不渲染
      if (!brief.sections || brief.sections.length === 0) {
        preview.url = '';
        preview.error = '';
        previewStatus.value = 'idle';
        return;
      }
      // 已有渲染中：标记下次再做
      if (previewInflight) {
        previewQueued = true;
        return;
      }
      previewInflight = true;
      previewStatus.value = 'busy';
      preview.error = '';

      const cleanBrief = sanitizeBrief(brief);

      try {
        const r = await fetch('/api/render', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ brief: cleanBrief, session_id: sessionId.value, preview: true }),
        });
        const j = await r.json();
        if (!r.ok || j.error) {
          preview.error = (j.error || ('HTTP ' + r.status)).slice(0, 800);
          previewStatus.value = 'error';
        } else {
          preview.url = j.png_url + '?t=' + Date.now();
          preview.duration = j.duration_sec;
          previewStatus.value = 'live';
        }
      } catch (e) {
        preview.error = String(e);
        previewStatus.value = 'error';
      } finally {
        previewInflight = false;
        if (previewQueued) {
          previewQueued = false;
          // 队列中有新请求 → 也走防抖再次安排，避免连击撑爆
          schedulePreview();
        }
      }
    }

    function schedulePreview() {
      if (view.value !== 'editor') return;
      if (!autoPreview.value) return;
      if (previewDebounceTimer) clearTimeout(previewDebounceTimer);
      previewDebounceTimer = setTimeout(() => {
        renderPreview();
      }, PREVIEW_DEBOUNCE_MS);
    }

    function onFormChange() {
      if (view.value !== 'editor') return;
      if (autoPreview.value) previewStatus.value = 'busy';
      schedulePreview();
    }

    // ========== AI 对话 ==========
    const chat = reactive({
      history: [],     // {role, content, actions}
      input: '',
      busy: false,
      modelReady: false,
      model: '',
      error: '',
      uploadedImages: [],
      uploadingImage: false,
      imageAssetType: 'module_content_image',
    });
    const chatMessagesEl = ref(null);

    function compactAssistantHistory(items, limit = 80) {
      return (items || []).slice(-limit).map(m => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: String(m.content || '').slice(0, 2000),
      })).filter(m => m.content);
    }

    function replaceAssistantHistory(target, items) {
      target.splice(0, target.length, ...compactAssistantHistory(items));
    }

    function projectAssistantMemoryKey(projectId) {
      return `ieg_project_assistant_memory_${projectId}`;
    }

    function ensureProjectAssistantMemory(projectId = currentProject.value?.id) {
      if (!projectId) return null;
      if (!projectAssistantMemory[projectId]) {
        let stored = null;
        try {
          stored = JSON.parse(localStorage.getItem(projectAssistantMemoryKey(projectId)) || 'null');
        } catch (e) {
          stored = null;
        }
        projectAssistantMemory[projectId] = {
          shared: compactAssistantHistory(stored?.shared || []),
          poster: compactAssistantHistory(stored?.poster || []),
          copywriter: compactAssistantHistory(stored?.copywriter || []),
        };
      }
      return projectAssistantMemory[projectId];
    }

    function persistProjectAssistantMemory(projectId, memory) {
      if (!projectId || !memory) return;
      try {
        localStorage.setItem(projectAssistantMemoryKey(projectId), JSON.stringify({
          shared: compactAssistantHistory(memory.shared || []),
          poster: compactAssistantHistory(memory.poster || []),
          copywriter: compactAssistantHistory(memory.copywriter || []),
        }));
      } catch (e) {}
    }

    function saveCurrentProjectAssistantMemory() {
      const projectId = currentProject.value?.id;
      if (!projectId) return;
      const memory = ensureProjectAssistantMemory(projectId);
      if (!memory) return;
      memory.poster = compactAssistantHistory(chat.history);
      memory.copywriter = compactAssistantHistory(copyChat.history);
      persistProjectAssistantMemory(projectId, memory);
    }

    function loadProjectAssistantMemory(projectId) {
      const memory = ensureProjectAssistantMemory(projectId);
      replaceAssistantHistory(chat.history, memory?.poster || []);
      replaceAssistantHistory(copyChat.history, memory?.copywriter || []);
    }

    function rememberProjectAssistantHandoff(targetNav, text) {
      const memory = ensureProjectAssistantMemory();
      if (!memory || !text) return;
      const label = skillLabelOf(targetNav);
      memory.shared.push({ role: 'user', content: `[首页助手转交到${label}] ${text}` });
      memory.shared = compactAssistantHistory(memory.shared);
      persistProjectAssistantMemory(currentProject.value?.id, memory);
    }

    function rememberProjectFeatureUserMessage(targetNav, text) {
      const memory = ensureProjectAssistantMemory();
      if (!memory || !text) return;
      memory.shared.push({ role: 'user', content: `[${skillLabelOf(targetNav)}] ${text}` });
      memory.shared = compactAssistantHistory(memory.shared);
      persistProjectAssistantMemory(currentProject.value?.id, memory);
    }

    function projectScopedAssistantHistory(localHistory) {
      const memory = ensureProjectAssistantMemory();
      return compactAssistantHistory([...(memory?.shared || []), ...(localHistory || [])], 50);
    }

    const posterPreviewZoom = ref(100);
    const posterPreviewGesture = reactive({
      dragging: false,
      startX: 0,
      startY: 0,
      scrollLeft: 0,
      scrollTop: 0,
      pinchStartDistance: 0,
      pinchStartZoom: 100,
      pinchStartContentX: 0,
      pinchStartContentY: 0,
    });
    const chatStatusClass = computed(() => {
      if (chat.busy) return 'busy';
      if (chat.error) return 'error';
      if (chat.modelReady) return 'ready';
      return '';
    });

    async function checkChatHealth() {
      try {
        const r = await fetch('/api/chat/health');
        const j = await r.json();
        chat.modelReady = !!j.model_ready;
        chat.model = j.current_model || '';
        if (j.provider === 'ollama') {
          if (!j.ollama_running) chat.error = 'Ollama 未运行';
          else if (!j.model_ready) chat.error = `模型 ${j.current_model} 未下载`;
          else chat.error = '';
        } else {
          // deepseek
          if (!j.key_set) chat.error = '未配置 API Key（点右上角 ⚙️）';
          else chat.error = '';
        }
      } catch (e) {
        chat.modelReady = false;
        chat.error = String(e);
      }
    }

    function scrollChatToBottom() {
      nextTick(() => {
        const el = chatMessagesEl.value;
        if (el) el.scrollTop = el.scrollHeight;
      });
    }

    function setPosterPreviewZoom(delta) {
      const next = Number(posterPreviewZoom.value || 100) + delta;
      posterPreviewZoom.value = Math.max(60, Math.min(220, next));
    }

    function setPosterPreviewZoomValue(value) {
      posterPreviewZoom.value = Math.max(60, Math.min(240, Math.round(value)));
    }

    function onPosterPreviewWheel(event) {
      if (!event) return;
      event.preventDefault?.();
      const el = event.currentTarget;
      // macOS 触控板：双指滑动是普通 wheel；捏合缩放通常带 ctrlKey。
      // 所以普通双指上下/左右滑动只滚动画布，不触发缩放。
      if (!event.ctrlKey) {
        if (el) {
          el.scrollLeft += event.deltaX || 0;
          el.scrollTop += event.deltaY || 0;
        }
        return;
      }
      const step = event.deltaY > 0 ? -10 : 10;
      setPosterPreviewZoom(step);
    }

    function onPosterPreviewPointerDown(event) {
      if (event.pointerType === 'touch') return;
      const el = event.currentTarget;
      if (!el) return;
      posterPreviewGesture.dragging = true;
      posterPreviewGesture.startX = event.clientX;
      posterPreviewGesture.startY = event.clientY;
      posterPreviewGesture.scrollLeft = el.scrollLeft;
      posterPreviewGesture.scrollTop = el.scrollTop;
      el.setPointerCapture?.(event.pointerId);
    }

    function onPosterPreviewPointerMove(event) {
      if (!posterPreviewGesture.dragging) return;
      const el = event.currentTarget;
      el.scrollLeft = posterPreviewGesture.scrollLeft - (event.clientX - posterPreviewGesture.startX);
      el.scrollTop = posterPreviewGesture.scrollTop - (event.clientY - posterPreviewGesture.startY);
    }

    function onPosterPreviewPointerEnd(event) {
      posterPreviewGesture.dragging = false;
      event.currentTarget?.releasePointerCapture?.(event.pointerId);
    }

    function touchDistance(touches) {
      if (!touches || touches.length < 2) return 0;
      const dx = touches[0].clientX - touches[1].clientX;
      const dy = touches[0].clientY - touches[1].clientY;
      return Math.sqrt(dx * dx + dy * dy);
    }

    function touchCenter(touches) {
      return {
        x: (touches[0].clientX + touches[1].clientX) / 2,
        y: (touches[0].clientY + touches[1].clientY) / 2,
      };
    }

    function onPosterPreviewTouchStart(event) {
      if (event.touches?.length === 2) {
        const el = event.currentTarget;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const center = touchCenter(event.touches);
        posterPreviewGesture.pinchStartDistance = touchDistance(event.touches);
        posterPreviewGesture.pinchStartZoom = posterPreviewZoom.value;
        posterPreviewGesture.pinchStartContentX = el.scrollLeft + center.x - rect.left;
        posterPreviewGesture.pinchStartContentY = el.scrollTop + center.y - rect.top;
        posterPreviewGesture.dragging = false;
      }
    }

    function onPosterPreviewTouchMove(event) {
      if (event.touches?.length !== 2 || !posterPreviewGesture.pinchStartDistance) return;
      event.preventDefault?.();
      const el = event.currentTarget;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const dist = touchDistance(event.touches);
      const pinchDelta = Math.abs(dist - posterPreviewGesture.pinchStartDistance);
      const nextZoom = pinchDelta > 12
        ? Math.max(60, Math.min(240, Math.round(posterPreviewGesture.pinchStartZoom * (dist / posterPreviewGesture.pinchStartDistance))))
        : posterPreviewGesture.pinchStartZoom;
      const ratio = nextZoom / Math.max(1, posterPreviewGesture.pinchStartZoom);
      const center = touchCenter(event.touches);
      const localX = center.x - rect.left;
      const localY = center.y - rect.top;
      posterPreviewZoom.value = nextZoom;
      nextTick(() => {
        el.scrollLeft = posterPreviewGesture.pinchStartContentX * ratio - localX;
        el.scrollTop = posterPreviewGesture.pinchStartContentY * ratio - localY;
      });
    }

    function onPosterPreviewTouchEnd(event) {
      if (!event.touches || event.touches.length < 2) {
        posterPreviewGesture.pinchStartDistance = 0;
      }
    }

    function findEditablePosterModule(text = '') {
      const modules = (posterStrategy.value?.module_plan || []).filter(m => !isTitleVisualModule(m) && !isLogoVisualModule(m));
      const nth = String(text).match(/第\s*(\d+)\s*个?模块/);
      if (nth) return modules[Math.max(0, Number(nth[1]) - 1)] || null;
      return modules.find(m => String(text).includes(m.module_config?.module_title || m.name || '')) || modules.find(m => m.ui_open) || modules[0] || null;
    }

    async function applyPosterAssistantCommand(text, images = []) {
      if (detailNav.value !== 'poster_brief' || !posterStrategy.value) return null;
      const raw = String(text || '').trim();
      const normalized = raw.replace(/\s+/g, '');
      const changes = [];
      const lowerImages = images.map(img => ({
        ...img,
        asset_type: img.asset_type || chat.imageAssetType || 'module_content_image',
        asset_type_label: img.asset_type_label || assetTypeLabel(img.asset_type || chat.imageAssetType),
      }));

      if (/logo|LOGO/.test(raw)) {
        if (/顶部|上方|最上面|top/i.test(raw)) {
          copyImport.logoPosition = 'top';
          changes.push('Logo 已改为顶部显示');
        } else if (/底部|下方|最下面|bottom/i.test(raw)) {
          copyImport.logoPosition = 'bottom';
          changes.push('Logo 已改为底部显示');
        } else if (/不显示|隐藏|去掉|删除/.test(raw)) {
          copyImport.logoPosition = 'none';
          changes.push('Logo 已设为不显示');
        }
        if (/左对齐|靠左/.test(raw)) copyImport.logoAlign = 'left';
        if (/右对齐|靠右/.test(raw)) copyImport.logoAlign = 'right';
        if (/居中|中间/.test(raw)) copyImport.logoAlign = 'center';
      }

      const subtitleMatch = raw.match(/(?:副标题|subtitle).*?(?:改成|设置为|写成|是|为)[：:，,\s]*(.+)$/i);
      if (subtitleMatch?.[1]) {
        copyImport.subtitleText = subtitleMatch[1].trim();
        changes.push('副标题文字已更新');
      }
      const globalMatch = raw.match(/(?:全局底图|全局背景|长图底图).*?(?:要求|改成|设置为|做成|为)[：:，,\s]*(.+)$/);
      if (globalMatch?.[1]) {
        copyImport.globalBgPrompt = globalMatch[1].trim();
        changes.push('全局底图要求已更新');
      }
      const heroMatch = raw.match(/(?:头部底图|头图|主视觉底图).*?(?:要求|改成|设置为|做成|为)[：:，,\s]*(.+)$/);
      if (heroMatch?.[1]) {
        copyImport.heroBgPrompt = heroMatch[1].trim();
        changes.push('头部底图要求已更新');
      }
      const wordartMatch = raw.match(/(?:主标题艺术字|标题艺术字|艺术字).*?(?:要求|改成|设置为|做成|为)[：:，,\s]*(.+)$/);
      if (wordartMatch?.[1]) {
        copyImport.wordartPrompt = wordartMatch[1].trim();
        changes.push('主标题艺术字要求已更新');
      }

      const titleMatch = raw.match(/(?:第\s*\d+\s*个?模块|[^，。,.]*模块)?(?:标题|模块标题).*?(?:改成|设置为|写成|为)[：:，,\s]*(.+)$/);
      const contentMatch = raw.match(/(?:正文|内容|文案).*?(?:改成|设置为|写成|为)[：:，,\s]*(.+)$/);
      if (titleMatch?.[1] || contentMatch?.[1]) {
        const m = findEditablePosterModule(raw);
        if (m) {
          m.module_config = m.module_config || {};
          if (titleMatch?.[1]) {
            m.module_config.module_title = titleMatch[1].trim();
            changes.push(`已更新「${m.name || '模块'}」标题`);
          }
          if (contentMatch?.[1]) {
            m.module_config.content = contentMatch[1].trim();
            changes.push(`已更新「${m.module_config.module_title || m.name || '模块'}」正文`);
          }
        }
      }

      if (lowerImages.length) {
        for (const img of lowerImages) {
          if (/logo|LOGO/.test(raw) || ['logo_color', 'logo_black', 'logo_white'].includes(img.asset_type)) {
            img.asset_type = img.asset_type?.startsWith('logo_') ? img.asset_type : 'logo_color';
            img.asset_type_label = assetTypeLabel(img.asset_type);
            registerAssistantVisualAsset(img);
            changes.push('上传图片已放入 Logo 视觉层');
          } else if (/全局|底图|背景/.test(raw)) {
            img.asset_type = 'global_bg';
            img.asset_type_label = assetTypeLabel('global_bg');
            registerAssistantVisualAsset(img);
            changes.push('上传图片已放入全局底图');
          } else if (/头部|头图|主视觉/.test(raw)) {
            img.asset_type = 'hero_bg';
            img.asset_type_label = assetTypeLabel('hero_bg');
            registerAssistantVisualAsset(img);
            changes.push('上传图片已放入头部底图');
          } else if (/艺术字|标题图层/.test(raw)) {
            img.asset_type = /副标题/.test(raw) ? 'subtitle_wordart' : 'main_wordart';
            img.asset_type_label = assetTypeLabel(img.asset_type);
            registerAssistantVisualAsset(img);
            changes.push('上传图片已放入标题艺术字图层');
          } else {
            const m = findEditablePosterModule(raw);
            if (m) {
              m.module_config = m.module_config || {};
              m.module_config.images = m.module_config.images || [];
              if (!m.module_config.images.some(a => a.path === img.path)) m.module_config.images.push(img);
              changes.push(`上传图片已放入「${m.module_config.module_title || m.name || '模块'}」`);
            }
          }
        }
      }

      if (!changes.length) return null;
      markPosterPreviewDirty();
      await saveProjectPosterStrategy({ silent: true });
      await generatePosterFromModules({ auto: false });
      return changes.join('；');
    }

    async function sendMessage() {
      const text = chat.input.trim();
      if ((!text && chat.uploadedImages.length === 0) || chat.busy) return;
      const imagesForRequest = chat.uploadedImages.slice();
      const imageHint = imagesForRequest.length
        ? '\n\n[用户已上传图片，可用于 image_block]\n' + imagesForRequest.map((img, i) => `${i + 1}. ${img.name}: ${img.path}`).join('\n')
        : '';
      const outboundText = text + imageHint;

      chat.input = '';
      chat.uploadedImages = [];
      chat.history.push({ role: 'user', content: text || '请把刚上传的图片放到海报合适位置', images: imagesForRequest });
      rememberProjectFeatureUserMessage('poster_brief', text || '请把刚上传的图片放到海报合适位置');
      scrollChatToBottom();

      chat.busy = true;
      try {
        const localReply = await applyPosterAssistantCommand(text, imagesForRequest);
        if (localReply) {
          chat.history.push({ role: 'assistant', content: localReply });
          return;
        }
        const cleanBrief = sanitizeBrief(brief);
        // 历史只发文本（不发 actions）
        const histPayload = projectScopedAssistantHistory(chat.history.slice(0, -1));
        const r = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            brief: cleanBrief,
            message: outboundText,
            history: histPayload,
          }),
        });
        const j = await r.json();
        if (!r.ok || j.error) {
          chat.history.push({
            role: 'assistant',
            content: '⚠️ ' + (j.error || ('HTTP ' + r.status)),
          });
        } else {
          // 应用 actions
          const result = applyActions(j.actions || []);
          // 组装回复
          let reply = result.replyText;
          if (!reply) {
            if (j.actions.length === 0) reply = '我没明白要做什么，能再说一下吗？';
            else reply = `已执行 ${j.actions.length} 个操作`;
          }
          chat.history.push({
            role: 'assistant',
            content: reply,
            actions: j.actions.filter(a => a.name !== 'answer'),
          });
        }
      } catch (e) {
        chat.history.push({
          role: 'assistant',
          content: '⚠️ ' + String(e),
        });
      } finally {
        chat.busy = false;
        scrollChatToBottom();
        saveCurrentProjectAssistantMemory();
      }
    }

    async function uploadChatImage(event) {
      const file = event.target.files?.[0];
      event.target.value = '';
      if (!file || chat.uploadingImage) return;
      chat.uploadingImage = true;
      try {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('session_id', sessionId.value || 'default');
        fd.append('asset_type', chat.imageAssetType || 'module_content_image');
        fd.append('asset_label', assetTypeLabel(chat.imageAssetType));
        const r = await fetch('/api/upload', { method: 'POST', body: fd });
        const j = await r.json();
        if (!r.ok || !j.path) throw new Error(j.error || ('HTTP ' + r.status));
        chat.uploadedImages.push({
          name: j.filename || file.name,
          path: j.path,
          url: j.url,
          asset_type: j.asset_type || chat.imageAssetType,
          asset_type_label: j.asset_type_label || assetTypeLabel(chat.imageAssetType),
        });
        showToast('图片已上传，可继续输入放置要求');
      } catch (e) {
        showToast('图片上传失败：' + e, 'error');
      } finally {
        chat.uploadingImage = false;
      }
    }

    function sendExample(text) {
      chat.input = text;
      sendMessage();
    }

    function clearChat() {
      chat.history.splice(0);
      saveCurrentProjectAssistantMemory();
    }

    // 把 LLM 返回的 actions 应用到 brief
    function applyActions(actions) {
      let replyText = '';
      for (const action of actions) {
        try {
          executeAction(action);
        } catch (e) {
          console.error('action 执行失败', action, e);
        }
        if (action.name === 'answer') {
          replyText = action.args?.text || replyText;
        }
      }
      return { replyText };
    }

    function executeAction(action) {
      const { name, args } = action;
      switch (name) {
        case 'set_palette': {
          if (!brief.canvas) brief.canvas = {};
          brief.canvas.palette_strategy = args.palette;
          // 同步底色 bg_colors（从 named: 推一些常用值）
          const PRESET_BG = {
            'named:cyber_neon': ['#1A0A3D', '#0D0520'],
            'named:deep_space': ['#1E1B4B', '#0B1020'],
            'named:aurora': ['#1F2456', '#0E0B36'],
            'named:carnival': ['#FFE6E1', '#FFD3CD'],
            'named:festival_red': ['#5C0A0A', '#2D0303'],
            'named:velvet_gold': ['#2A1810', '#0F0805'],
            'named:arena': ['#0F1729', '#06081A'],
            'named:engine_core': ['#0A1A12', '#020A06'],
            'named:charcoal_gold': ['#1F1F1F', '#0A0A0A'],
          };
          if (PRESET_BG[args.palette]) brief.canvas.bg_colors = PRESET_BG[args.palette];
          break;
        }
        case 'set_field': {
          const sec = brief.sections?.[args.section_index];
          if (sec) setDeep(sec, args.field_path, args.value);
          break;
        }
        case 'set_canvas_field': {
          if (!brief.canvas) brief.canvas = {};
          setDeep(brief.canvas, args.field_path, args.value);
          break;
        }
        case 'add_section': {
          if (!brief.sections) brief.sections = [];
          const meta = schemas.sections?.[args.section_type];
          const newSec = { type: args.section_type, _uid: uid() };
          // 用 schema 默认值填充
          (meta?.fields || []).forEach(f => {
            if (f.default !== undefined) {
              setDeep(newSec, f.key, JSON.parse(JSON.stringify(f.default)));
            }
          });
          // 用 LLM 给的 initial_fields 覆盖
          if (args.initial_fields && typeof args.initial_fields === 'object') {
            for (const k of Object.keys(args.initial_fields)) {
              setDeep(newSec, k, args.initial_fields[k]);
            }
          }
          const pos = (typeof args.position === 'number')
            ? Math.max(0, Math.min(args.position, brief.sections.length))
            : brief.sections.length;
          brief.sections.splice(pos, 0, newSec);
          break;
        }
        case 'delete_section': {
          if (brief.sections && args.section_index >= 0 && args.section_index < brief.sections.length) {
            brief.sections.splice(args.section_index, 1);
          }
          break;
        }
        case 'move_section': {
          const arr = brief.sections;
          if (!arr) break;
          const fi = args.from_index, ti = args.to_index;
          if (fi >= 0 && fi < arr.length && ti >= 0 && ti < arr.length) {
            const item = arr.splice(fi, 1)[0];
            arr.splice(ti, 0, item);
          }
          break;
        }
        case 'duplicate_section': {
          if (brief.sections && args.section_index >= 0 && args.section_index < brief.sections.length) {
            const copy = JSON.parse(JSON.stringify(brief.sections[args.section_index]));
            copy._uid = uid();
            brief.sections.splice(args.section_index + 1, 0, copy);
          }
          break;
        }
        case 'set_notice_highlight': {
          const sec = brief.sections?.[args.section_index];
          if (!sec || sec.type !== 'notice_box') break;
          const bullets = sec.bullets || [];
          if (args.bullet_index < 0 || args.bullet_index >= bullets.length) break;
          const cur = bullets[args.bullet_index];
          const text = typeof cur === 'string' ? cur : (cur.text || '');
          if (args.highlight) {
            bullets[args.bullet_index] = {
              text,
              highlight: true,
              highlight_color: args.color || '#FF4444',
            };
          } else {
            bullets[args.bullet_index] = text;
          }
          break;
        }
        case 'load_template': {
          // 异步加载模板（不等）
          fetch('/api/template/' + args.template_name)
            .then(r => r.json())
            .then(j => {
              if (j.brief) {
                Object.keys(brief).forEach(k => delete brief[k]);
                Object.assign(brief, j.brief);
                (brief.sections || []).forEach(s => { s._uid = uid(); });
                syncBgDecoFromBrief();
              }
            });
          break;
        }
        case 'answer':
          // 不修改 brief
          break;
      }
    }

    function formatAction(a) {
      const { name, args } = a;
      switch (name) {
        case 'set_palette':
          return `切换配色 → ${args.palette}`;
        case 'set_field':
          return `改 #${args.section_index} 的 ${args.field_path} = ${JSON.stringify(args.value)}`;
        case 'set_canvas_field':
          return `改画布 ${args.field_path} = ${JSON.stringify(args.value)}`;
        case 'add_section':
          return `添加 ${args.section_type} ${args.position != null ? '到位置 ' + args.position : '到末尾'}`;
        case 'delete_section':
          return `删除 #${args.section_index}`;
        case 'move_section':
          return `移动 #${args.from_index} → #${args.to_index}`;
        case 'duplicate_section':
          return `复制 #${args.section_index}`;
        case 'set_notice_highlight':
          return `${args.highlight ? '标红' : '取消标红'} #${args.section_index} 第 ${args.bullet_index + 1} 条`;
        case 'load_template':
          return `载入模板 ${args.template_name}`;
        default:
          return name;
      }
    }

    // ========== 初始化 ==========
    onMounted(async () => {
      // v0.2 新增：先加载项目列表 + 配置 + 封面清单 + skill 注册表
      fetchProjects();
      fetchConfig();
      fetchCovers();
      fetchSkillsRegistry();
      fetchPosterStrategies();

      // 拉 schemas
      const r1 = await fetch('/api/schemas');
      const s = await r1.json();
      Object.assign(schemas, s);

      // 拉模板列表
      const r2 = await fetch('/api/templates');
      const j2 = await r2.json();
      templates.value = j2.templates;

      // 拉素材库
      const r3 = await fetch('/api/skill-uploads');
      const j3 = await r3.json();
      skillUploads.value = j3.scenes;

      // 创建 session
      const r4 = await fetch('/api/new-session', { method: 'POST' });
      const j4 = await r4.json();
      sessionId.value = j4.session_id;

      // 检查 LLM 是否就位
      checkChatHealth();
      // 每 30s 复查一次（用户可能后台启动 ollama）
      setInterval(checkChatHealth, 30000);

      // 正式模式：刷新/退出不恢复本地草稿，避免未保存内容串项目。
      try {
        localStorage.removeItem(draftStorageKey());
        localStorage.removeItem('poster-web-draft');
        localStorage.removeItem('poster-web-draft:global');
        sessionStorage.removeItem('apply_brief');
        sessionStorage.removeItem('apply_copy');
      } catch (e) {}
      resetEditorBrief();
      window.addEventListener('beforeunload', () => {
        try {
          localStorage.removeItem(draftStorageKey());
          localStorage.removeItem('poster-web-draft');
          localStorage.removeItem('poster-web-draft:global');
          sessionStorage.removeItem('apply_brief');
          sessionStorage.removeItem('apply_copy');
        } catch (e) {}
      });

      // 初始化 sortable
      await nextTick();
      initSortable();

      // 检查 sessionStorage 是否有要应用的 brief（从海报生成跳来）
      checkApplyBrief();

      // 点击页面其他地方关闭打开的菜单
      document.addEventListener('click', () => {
        menuOpenFor.value = null;
        detailStatusMenuOpen.value = false;
      });
      document.addEventListener('mousedown', handleRichGlobalMouseDown);
      document.addEventListener('focusin', handleRichEditorFocus);
      document.addEventListener('mouseup', handleRichEditorSelectionChange);
      document.addEventListener('keyup', handleRichEditorSelectionChange);
      window.addEventListener('scroll', handleRichViewportChange, true);
      window.addEventListener('resize', handleRichViewportChange);
    });

    // 当 view 切换到 editor 时也检查一次（初始 view 不是 editor 的情况）
    watch(view, (v) => {
      if (v === 'editor') {
        nextTick(() => checkApplyBrief());
      }
    });

    function checkApplyBrief() {
      try {
        const raw = sessionStorage.getItem('apply_brief');
        if (!raw) return;
        const data = JSON.parse(raw);
        if (!data || !data.brief) return;

        if (data.pid && editorContext.pid !== data.pid) {
          editorContext.pid = data.pid;
          editorContext.source_artifact_id = null;
          restoreDraft({ resetIfMissing: true });
        }

        const hasDraft = brief.sections && brief.sections.length > 0;
        let action = 'replace';
        if (hasDraft) {
          const choice = confirm(
            `检测到从海报生成跳来的 brief（来自 artifact ${data.artifact_id?.slice(0,12) || '?'}）。\n\n` +
            `[确定] 替换当前编辑器内容\n[取消] 保留当前内容（忽略导入）`
          );
          if (!choice) {
            sessionStorage.removeItem('apply_brief');
            return;
          }
        }

        // 替换：清空再 assign
        Object.keys(brief).forEach(k => delete brief[k]);
        Object.assign(brief, data.brief);
        // 给每个 section 加 _uid（编辑器需要）
        (brief.sections || []).forEach(s => { if (!s._uid) s._uid = uid(); });
        // 同步底层装饰简化配置
        if (typeof syncBgDecoFromBrief === 'function') syncBgDecoFromBrief();
        refreshMountedTiptapEditorsFromData();

        // 记录关联的项目（保存按钮用）
        editorContext.pid = data.pid;
        editorContext.source_artifact_id = data.artifact_id;
        selectCanvas();
        saveDraft();

        // 用完即焚
        sessionStorage.removeItem('apply_brief');
        showToast('已载入 brief，可在编辑器继续修改');

        if (autoPreview.value) renderPreview();
      } catch (e) {
        console.warn('apply_brief 处理失败:', e);
      }
    }

    // 编辑器关联项目上下文（从 detail 跳来时用）
    const editorContext = reactive({ pid: null, source_artifact_id: null });
    const savingToProject = ref(false);

    async function saveBriefToProject() {
      if (!editorContext.pid) {
        showToast('当前编辑器未关联项目，请从项目详情页进入', 'error');
        return;
      }
      if (savingToProject.value) return;
      savingToProject.value = true;
      try {
        const cleanBrief = sanitizeBrief(brief);
        const r = await fetch(`/api/projects/${editorContext.pid}/save-as-artifact`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ brief: cleanBrief }),
        });
        const j = await r.json();
        if (!r.ok || j.error) {
          showToast(j.error || ('HTTP ' + r.status), 'error');
          return;
        }
        showToast(`已保存为新版本（耗时 ${j.artifact?.duration_sec || '?'}s）`);
      } catch (e) {
        showToast('保存失败：' + e, 'error');
      } finally {
        savingToProject.value = false;
      }
    }

    // ========== Sortable ==========
    const sortableEl = ref(null);
    function initSortable() {
      const el = sortableEl.value;
      if (!el) return;
      Sortable.create(el, {
        animation: 200,
        handle: '.handle',
        ghostClass: 'sortable-ghost',
        chosenClass: 'sortable-chosen',
        onEnd(evt) {
          const oldIdx = evt.oldIndex;
          const newIdx = evt.newIndex;
          if (oldIdx === newIdx) return;

          // 关键修复：SortableJS 已经移动了 DOM 节点，
          // 此时如果直接改 Vue 数据，Vue 会基于"错乱的 DOM"做 diff → 顺序不一致
          // 必须先把 DOM 还原成 Vue 期望的旧顺序，再改数据
          const parent = evt.from;
          const movedNode = parent.children[newIdx];
          const refNode = parent.children[oldIdx > newIdx ? oldIdx + 1 : oldIdx];
          parent.insertBefore(movedNode, refNode || null);

          // DOM 还原后，下一帧才修改数据，让 Vue 走正常的 diff 流程
          nextTick(() => {
            const arr = brief.sections;
            const item = arr.splice(oldIdx, 1)[0];
            arr.splice(newIdx, 0, item);
            // 修正选中索引
            if (selectedKind.value === 'section') {
              if (selectedIdx.value === oldIdx) selectedIdx.value = newIdx;
              else if (oldIdx < selectedIdx.value && newIdx >= selectedIdx.value) selectedIdx.value -= 1;
              else if (oldIdx > selectedIdx.value && newIdx <= selectedIdx.value) selectedIdx.value += 1;
            }
          });
        },
      });
    }

    // ========== Sections 操作 ==========
    function addSection(type) {
      const meta = schemas.sections[type];
      const newSec = { type, _uid: uid() };
      // 用默认值填充
      (meta?.fields || []).forEach(f => {
        if (f.default !== undefined) {
          setDeep(newSec, f.key, JSON.parse(JSON.stringify(f.default)));
        }
      });
      brief.sections.push(newSec);
      selectSection(brief.sections.length - 1);
    }
    function delSection(idx) {
      brief.sections.splice(idx, 1);
      if (selectedIdx.value === idx) {
        selectedKind.value = 'canvas';
        selectedIdx.value = -1;
      } else if (selectedIdx.value > idx) {
        selectedIdx.value -= 1;
      }
    }
    function dupSection(idx) {
      const copy = JSON.parse(JSON.stringify(brief.sections[idx]));
      copy._uid = uid();
      brief.sections.splice(idx + 1, 0, copy);
    }
    function moveUp(idx) {
      if (idx <= 0) return;
      const arr = brief.sections;
      [arr[idx - 1], arr[idx]] = [arr[idx], arr[idx - 1]];
      if (selectedKind.value === 'section') {
        if (selectedIdx.value === idx) selectedIdx.value = idx - 1;
        else if (selectedIdx.value === idx - 1) selectedIdx.value = idx;
      }
    }
    function moveDown(idx) {
      const arr = brief.sections;
      if (idx >= arr.length - 1) return;
      [arr[idx + 1], arr[idx]] = [arr[idx], arr[idx + 1]];
      if (selectedKind.value === 'section') {
        if (selectedIdx.value === idx) selectedIdx.value = idx + 1;
        else if (selectedIdx.value === idx + 1) selectedIdx.value = idx;
      }
    }
    // 中文兜底名（schemas 加载前或类型未知时）
    const SECTION_TYPE_CN = {
      top_logo_bar: '顶部 Logo 横幅',
      hero_strip: '主标题艺术字',
      subtitle_text: '副标题',
      section_title_bar: '模块标题',
      lead_paragraph: '段落正文',
      image_block: '图片块',
      data_table: '数据表格',
      faculty_grid: '讲师团 / 顾问团',
      notice_box: '注意事项 / 学员须知',
      contact_inline: '联系方式',
      info_card: '信息卡（带 Logo）',
      cta_button: 'CTA 大按钮',
      complex_table: '复杂表格',
      table_module: '表格模块',
      info_card_with_qr: '信息卡 + 二维码',
      qa_block: '问答块',
      meta_row: '元信息行',
      schedule_table: '日程表',
      resource_grid: '资源网格',
      rules_box: '规则框',
      contact_card: '联系卡',
      footer_logobar: '底部 Logo 横幅',
      curriculum_timeline: '课程时间线',
      benefit_grid: '收益网格',
      bullet_points_block: '要点块',
    };
    function sectionTypeName(t) {
      return SECTION_TYPE_CN[t] || t;
    }
    function selectCanvas() {
      selectedKind.value = 'canvas';
      selectedIdx.value = -1;
    }
    function selectSection(idx) {
      selectedKind.value = 'section';
      selectedIdx.value = idx;
    }
    const currentSection = computed(() =>
      selectedKind.value === 'section' && selectedIdx.value >= 0
        ? brief.sections[selectedIdx.value] : null
    );

    function sectionPreview(s) {
      // 取最显眼的字段做摘要
      const t = s.text || s.heading || s.body || s.title_card?.image || s.image_path
              || s.headers?.join(', ') || '';
      return String(t).slice(0, 60);
    }

    // ========== 模板载入 ==========
    async function loadTemplate() {
      if (!selectedTemplate.value) return;
      const r = await fetch('/api/template/' + selectedTemplate.value);
      const j = await r.json();
      if (!j.brief) { showToast('载入失败', 'error'); return; }
      // 替换 brief
      Object.keys(brief).forEach(k => delete brief[k]);
      Object.assign(brief, j.brief);
      // 给每个 section 加 _uid
      (brief.sections || []).forEach(s => { s._uid = uid(); });
      // 同步底层装饰简化配置
      syncBgDecoFromBrief();
      refreshMountedTiptapEditorsFromData();
      selectCanvas();
      saveDraft();
      showToast('已载入模板：' + selectedTemplate.value);
      // 模板载入后立刻渲染一次预览
      if (autoPreview.value) renderPreview();
    }

    function resetBrief() {
      if (!confirm('丢弃当前项目的编辑器内容，重新开始？')) return;
      resetEditorBrief();
      saveDraft();
    }

    function clearAll() {
      if (!confirm('清空所有 sections？')) return;
      brief.sections.splice(0);
      selectCanvas();
    }

    function hardReset() {
      if (!confirm('清除当前项目的浏览器草稿、所有未保存内容会丢失？')) return;
      try {
        localStorage.removeItem(draftStorageKey());
        if (!editorContext.pid) {
          localStorage.removeItem('poster-web-draft');
          localStorage.removeItem('poster-web-draft:global');
        }
      } catch (e) {}
      resetEditorBrief();
      showToast('已清除当前项目编辑器草稿');
    }

    // ========== 渲染 ==========
    async function render() {
      if (rendering.value) return;
      rendering.value = true;
      modal.show = true;
      modal.loading = true;
      modal.title = '渲染海报';
      modal.error = '';
      modal.pngUrl = '';
      modal.pdfUrl = '';

      // 清洗 brief
      const cleanBrief = sanitizeBrief(brief);

      try {
        const r = await fetch('/api/render', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ brief: cleanBrief, session_id: sessionId.value }),
        });
        const j = await r.json();
        if (!r.ok || j.error) {
          modal.error = j.error + (j.traceback ? '\n\n' + j.traceback : '');
        } else {
          modal.pngUrl = j.png_url;
          modal.pdfUrl = j.pdf_url;
          modal.duration = j.duration_sec;
        }
      } catch (e) {
        modal.error = String(e);
      } finally {
        rendering.value = false;
        modal.loading = false;
      }
    }

    // ========== 底层装饰 ==========
    function toggleBgDeco(on) {
      if (on) {
        brief.background_decorations = {
          seed: 42,
          exclude_top: 1500,
          exclude_bottom: 200,
          types: [],
        };
      } else {
        brief.background_decorations = null;
      }
    }
    function syncBgDecoFromBrief() {
      const bd = brief.background_decorations;
      if (!bd) {
        bgDecoText.value = '';
        return;
      }
      bgDecoText.value = (bd.types || []).map(t => t.path).join('\n');
      if (bd.types?.[0]) {
        bgDecoConfig.count = bd.types[0].count || 18;
        bgDecoConfig.alpha = bd.types[0].alpha != null ? bd.types[0].alpha : 0.55;
      }
    }
    function onBgDecoTextInput(text) {
      bgDecoText.value = text;
      syncBgDeco();
    }
    function syncBgDeco() {
      const bd = brief.background_decorations;
      if (!bd) return;
      const paths = bgDecoText.value.split('\n').map(s => s.trim()).filter(Boolean);
      bd.types = paths.map(p => ({
        path: p,
        size: [60, 120],
        count: bgDecoConfig.count,
        alpha: bgDecoConfig.alpha,
        rotate: true,
        blur: 0,
      }));
    }

    // ========== localStorage 草稿 ==========
    let saveDraftTimer = null;
    watch(brief, () => {
      // saveDraft 也走防抖（避免 deep watch 触发多次同步序列化）
      if (saveDraftTimer) clearTimeout(saveDraftTimer);
      saveDraftTimer = setTimeout(saveDraft, 500);
      schedulePreview();
    }, { deep: true });
    function draftStorageKey(pid = editorContext.pid) {
      return pid ? `poster-web-draft:${pid}` : 'poster-web-draft:global';
    }

    function resetEditorBrief() {
      Object.keys(brief).forEach(k => delete brief[k]);
      Object.assign(brief, {
        scene: 'S3',
        logo_position: 'none',
        canvas: {
          width: 1440,
          bg_colors: ['#1A0A3D', '#0D0520'],
          palette_strategy: 'named:cyber_neon',
          pattern: 'none',
          glow: false,
        },
        decorations: { density: 'none' },
        background_decorations: null,
        sections: [],
      });
      selectCanvas();
      syncBgDecoFromBrief();
    }

    function saveDraft() {
      // 正式模式不保存本地草稿；只有显式“保存当前编辑”才写入项目。
    }
    function restoreDraft(opts = {}) {
      try {
        let raw = localStorage.getItem(draftStorageKey());
        // 兼容旧版全局草稿：只有未关联项目时才读取，避免项目间串稿
        if (!raw && !editorContext.pid) raw = localStorage.getItem('poster-web-draft');
        if (!raw) {
          if (opts.resetIfMissing) resetEditorBrief();
          return;
        }
        let obj = JSON.parse(raw);
        // 关键：先 sanitize 修复脏数据（如 bg_colors 是字符串），再赋值
        // 否则一启动就触发 watch → 预览失败 → 状态卡住
        obj = sanitizeBrief(obj);
        // 加上必需字段兜底
        if (!obj.sections) obj.sections = [];
        if (!obj.canvas) obj.canvas = { width: 1440 };
        if (!obj.canvas.bg_colors) obj.canvas.bg_colors = ["#1A0A3D", "#0D0520"];
        Object.keys(brief).forEach(k => delete brief[k]);
        Object.assign(brief, obj);
        (brief.sections || []).forEach(s => { if (!s._uid) s._uid = uid(); });
        syncBgDecoFromBrief();
        refreshMountedTiptapEditorsFromData();
      } catch (e) {
        // 草稿坏了就直接清空
        console.warn('草稿恢复失败，清空:', e);
        localStorage.removeItem(draftStorageKey());
        if (opts.resetIfMissing) resetEditorBrief();
      }
    }

    function onUpload(payload) {
      // 暂未实现"素材库"选择面板，这里先不处理
      showToast('素材库选择功能稍后开放，先用上传按钮', 'success');
    }

    function handleRichGlobalMouseDown(event) {
      if (event.target?.closest?.('.floating-rich-toolbar')) return;
      if (event.target?.closest?.('.rich-editor.tiptap-host, .ProseMirror')) return;
      hideFloatingRichToolbar();
    }

    function richSlotOfEditor(editor) {
      if (!editor) return 'body';
      if (editor.dataset?.richSlot) return editor.dataset.richSlot;
      if (editor.classList?.contains('title')) return 'title';
      return 'body';
    }

    function handleRichEditorFocus(event) {
      const editor = event.target?.closest?.('.rich-editor.tiptap-host');
      if (!editor) return;
      activateRichEditor({ currentTarget: editor, target: editor }, null, '', richSlotOfEditor(editor));
    }

    function handleRichEditorSelectionChange(event) {
      const editor = event.target?.closest?.('.rich-editor.tiptap-host');
      if (!editor) return;
      if (floatingRich.editor !== editor) {
        activateRichEditor({ currentTarget: editor, target: editor }, null, '', richSlotOfEditor(editor));
      } else {
        saveRichSelection({ currentTarget: editor, target: editor });
      }
    }

    function handleRichViewportChange() {
      if (floatingRich.visible) positionFloatingRichToolbar();
    }

    return {
      // 常量
      STATUS_LABEL, TABS, NAV_META, KB_ACCEPT,
      // v0.2 新增：视图状态机 + 项目数据
      view, projects, projectStats, currentProject,
      goList, goDetail, openEditorForProject, openSkill,
      newProjectPrompt, confirmDeleteProject,
      formatTs, skillLabel, skillIcon, skillIconClass,
      // F1-F5 新增：sidebar / 过滤 / 菜单 / 模态
      navTab, setNavTab,
      searchQuery, filterTab, tabCount, homeAssistant, sendHomeAssistant,
      handleHomeAssistantAttachment, removeHomeAssistantAttachment, toggleHomeVoiceInput,
      activeProjects, archivedProjects,
      menuOpenFor, toggleMenu,
      detailStatusMenuOpen, toggleDetailStatusMenu,
      changeStatus,
      // v0.4 详情页二级 nav
      detailNav, setDetailNav, runningJob, cancelRunningJob, artifactHistoryOpen,
      skillLabelOf, skillSubOf, skillIconOf,
      platformKbDocs, projectKbDocs, posterCopyKbDocs, posterImageKbDocs,
      // v0.4 skill 调用
      skillsRegistry, skillForm, skillRunning, skillStream,
      copyImport, handleCopyImportFileSelect, runCopyImportUpload,
      posterStrategies, posterStrategySelection, posterStrategy,
      posterFunctionProjects, selectedPosterFunctionProjectIds,
      posterFunctionNameEditing, startPosterFunctionNameEdit,
      finishPosterFunctionNameEdit, cancelPosterFunctionNameEdit,
      currentPosterFunctionProject, posterFunctionProjectsLoading,
      posterFunctionCreate, fetchPosterFunctionProjects, loadPosterFunctionProject, requestLoadPosterFunctionProject,
      openPosterFunctionCreate, cancelPosterFunctionCreate, selectPosterFunctionCreateType,
      selectPosterFunctionCreateScene, posterFunctionCreateTypeMeta, posterFunctionCreateSceneMeta,
      allowedPosterFunctionCreateScenes, resolvePosterFunctionCreateStrategy,
      createBlankPosterFunctionProject, deletePosterFunctionProject,
      isPosterFunctionProjectSelected, togglePosterFunctionProjectSelection,
      selectAllPosterFunctionProjects, clearPosterFunctionProjectSelection,
      deleteSelectedPosterFunctionProjects,
      selectProjectTypeForPoster, allowedPosterScenes, resolvePosterStrategy,
      selectCurrentPosterType, allowedCurrentPosterScenes, resolveCurrentPosterStrategy,
      handleCurrentPosterTypeChange, handleCurrentPosterSceneChange,
      selectProjectTypeForNewProject, allowedNewProjectScenes, resolveNewProjectStrategy,
      currentPosterStrategyPayload, moduleStatusLabel, moduleStatusClass,
      moduleDisplayName, moduleMetaText, moduleComponentLabel, specialModuleKind,
      moduleTitleLabel, moduleTypeCodeLabel,
      startModuleTitleEdit, finishModuleTitleEdit, cancelModuleTitleEdit,
      markPosterPreviewDirty,
      colorOptionStyle, colorOptionLabel, toggleModuleColorPicker, setModuleColor,
      textEditorStyle, subTitleEditorStyle, syncEditableText, richHtml, setRichToggle, richCommand,
      floatingRich, floatingRichStyle, activateRichEditor, saveRichSelection,
      applyFloatingRichCommand, uploadInlineRichImage, pickInlineRichImage, hideFloatingRichToolbar, selectRichImage, handleRichEditorKeydown,
      setRichFontFamily, setRichFontSize, setRichAlign,
      moduleAutofill, handleModuleAutofillFiles, handleCopyAssistantFiles, removeModuleAutofillFile, runModuleAutofill,
      runModuleCopyGenerate, clearModuleCopyDraft, applyModuleCopyDraft, goPosterBriefAfterCopy, moduleCopyDraftLabel,
      syncCopyDraftReadableFromModules,
      copyChat, copyChatMessagesEl, sendCopyChatMessage, clearCopyChat,
      copyDraftNeedsImage, copyDraftImagePlaceholder, addCopyDraftTableRow, addCopyDraftTableCol,
      removeCopyDraftTableRow, addCopyDraftSubsection, addCopyDraftAction,
      exportModuleCopyDraftMd, exportModuleCopyDraftWord,
      moduleAddKey, MODULE_UNDERLINE_COLORS, MODULE_PANEL_COLORS, MODULE_BORDER_COLORS, moduleImageUploading,
      MODULE_TEXT_COLORS, MODULE_FONT_OPTIONS,
      allModuleOptions, addStrategyModule, removeStrategyModule, moveStrategyModule,
      moduleTitleRequired, isTitleVisualModule, isLogoVisualModule, moduleImageKey, uploadStrategyModuleImages, removeStrategyModuleImage,
      uploadModuleImageForTarget,
      structuredModuleRenderer, isStructuredModule, moduleImageOptions,
      addAvatarGroup, removeAvatarGroup, addAvatarPerson, removeAvatarPerson,
      addSpeakerSection, removeSpeakerSection,
      addCourseItem, removeCourseItem, addAction, removeAction,
      addRatingItem, removeRatingItem, addQuoteItem, removeQuoteItem,
      addTextSubsection, removeTextSubsection, addTextListItem, removeTextListItem,
      addFeedbackSubmodule, removeFeedbackSubmodule, setImageFromOption,
      addQaItem, removeQaItem, addTimelinePart, removeTimelinePart,
      addTableRow, removeTableRow, addTableColumn, removeTableColumn,
      titleLayerLabel, uploadTitleVisualLayer, removeTitleVisualLayer,
      generatePosterFromModules,
      assetTypeOptions, assetTypeLabel, uploadCopyVisualAssets, removeCopyVisualAsset,
      runSkill, applyCopyToEditor, applyBriefToEditor, viewArtifact,
      getSkillArtifacts, posterBriefPreviewUrl, posterLightbox, posterExportUrl,
      openPosterLightbox, closePosterLightbox, openPosterFull,
      // v0.4 编辑器项目上下文 + 保存按钮
      editorContext, savingToProject, saveBriefToProject,
      ownerColorClass, relativeTime,
      covers, newProjectModal, newProjectForm,
      openNewProject, submitNewProject, cancelNewProject,
      projectEditModal, openProjectEdit, cancelProjectEdit, submitProjectEdit,
      generateProjectCover, uploadProjectCover,
      handleNpUpload, handleNpDrop, removeNpDoc, aiExtractFromDocs,
      recognizeCurrentProjectKb, saveProjectPosterStrategy, saveCurrentPosterEdit,
      projectDetailBannerStyle,
      // v0.3 知识库
      kb, fetchKbDocs, handleKbUpload, handlePosterProjectKbUpload, deleteKbDoc, kbIcon, formatBytes,
      alert,
      // v0.2 新增：设置抽屉
      settingsOpen, config, settingsDraft, settingsTest, settingsSaving,
      openSettings, closeSettings, testSettings, testImageSettings, saveSettings,
      presetList, applyModelPreset, modelConfigured, modelStatusText, allModelStatusText,
      // 编辑器原有
      schemas, templates, skillUploads, sessionId,
      selectedTemplate, rendering,
      brief, selectedKind, selectedIdx, currentSection,
      sortableEl,
      bgDecoConfig, bgDecoText,
      modal, toast, choiceDialog, resolveChoiceDialog,
      preview, previewStatus, autoPreview, renderPreview,
      chat, chatMessagesEl, chatStatusClass, posterPreviewZoom, setPosterPreviewZoom,
      onPosterPreviewWheel, onPosterPreviewPointerDown, onPosterPreviewPointerMove,
      onPosterPreviewPointerEnd, onPosterPreviewTouchStart, onPosterPreviewTouchMove,
      onPosterPreviewTouchEnd,
      uploadChatImage,
      sendMessage, sendExample, clearChat, formatAction,
      addSection, delSection, dupSection, moveUp, moveDown,
      selectCanvas, selectSection, sectionPreview, sectionTypeName,
      loadTemplate, resetBrief, clearAll, hardReset, render,
      toggleBgDeco, onBgDecoTextInput, syncBgDeco,
      onUpload, onFormChange,
    };
  },
});

app.directive('rich-editor-init', {
  mounted(el, binding) {
    // FIX: 问题1/3/4 - TipTap 区域挂载即初始化，保证编辑器 DOM、Vue 数据和保存 payload 使用同一个 editor_json 来源。
    Promise.resolve().then(() => window.__IEG_ENSURE_RICH_EDITOR__?.(el, binding.value));
  },
  updated(el, binding) {
    Promise.resolve().then(() => window.__IEG_ENSURE_RICH_EDITOR__?.(el, binding.value));
  },
  beforeUnmount(el) {
    const editor = el.__tiptapEditor;
    if (editor && !editor.isDestroyed) {
      try { window.__IEG_FLUSH_RICH_EDITORS__?.(); } catch (e) {}
    }
  },
});

app.directive('rich-html', {
  mounted(el, binding) {
    // FIX: 问题1/2/4 - TipTap 宿主不再接受 v-rich-html 写 DOM，避免旧 HTML 与 editor_json 双源覆盖。
    if (el.classList?.contains('tiptap-host')) return;
    el.__richHtmlValue = binding.value || '';
    if (!el.__tiptapEditor && !el.innerHTML) el.innerHTML = el.__richHtmlValue;
  },
  updated(el, binding) {
    if (el.classList?.contains('tiptap-host')) return;
    const next = binding.value || '';
    if (el.__tiptapEditor || el.classList?.contains('tiptap-ready')) return;
    if (document.activeElement === el) return;
    if (next !== el.__richHtmlValue && el.innerHTML !== next) {
      el.innerHTML = next;
    }
    el.__richHtmlValue = next;
  },
});

app.mount('#app');
