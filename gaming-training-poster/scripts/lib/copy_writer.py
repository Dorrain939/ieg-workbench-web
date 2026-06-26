"""
文案生成器 (copy_writer) —— 解决"文案靠抠原图"这一硬伤。

定位
====
这不是一个跑大模型的"自动文案 AI"，而是一套结构化文案模板 + 字段拼装器。
它做的事：
  - 提供 6 个场景 × 主要组件 的"骨架 + 风格短语"模板
  - 接收 brief 里的关键字段（topic / date / department / role / target / cta_text...）
  - 按场景调性挑词、按字段填空、按上下文挑句式，输出可直接进 brief.sections 的完整文案
  - 同时输出可读的 reasoning（为什么这么写），方便用户改

为什么不直接 LLM 生成？
======================
1. 调性可控、可复盘、可审计——HR/L&D 文案的红线很严
2. 不依赖外部 API key、零网络成本、可批量出
3. 与 scene_router 强耦合，避免"什么都生成得很顺"的同质化

如果业务方想接 LLM
====================
保留接口 `propose(scene, component, fields, *, llm_hook=None)` —— 当 llm_hook
被注入时，会把骨架文案当作 system prompt 发给 LLM 做润色，再返回。
默认 llm_hook=None，纯模板模式。
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


# ============================================================
# 场景调性词库
# ============================================================
SCENE_TONE: Dict[str, Dict[str, List[str]]] = {
    "S1": {
        "verbs":     ["启航", "踏上", "解锁", "点亮", "迎接"],
        "nouns":     ["新关卡", "成长地图", "工程脉络", "技术全景", "新手村"],
        "feelings":  ["热血", "新鲜", "充满期待", "好奇心爆棚"],
        "pronouns":  ["新鹅", "新同学", "新人"],
        "endings":   ["让我们一起", "出发吧", "Welcome aboard", "新征程开始"],
    },
    "S2": {
        "verbs":     ["谋远", "锤炼", "进阶", "深思", "塑造"],
        "nouns":     ["战略", "组织力", "领导力", "决策力", "未来视野"],
        "feelings":  ["沉稳", "笃定", "格局", "责任"],
        "pronouns":  ["管理者", "总监", "Leader"],
        "endings":   ["与组织共生长", "向远而行", "lead the way"],
    },
    "S3": {
        "verbs":     ["拆解", "深潜", "构建", "突破", "重塑"],
        "nouns":     ["引擎", "架构", "AI 工程", "算法", "工具链"],
        "feelings":  ["极客", "硬核", "上头"],
        "pronouns":  ["开发者", "工程师", "Tech Talker"],
        "endings":   ["来一场技术对话", "把答案给所有人"],
    },
    "S4": {
        "verbs":     ["相聚", "庆祝", "回响", "共度", "拥抱"],
        "nouns":     ["仪式感", "回忆", "故事", "热闹", "我们"],
        "feelings":  ["温暖", "热闹", "走心", "幸福"],
        "pronouns":  ["每一位", "大家", "同伴"],
        "endings":   ["把这一刻刻进时间线", "see you there"],
    },
    "S5": {
        "verbs":     ["登台", "致敬", "祝贺", "授予", "见证"],
        "nouns":     ["勋章", "里程碑", "高光时刻", "荣誉", "成长"],
        "feelings":  ["庄重", "荣耀", "动容"],
        "pronouns":  ["TA", "新晋"],
        "endings":   ["此刻属于你", "因热爱而被看见"],
    },
    "S6": {
        "verbs":     ["开战", "对决", "燃起", "破壁", "决出"],
        "nouns":     ["创意", "代码", "极限", "胜负", "灵感"],
        "feelings":  ["热血", "燃", "竞技", "肾上腺素"],
        "pronouns":  ["开发者", "战队", "玩家们"],
        "endings":   ["全力以赴", "ready to ship", "let it rip"],
    },
}


# ============================================================
# 模板：每个场景 × 每个组件 的写法
# ============================================================
# 用 {占位符} 表示从 fields 取的字段；模板可以多版本，runtime 随机选一条
TEMPLATES: Dict[str, Dict[str, List[str]]] = {

    # ----------- hero 标题（短语，2-3 字一行最佳）-----------
    "hero_title": {
        "S1": ["{topic}", "{topic} · 启航", "新鹅养成", "{topic}训练营"],
        "S2": ["{topic}", "{topic} · 进阶", "{topic} 精英计划"],
        "S3": ["{topic}", "{topic} 技术周", "Tech · {topic}"],
        "S4": ["{topic}", "{topic} 嘉年华", "{topic} · 一起来"],
        "S5": ["{topic}", "{topic} · 高光时刻", "致敬{topic}"],
        "S6": ["{topic}", "{topic} HACK", "{topic} 决战"],
    },

    "hero_subtitle": {
        "S1": ["欢迎加入 {department} 大家庭"],
        "S2": ["写给每一位{pronoun}"],
        "S3": ["{department} 技术分享 · {date}"],
        "S4": ["{date} · {location}"],
        "S5": ["{department} · {date}"],
        "S6": ["{date} · {location} · 燃就完事"],
    },

    # ----------- lead_paragraph 欢迎/引言 -----------
    "lead_paragraph": {
        "S1": [
            "{pronoun}你好，欢迎加入 {department}。从你按下 offer 那一刻起，"
            "你就不再只是一名玩家——而是要成为下一个把好玩做出来的人。"
            "{topic} 是为你准备的第一次{noun}，它会陪你 {duration}，"
            "把你需要的{noun}一点点交到你手里。准备好了吗？{ending}。"
        ],
        "S2": [
            "{topic} 不只是一次培训，而是为有志于走得更远的{pronoun}准备的"
            "{noun}。在这里，你将{verb}{noun}、与同行者交换问题、把"
            "「我」变成「我们」。{ending}。"
        ],
        "S3": [
            "{topic} 把 {department} 内部最前沿的{noun}摊在桌上：从底层"
            "到框架、从工具到方法。每一场都是一次{noun}级别的{verb}。"
            "{ending}。"
        ],
        "S4": [
            "{topic} 是属于 {department} 全体{pronoun}的{noun}时刻。"
            "我们不谈 KPI，只谈那些好玩的、好笑的、值得被记住的事。"
            "{date}，{location}，{ending}。"
        ],
        "S5": [
            "感谢每一位被{topic}看见的{pronoun}。你们的{noun}与坚持，"
            "让 {department} 一次次跨过节点。{ending}——因为热爱本身就值得被致敬。"
        ],
        "S6": [
            "{topic} 不只是一场比赛，是 {department} 把「奇怪的想法」放出来奔跑的{noun}。"
            "{duration} 内，组队、构思、写代码、抢上线——{ending}。"
        ],
    },

    # ----------- info_card / 关于 X -----------
    "info_card_about": {
        "S1": [
            "{topic} 是面向 {department} 全体{pronoun}的{role_target}{tag}培养项目。"
            "通过{phases}的组合形式，帮你打下扎实的{noun}基础，让你更快地从「上手」走到「上路」。"
        ],
        "S2": [
            "{topic} 面向 {department} 的 {role_target}，覆盖{phases}全链路。"
            "我们相信好的管理者是被锤炼出来的——这个{noun}就是你的训练场。"
        ],
        "S3": [
            "{topic} 面向 {department} 所有 {role_target}，由内部技术专家轮值主讲。"
            "覆盖 {phases}，每场都有 Q&A 和 demo，硬核到底。"
        ],
        "S4": [
            "{topic} 面向 {department} 全体{pronoun}，{phases}串成一整天的"
            "{noun}。带上你最舒服的衣服来就行，剩下的都准备好了。"
        ],
        "S5": [
            "{topic} 是 {department} 每{cycle}固定举办的表彰盛典，授予在 {phases} "
            "中表现卓越的{pronoun}。每一枚{noun}背后都是一段值得被讲述的故事。"
        ],
        "S6": [
            "{topic} 是 {department} 内部级别最高的代码竞技。"
            "{phases} 三阶段，从命题到 Demo Day，48 小时把想法变成产品。"
        ],
    },

    # ----------- info_card_with_qr / 关于报名/调查问卷 -----------
    "info_card_qr": {
        "S1": [
            "为了给你匹配最合适的{noun}与导师，请扫码完成入营调查问卷。"
            "请按你的真实情况认真填写，所有信息严格保密。"
            "截止时间：{deadline}。完成即可领取「{topic} 定制礼物」一份。"
        ],
        "S2": [
            "请扫码报名 {topic}。请如实填写背景与期待，"
            "我们会据此为你匹配同侪小组与教练。截止时间：{deadline}。"
        ],
        "S3": [
            "扫码报名/收看 {topic} 直播。"
            "线下席位有限，先报先得；线上席位无上限。截止时间：{deadline}。"
        ],
        "S4": [
            "扫码登记参与 {topic}。{deadline} 前完成可领取限定纪念礼。"
        ],
        "S5": [
            "扫码进入 {topic} 线上颁奖直播间，{date} 准时开播。"
        ],
        "S6": [
            "扫码报名 {topic}：单人组队均可，截止 {deadline}。报名后会拉入"
            "选手群，命题与时间表第一时间同步。"
        ],
    },

    # ----------- section_title_bar 段落分隔标题 -----------
    "section_title_qa":      ["常见问题解答", "FAQ", "Q&A"],
    "section_title_schedule":["项目时间线", "课程安排", "Schedule", "排期"],
    "section_title_rules":   ["参与须知", "注意事项", "Rules"],
    "section_title_contact": ["联系我们", "Contact"],

    # ----------- contact_card -----------
    "contact_card": {
        "*": [
            "有任何疑问，欢迎联系{owner_role} {owner_name}。"
            "请扫码添加企业微信，备注「姓名 + 部门 + {role_target}」。"
        ],
    },

    # ----------- cta_button -----------
    "cta_button": {
        "S1": ["立即报名", "我要加入", "Join the Bootcamp"],
        "S2": ["申请进入", "提名/自荐", "Apply"],
        "S3": ["扫码占座", "我要听！", "Reserve"],
        "S4": ["我要参加", "约一个", "Count me in"],
        "S5": ["进入直播间", "围观颁奖", "Watch live"],
        "S6": ["我要组队", "立即报名", "Form your squad"],
    },
}


# ============================================================
# 字段默认值（缺字段时用兜底，避免模板报错）
# ============================================================
DEFAULT_FIELDS: Dict[str, str] = {
    "topic": "训练营",
    "department": "腾讯互动娱乐事业群（IEG）",
    "date": "近期",
    "deadline": "活动开始前 3 天",
    "duration": "若干周",
    "location": "深圳·腾讯滨海大厦",
    "role_target": "目标人群",
    "owner_role": "项目运营",
    "owner_name": "（待填写）",
    "tag": "【必修】",
    "phases": "岗前学习 / 入职后培训 / 实战",
    "cycle": "季度",
}


# ============================================================
# Engine
# ============================================================
@dataclass
class CopyContext:
    scene: str
    fields: Dict[str, str] = field(default_factory=dict)
    seed: int = 42
    llm_hook: Optional[Callable[[str, str], str]] = None

    def f(self, key: str) -> str:
        if key in self.fields and self.fields[key]:
            return str(self.fields[key])
        return DEFAULT_FIELDS.get(key, f"<{key}>")


def _pick_word(scene: str, kind: str, rng: random.Random) -> str:
    """从 SCENE_TONE 里挑一个词。kind ∈ {verbs,nouns,feelings,pronouns,endings}"""
    bag = SCENE_TONE.get(scene, SCENE_TONE["S1"]).get(kind, [""])
    return rng.choice(bag) if bag else ""


def _render(template: str, ctx: CopyContext, rng: random.Random) -> str:
    """支持的占位符：
       {topic} {department} {date} {deadline} {duration} {location}
       {role_target} {owner_role} {owner_name} {tag} {phases} {cycle}
       {pronoun} {verb} {noun} {feeling} {ending}
    """
    repl: Dict[str, str] = {k: ctx.f(k) for k in DEFAULT_FIELDS}
    repl["pronoun"] = _pick_word(ctx.scene, "pronouns", rng)
    repl["verb"]    = _pick_word(ctx.scene, "verbs", rng)
    repl["noun"]    = _pick_word(ctx.scene, "nouns", rng)
    repl["feeling"] = _pick_word(ctx.scene, "feelings", rng)
    repl["ending"]  = _pick_word(ctx.scene, "endings", rng)

    out = template
    for k, v in repl.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def propose(component: str, ctx: CopyContext) -> str:
    """生成一段文案。component 同 brief.sections 里的 type 或细分键
    （比如 'lead_paragraph' / 'info_card_about' / 'cta_button'）。
    """
    rng = random.Random(ctx.seed + hash(component) % 1024)

    bag = TEMPLATES.get(component)
    if bag is None:
        return f"<no template for {component}>"

    if isinstance(bag, list):
        text = rng.choice(bag)
    else:
        # dict by scene
        candidates = bag.get(ctx.scene) or bag.get("*") or []
        if not candidates:
            return f"<no template for {component}@{ctx.scene}>"
        text = rng.choice(candidates)

    rendered = _render(text, ctx, rng)

    # 可选 LLM 润色
    if ctx.llm_hook is not None:
        try:
            polished = ctx.llm_hook(component, rendered)
            if polished and isinstance(polished, str):
                return polished
        except Exception as e:
            print(f"[copy_writer] llm_hook failed: {e}")
    return rendered


def auto_fill_brief(brief: dict, fields: Dict[str, str], *,
                    llm_hook: Optional[Callable[[str, str], str]] = None) -> dict:
    """对 brief.sections 里所有"空文本字段"自动补齐。

    规则：只在以下情况触发自动文案：
      - sections[i].text   为空 / "AUTO"  → 用 lead_paragraph 模板
      - sections[i].body   为空 / "AUTO"  → 用 info_card_about 或 info_card_qr
      - sections[i].lines  含 "AUTO"      → 用 hero_title
      - sections[i].heading 为空 / "AUTO" → 用 component-specific 标题模板

    已有内容的字段不动，避免覆盖人工撰写。
    """
    scene = brief.get("scene", "S1")
    seed = brief.get("seed", 42)
    ctx = CopyContext(scene=scene, fields=fields, seed=seed, llm_hook=llm_hook)

    out_sections = []
    for s in brief.get("sections", []):
        s = dict(s)  # 浅拷
        t = s.get("type")

        if t == "hero_strip":
            card = dict(s.get("title_card") or {})
            lines = card.get("lines") or []
            if not lines or any(l == "AUTO" for l in lines):
                title = propose("hero_title", ctx)
                # 主标题超过 6 字时强制拆两行
                if len(title) > 6:
                    mid = len(title) // 2
                    card["lines"] = [title[:mid], title[mid:]]
                else:
                    card["lines"] = [title]
            s["title_card"] = card

        elif t == "lead_paragraph":
            if not s.get("text") or s["text"] == "AUTO":
                s["text"] = propose("lead_paragraph", ctx)

        elif t == "info_card":
            if not s.get("heading") or s["heading"] == "AUTO":
                s["heading"] = "关于 {topic}".replace("{topic}", ctx.f("topic"))
            if not s.get("body") or s["body"] == "AUTO":
                s["body"] = propose("info_card_about", ctx)

        elif t == "info_card_with_qr":
            if not s.get("heading") or s["heading"] == "AUTO":
                s["heading"] = "关于报名"
            if not s.get("body") or s["body"] == "AUTO":
                s["body"] = propose("info_card_qr", ctx)

        elif t == "section_title_bar":
            if not s.get("text") or s["text"] == "AUTO":
                # 简单按下一个 section 推断
                s["text"] = "FAQ"

        elif t == "cta_button":
            if not s.get("text") or s["text"] == "AUTO":
                s["text"] = propose("cta_button", ctx)

        elif t == "contact_card":
            if not s.get("text") or s["text"] == "AUTO":
                s["text"] = propose("contact_card", ctx)

        out_sections.append(s)

    brief = dict(brief)
    brief["sections"] = out_sections
    return brief
