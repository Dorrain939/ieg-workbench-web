"""
美学配色库 (palette_lab) —— 解决"配色不自然"这一硬伤。

为什么需要这个文件？
====================
v0.4 的 SCENE_PALETTE 只是按场景给了 4 个 hex，色与色之间的关系靠拍脑袋。
v0.5 引入"配色方案 (Scheme)"概念：每个方案都是一个有名字、有色彩学根据、
有真实灵感来源的成熟组合。同一场景下挂多个方案，runtime 按 brief 选/混。

色彩学骨架（按 HSL 关系建构）
==============================
- Mono           —— 同一 hue，明度/饱和度变化 → 安静、商务
- Analogous      —— H 相邻 ±30° → 柔和、自然过渡
- Complementary  —— H 对角 180° → 强对比、聚焦
- Split-Comp     —— H + 对角左右各 30° → 强烈但不冲突
- Triad          —— H 等分 120° → 活泼、平衡
- Tetrad         —— H 等分 90° (双互补) → 信息量最大、最难调

每个 Scheme 自带：
- name / theory       配色理论标签
- inspiration         真实灵感来源（游戏/品牌/海报）
- bg_colors           背景双色（深→更深 / 同 hue 双明度）
- glow_top / glow_bottom   径向光晕色（让顶/底 hue 错位）
- primary             主色（卡片头条 / heading 背景）
- accent_a            强调色 1（标题外发光、按钮、CTA）
- accent_b            强调色 2（次要装饰、QA 问题）
- text_on_dark        在 bg_colors 上字色
- text_on_primary     在 primary 上字色（可与 dark 不同）
- vibe                适用调性关键词（用于 brief 匹配）

如何选
=========
1. brief 给 scheme_id     → 直接取
2. brief 给 vibe 关键词    → 在该 scene 的方案里选 vibe 最匹配的
3. brief 啥都没给         → 取 scene 的默认（DEFAULT_SCHEME）

色彩学规则（防崩塌）
====================
1. text 与 bg 对比度 ≥ 4.5（WCAG AA），否则换 text_on_dark 极性
2. accent_a 与 primary 至少差 30° hue，否则视觉黏连
3. glow 颜色取 accent_a/b（hue 已经在 palette 内），不引入第 5 色
"""
from __future__ import annotations
import colorsys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .palette import hex_to_rgb, contrast_ratio, luminance


# ============================================================
# Scheme 数据结构
# ============================================================
@dataclass
class ColorScheme:
    id: str
    name: str
    theory: str          # mono / analogous / complementary / split-comp / triad / tetrad
    inspiration: str
    vibe: List[str]
    # 背景层
    bg_colors: Tuple[str, str]
    glow_top: str
    glow_bottom: str
    # 内容层
    primary: str
    accent_a: str
    accent_b: str
    neutral_panel: str   # 段落卡 / 须知 用的中性面板色
    # 文字层
    text_on_dark: str    # 通常 #FFFFFF / #F5F5FA
    text_on_primary: str # 在 primary 块上的字
    text_on_accent_a: str
    # 元数据
    brightness: str = "dark"   # dark | light
    pattern: str = "grid"      # grid | dots | none

    def to_palette_dict(self) -> Dict[str, str]:
        """转成现有 ctx.palette 兼容的字典。"""
        return {
            "primary": self.primary,
            "accent_a": self.accent_a,
            "accent_b": self.accent_b,
            "neutral": self.bg_colors[1],
            "neutral_panel": self.neutral_panel,
            # v0.6: 给文字打底用的深色面板，比 neutral_panel 更暗保证白字对比度
            "panel_dark": self._darken(self.bg_colors[1], 0.6),
            "text_on_dark": self.text_on_dark,
            "text_on_primary": self.text_on_primary,
            "text_on_accent_a": self.text_on_accent_a,
        }

    @staticmethod
    def _darken(hex_color: str, factor: float = 0.7) -> str:
        """把 hex 颜色乘以 factor 返回更暗的版本。factor<1 变暗。"""
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))
        return f"#{r:02X}{g:02X}{b:02X}"

    def to_canvas_cfg(self) -> Dict:
        """转成 _draw_background 用的 canvas 字典片段。"""
        return {
            "bg_strategy": "gradient-2",
            "bg_colors": list(self.bg_colors),
            "glow": True,
            "glow_top_color": self.glow_top,
            "glow_bottom_color": self.glow_bottom,
            "pattern": self.pattern,
            "grain": True,
        }


# ============================================================
# 配色方案库（每个 scene 至少 2 套，按"色彩学理论 + 真实灵感"配对）
# ============================================================
SCHEMES: Dict[str, List[ColorScheme]] = {

    # =========================================================
    # S1 · 新人训练营 / Onboarding —— 朝气、新关卡感
    # =========================================================
    "S1": [
        ColorScheme(
            id="S1-aurora",
            name="启航·极光",
            theory="analogous (蓝→紫)",
            inspiration="《星之卡比》新章节标题画 + 日航极光 KV",
            vibe=["朝气", "启航", "新人", "希望", "破晓"],
            bg_colors=("#1A2A6C", "#0B1340"),    # 深蓝 → 更深的午夜蓝
            glow_top="#FFC371",                   # 暖橙日出
            glow_bottom="#5B3FA0",                # 紫色返照
            primary="#3B82F6",                    # 主蓝
            accent_a="#FBBF24",                   # 金黄（CTA / 标题）
            accent_b="#A78BFA",                   # 淡紫（次装饰）
            neutral_panel="#13183D",
            text_on_dark="#F8FAFC",
            text_on_primary="#FFFFFF",
            text_on_accent_a="#1A2A6C",           # 深蓝压金
            brightness="dark",
            pattern="grid",
        ),
        ColorScheme(
            id="S1-pixel-dawn",
            name="像素·黎明",
            theory="split-complementary (青绿 + 暖橙黄)",
            inspiration="《Stardew Valley》黎明色 + IEG 校招长图",
            vibe=["像素", "游戏感", "1上手", "training-camp"],
            bg_colors=("#0F3D3E", "#062626"),    # 深青绿
            glow_top="#FFD66B",
            glow_bottom="#16A34A",
            primary="#10B981",                    # 翠绿主
            accent_a="#FBBF24",                   # 金（互补）
            accent_b="#FF8A65",                   # 珊瑚橙（次互补）
            neutral_panel="#0B2C2D",
            text_on_dark="#ECFDF5",
            text_on_primary="#06251F",            # 深绿压翠绿
            text_on_accent_a="#0F3D3E",
            brightness="dark",
            pattern="dots",
        ),
        ColorScheme(
            id="S1-nebula-blue",
            name="星云·蓝绿",
            theory="analogous (蓝绿→蓝)",
            inspiration="《Sea of Stars》主视觉 + 微软 Ignite 蓝",
            vibe=["科技", "稳健", "新一代"],
            bg_colors=("#0E2A47", "#051528"),
            glow_top="#22D3EE",
            glow_bottom="#A78BFA",
            primary="#0EA5E9",
            accent_a="#22D3EE",
            accent_b="#FBBF24",
            neutral_panel="#0A1F36",
            text_on_dark="#F0F9FF",
            text_on_primary="#FFFFFF",
            text_on_accent_a="#0E2A47",
            brightness="dark",
            pattern="grid",
        ),
    ],

    # =========================================================
    # S2 · 领导力 —— 沉稳、勋章、长期主义
    # =========================================================
    "S2": [
        ColorScheme(
            id="S2-deep-space",
            name="深空·勋章金",
            theory="complementary (深蓝紫 ↔ 金)",
            inspiration="《Civilization VI》成就页 + 大英博物馆视觉",
            vibe=["沉稳", "勋章", "战略", "高管", "长期"],
            bg_colors=("#1E1B4B", "#0B1020"),
            glow_top="#C9A961",
            glow_bottom="#475569",
            primary="#312E81",
            accent_a="#C9A961",                   # 古铜金（不反光）
            accent_b="#94A3B8",                   # 高级灰
            neutral_panel="#161433",
            text_on_dark="#F1F5F9",
            text_on_primary="#FFFFFF",
            text_on_accent_a="#1E1B4B",
            brightness="dark",
            pattern="grid",
        ),
        ColorScheme(
            id="S2-charcoal-gold",
            name="炭灰·浮金",
            theory="mono + 金点缀",
            inspiration="《Death Stranding》UI + 万宝龙",
            vibe=["商务", "克制", "高级感", "executive"],
            bg_colors=("#1C1F26", "#0A0C12"),
            glow_top="#D4AF37",
            glow_bottom="#3F4756",
            primary="#2A2E38",
            accent_a="#D4AF37",
            accent_b="#8C92A3",
            neutral_panel="#13161D",
            text_on_dark="#F5F5F5",
            text_on_primary="#F5F5F5",
            text_on_accent_a="#1C1F26",
            brightness="dark",
            pattern="none",
        ),
    ],

    # =========================================================
    # S3 · 技术分享 —— 极客、霓虹、电路
    # =========================================================
    "S3": [
        ColorScheme(
            id="S3-cyber-neon",
            name="霓虹·赛博",
            theory="split-comp (深蓝紫 + 青绿/洋红)",
            inspiration="《Cyberpunk 2077》UI + Linear 科技品牌",
            vibe=["极客", "霓虹", "未来", "AI", "tech-talk"],
            bg_colors=("#0F172A", "#020617"),
            glow_top="#22D3EE",
            glow_bottom="#A78BFA",
            primary="#1E293B",
            accent_a="#22D3EE",                   # 青蓝
            accent_b="#F472B6",                   # 洋红
            neutral_panel="#0B1322",
            text_on_dark="#E2E8F0",
            text_on_primary="#FFFFFF",
            text_on_accent_a="#0F172A",
            brightness="dark",
            pattern="grid",
        ),
        ColorScheme(
            id="S3-engine-core",
            name="引擎核心·荧光",
            theory="triad (蓝-绿-黄)",
            inspiration="《控制 Control》 + Unity Engine 视觉",
            vibe=["引擎", "代码", "硬核", "engineering"],
            bg_colors=("#0A1F1B", "#031210"),
            glow_top="#34D399",
            glow_bottom="#3B82F6",
            primary="#1E3A35",
            accent_a="#34D399",                   # 荧光绿
            accent_b="#FBBF24",                   # 警示黄
            neutral_panel="#0A1814",
            text_on_dark="#ECFDF5",
            text_on_primary="#FFFFFF",
            text_on_accent_a="#0A1F1B",
            brightness="dark",
            pattern="dots",
        ),
    ],

    # =========================================================
    # S4 · 文化活动 —— 温暖、节日、糖果
    # =========================================================
    "S4": [
        ColorScheme(
            id="S4-carnival",
            name="嘉年华·糖果",
            theory="triad (橙-粉-黄)",
            inspiration="《Splatoon》节庆 + 任天堂派对游戏",
            vibe=["节日", "团建", "庆典", "周年", "嘉年华"],
            bg_colors=("#FF7E5F", "#FEB47B"),    # 橙渐变（亮底）
            glow_top="#FFE082",
            glow_bottom="#EC4899",
            primary="#F97316",
            accent_a="#FACC15",                   # 阳光黄
            accent_b="#EC4899",                   # 糖果粉
            neutral_panel="#FFF7ED",
            text_on_dark="#1C1917",               # 浅底用深字
            text_on_primary="#FFFFFF",
            text_on_accent_a="#7C2D12",
            brightness="light",
            pattern="dots",
        ),
        ColorScheme(
            id="S4-jubilee-red",
            name="新春朱红·暖金",
            theory="warm-analogous (米白→暖橙→朱红)",
            inspiration="春节红包 + 故宫宫墙红 + 喜上眉梢",
            vibe=["新春", "喜庆", "团圆", "拜年", "红包", "拜年"],
            bg_colors=("#FFF8EE", "#FFE4B8"),    # 米白 → 浅暖橙渐变（更明亮）
            glow_top="#FCD34D",                   # 顶部金光（柔和）
            glow_bottom="#FB923C",                # 底部橙光（柔和）
            primary="#DC2626",                    # 中国红
            accent_a="#B91C1C",                   # 深朱红（重点强调）
            accent_b="#D97706",                   # 暖金（次强）
            neutral_panel="#FFFBF0",              # 微暖象牙白卡片
            text_on_dark="#3F0D12",               # 浅底深酒红字
            text_on_primary="#FFF7ED",
            text_on_accent_a="#FFF7ED",
            brightness="light",
            pattern="none",
        ),
        ColorScheme(
            id="S4-sunset-arcade",
            name="霓虹日落",
            theory="analogous (橙→紫红)",
            inspiration="80s synthwave + 复古街机",
            vibe=["复古", "synthwave", "嗨", "音乐节"],
            bg_colors=("#3B1053", "#150226"),
            glow_top="#FF6B6B",
            glow_bottom="#FFB75E",
            primary="#7C2D86",
            accent_a="#FF6B6B",
            accent_b="#FFB75E",
            neutral_panel="#250C3D",
            text_on_dark="#FFF7ED",
            text_on_primary="#FFFFFF",
            text_on_accent_a="#3B1053",
            brightness="dark",
            pattern="grid",
        ),
    ],

    # =========================================================
    # S5 · 晋升表彰 —— 仪式、聚光、华丽不浮夸
    # =========================================================
    "S5": [
        ColorScheme(
            id="S5-velvet-gold",
            name="酒红·浮金",
            theory="complementary (酒红 ↔ 金)",
            inspiration="奥斯卡颁奖典礼 + 卡地亚红",
            vibe=["晋升", "颁奖", "仪式", "表彰", "光荣"],
            bg_colors=("#3F0D12", "#170303"),
            glow_top="#FBBF24",
            glow_bottom="#7C2D12",
            primary="#7C2D12",
            accent_a="#FBBF24",
            accent_b="#FFFFFF",                   # 纯白聚光
            neutral_panel="#220606",
            text_on_dark="#FEF3C7",
            text_on_primary="#FFFFFF",
            text_on_accent_a="#3F0D12",
            brightness="dark",
            pattern="none",
        ),
        ColorScheme(
            id="S5-ink-honor",
            name="墨蓝·勋章",
            theory="split-comp (墨蓝 + 金/白)",
            inspiration="日本勋章证书 + 三宅一生",
            vibe=["东方", "克制", "证书", "学者风"],
            bg_colors=("#0E1B33", "#03081A"),
            glow_top="#E2C275",
            glow_bottom="#3B5998",
            primary="#1E3A8A",
            accent_a="#E2C275",
            accent_b="#F5F5F5",
            neutral_panel="#0B142A",
            text_on_dark="#F5F5F5",
            text_on_primary="#FFFFFF",
            text_on_accent_a="#0E1B33",
            brightness="dark",
            pattern="dots",
        ),
    ],

    # =========================================================
    # S6 · 内部赛事 / Hackathon —— 燃、对抗、电竞
    # =========================================================
    "S6": [
        ColorScheme(
            id="S6-arena",
            name="对抗竞技场",
            theory="complementary (红 ↔ 绿) + 黑底",
            inspiration="《Valorant》比赛 KV + 红牛电竞",
            vibe=["黑客马拉松", "对抗", "电竞", "决战"],
            bg_colors=("#170A0A", "#050202"),
            glow_top="#DC2626",
            glow_bottom="#16A34A",
            primary="#1A0808",
            accent_a="#EF4444",
            accent_b="#22C55E",
            neutral_panel="#150707",
            text_on_dark="#FEE2E2",
            text_on_primary="#FFFFFF",
            text_on_accent_a="#170A0A",
            brightness="dark",
            pattern="grid",
        ),
        ColorScheme(
            id="S6-circuit-flame",
            name="电路·火焰",
            theory="tetrad (红橙-黄-青-紫)",
            inspiration="《Tron》比赛回路 + AWS Game Tech",
            vibe=["创意大赛", "代码", "燃", "破纪录"],
            bg_colors=("#0A1232", "#020514"),
            glow_top="#F97316",
            glow_bottom="#22D3EE",
            primary="#1E1B4B",
            accent_a="#F97316",
            accent_b="#22D3EE",
            neutral_panel="#0B1230",
            text_on_dark="#E0E7FF",
            text_on_primary="#FFFFFF",
            text_on_accent_a="#0A1232",
            brightness="dark",
            pattern="grid",
        ),
    ],
}


# 每个场景的默认方案（vibe 都没给的兜底）
DEFAULT_SCHEME: Dict[str, str] = {
    "S1": "S1-aurora",
    "S2": "S2-deep-space",
    "S3": "S3-cyber-neon",
    "S4": "S4-carnival",
    "S5": "S5-velvet-gold",
    "S6": "S6-arena",
}


# ============================================================
# 选方案
# ============================================================
def list_schemes(scene: str) -> List[ColorScheme]:
    return SCHEMES.get(scene, SCHEMES["S1"])


def get_scheme(scene: str, scheme_id: Optional[str] = None,
               vibe_keywords: Optional[List[str]] = None) -> ColorScheme:
    """三段式选方案：

    1) scheme_id 命中 → 直接取
    2) vibe_keywords 与某方案 vibe 命中 → 取最高分
    3) 都没有 → 取 scene 默认
    """
    candidates = list_schemes(scene)

    if scheme_id:
        for s in candidates:
            if s.id == scheme_id:
                return s
        # id 没匹配，落到下一步

    if vibe_keywords:
        best, best_score = None, 0
        for s in candidates:
            score = sum(1 for k in vibe_keywords if k in s.vibe)
            if score > best_score:
                best, best_score = s, score
        if best:
            return best

    default_id = DEFAULT_SCHEME.get(scene, candidates[0].id)
    for s in candidates:
        if s.id == default_id:
            return s
    return candidates[0]


# ============================================================
# 一些工具：给装饰、文本智能选色
# ============================================================
def adjust_lightness(hex_color: str, delta: float) -> str:
    """把颜色明度加 delta（-1.0~1.0），用于派生 hover/press 等状态色。"""
    r, g, b = hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    l = max(0.0, min(1.0, l + delta))
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return "#{:02X}{:02X}{:02X}".format(int(r2*255), int(g2*255), int(b2*255))


def best_text_color(bg_hex: str, candidates: Optional[List[str]] = None) -> str:
    """从候选字色里挑对比度最高的；候选默认 [白, 深墨]。"""
    candidates = candidates or ["#FFFFFF", "#0E0F1A", "#1C1917"]
    bg_rgb = hex_to_rgb(bg_hex)
    best, best_cr = candidates[0], 0
    for c in candidates:
        cr = contrast_ratio(bg_rgb, hex_to_rgb(c))
        if cr > best_cr:
            best, best_cr = c, cr
    return best


def halo_color_for(text_hex: str) -> str:
    """给文字配一个反差描边色（防止文字落到过渡区融底）。"""
    return "#0E0F1A" if luminance(hex_to_rgb(text_hex)) > 0.5 else "#FFFFFF"
