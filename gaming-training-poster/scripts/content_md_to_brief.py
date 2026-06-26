"""content.md → brief.json 转换器（v0.10）

用法：
  python scripts/content_md_to_brief.py \
      --content assets/uploads/<场景名>/content.md \
      --out scripts/brief_<场景名>.json \
      --scene S4 \
      --palette named:festival_red

让用户按"写文档"的习惯写正文，引擎自动转成模块化 brief。

Markdown 约定（lightweight）：
─────────────────────────────────────────────
# 海报主标题（艺术字）
> 副标题（hero subtitle，可选）

## 项目背景
辞旧迎新…（lead_paragraph）

## 你将获得 / 课程目标 / 解决痛点
- 第一条
- 第二条
- 第三条

## 课程内容 / 时间轴 / 课程安排
| 时间 | 内容 | 形式 | 产出 |       ← 表格自动转 data_table
| 1.20 14:00 | 管理跃迁 | 线下 | 自评 |
| 1.22 10:00 | 业务复盘 | 线上 | 报告 |

## 讲师团
- 张老师 / IEG 学习与发展总监 / 头像: instructor_zhang.jpg
- 李老师 / 业务复盘专家 / 头像: instructor_li.jpg

## 注意事项
- 全程参与
- 提前请假
- 资料保密

## 报名方式
立即报名
- 截止时间：2026 年 2 月 5 日
- 名额：30 人
- 地点：IEG 28F

## 联系方式
联系人：dorrainzeng（曾子河）
─────────────────────────────────────────────
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


HEADING_KEYWORDS = {
    "lead":     ["项目背景", "导语", "摘要", "致新鹅", "前言"],
    "bullets":  ["你将获得", "课程目标", "解决痛点", "项目目标", "面向人群"],
    "schedule": ["课程内容", "时间轴", "课程安排", "项目内容", "课程表"],
    "faculty":  ["讲师团", "讲师阵容", "讲师资源", "讲师"],
    "notice":   ["注意事项", "学员须知", "纪律要求"],
    "register": ["报名方式", "报名", "如何报名"],
    "contact":  ["联系方式", "项目对接人", "联系人", "对接人"],
}


def _classify_heading(text: str) -> Optional[str]:
    for k, kws in HEADING_KEYWORDS.items():
        if any(kw in text for kw in kws):
            return k
    return None


def _is_table_row(line: str) -> bool:
    return line.lstrip().startswith("|") and line.rstrip().endswith("|")


def _parse_table(lines: List[str]) -> Dict[str, Any]:
    """| 时间 | 内容 | ...| 二维数组 + 列对齐"""
    rows = []
    for ln in lines:
        if not _is_table_row(ln):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        # 跳过分隔行 |---|---|
        if all(re.match(r"^[-:\s]*$", c) for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return {}
    headers = rows[0]
    data_rows = rows[1:]
    return {"headers": headers, "rows": data_rows}


def _parse_faculty(lines: List[str]) -> List[Dict[str, str]]:
    """每行格式：- 名字 / title / 头像: file.jpg"""
    out = []
    for ln in lines:
        ln = ln.strip()
        if not (ln.startswith("- ") or ln.startswith("* ")):
            continue
        parts = [p.strip() for p in ln[2:].split("/")]
        if not parts:
            continue
        item = {"name": parts[0]}
        for p in parts[1:]:
            if "头像" in p or "avatar" in p.lower():
                m = re.search(r"[:：]\s*(\S+)", p)
                if m:
                    item["avatar"] = m.group(1)
            else:
                item.setdefault("title", p)
        out.append(item)
    return out


def _parse_bullets(lines: List[str]) -> List[str]:
    out = []
    for ln in lines:
        ln = ln.strip()
        if ln.startswith("- ") or ln.startswith("* "):
            out.append(ln[2:].strip())
    return out


def md_to_brief(content_md: str, scene: str = "S4",
                palette: str = "named:festival_red",
                uploads_dir: str = "") -> Dict[str, Any]:
    """主转换入口。

    uploads_dir: 形如 'assets/uploads/lunar-new-year-2026'，brief 内所有素材路径会以此为根。
    """
    sections: List[Dict[str, Any]] = []
    title_text: Optional[str] = None
    subtitle_text: Optional[str] = None

    # 拆段：以 "## " 二级标题为分隔
    raw_lines = content_md.splitlines()
    blocks: List[Dict[str, Any]] = []
    cur_kind = None
    cur_title = None
    cur_lines: List[str] = []

    def flush():
        if cur_kind is not None:
            blocks.append({"kind": cur_kind, "title": cur_title, "lines": cur_lines.copy()})

    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            # 主标题
            title_text = stripped[2:].strip()
        elif stripped.startswith(">"):
            subtitle_text = stripped.lstrip(">").strip()
        elif stripped.startswith("## "):
            flush()
            cur_title = stripped[3:].strip()
            cur_kind = _classify_heading(cur_title) or "generic"
            cur_lines = []
        else:
            cur_lines.append(line)
        i += 1
    flush()

    # 1. hero_strip
    hero = {
        "type": "hero_strip",
        "height": 800,
        "logo_slot": None,
        "tight_bottom": True,
        "title_card": {
            "style": "ai_wordart",
            "lines": [title_text] if title_text else ["主标题"],
            "subtitle": subtitle_text or "",
            "width_ratio": 0.66,
            "offset_from_bottom": 60,
            "safe_zone": "bottom",
        }
    }
    if uploads_dir:
        hero["title_card"]["image"] = f"{uploads_dir}/wordart.png"
        hero["hero_mascot"] = {
            "image": f"{uploads_dir}/mascot.png",
            "side": "right", "height_ratio": 0.62, "offset_y": -30
        }
    sections.append(hero)

    section_index = 1
    for blk in blocks:
        kind = blk["kind"]
        title = blk["title"] or ""
        lines = [ln for ln in blk["lines"] if ln.strip() != ""]
        body_text = "\n".join(lines).strip()
        if not body_text:
            continue

        # 段标题（紧贴正文，已内化）
        if kind != "register":  # 报名段不要标题
            sections.append({
                "type": "section_title_bar",
                "style": "plain",
                "text": title,
                "text_color": "#FFFFFF",
                "underline_color": "auto",
            })
            section_index += 1

        if kind == "lead":
            sections.append({
                "type": "lead_paragraph",
                "panel_style": "frosted",
                "text": body_text.replace("\n", " "),
            })
        elif kind == "bullets":
            bullets = _parse_bullets(lines)
            sections.append({
                "type": "bullet_points_block",
                "bullets": bullets or [body_text],
            })
        elif kind == "schedule":
            # 优先识别表格；否则当 timeline 列表
            table = _parse_table(lines)
            if table:
                sections.append({
                    "type": "data_table",
                    "headers": table["headers"],
                    "rows": table["rows"],
                    "style": "soft",
                })
            else:
                bullets = _parse_bullets(lines)
                sections.append({
                    "type": "bullet_points_block",
                    "bullets": bullets or [body_text],
                })
        elif kind == "faculty":
            faculty = _parse_faculty(lines)
            members = []
            for item in faculty:
                m = {"name": item.get("name", ""), "title": item.get("title", "")}
                if item.get("avatar") and uploads_dir:
                    m["avatar"] = f"{uploads_dir}/{item['avatar']}"
                members.append(m)
            sections.append({
                "type": "faculty_grid",
                "layout": "compact" if len(members) > 4 else "detail",
                "members": members,
            })
        elif kind == "notice":
            bullets = _parse_bullets(lines)
            sections.append({
                "type": "notice_box",
                "inline": True,
                "bullets": bullets or [body_text],
            })
        elif kind == "register":
            # 第一行通常是按钮文字；后续 bullet 是 pre/post 提示
            btn_text = "立即报名"
            pre_lines: List[str] = []
            for ln in lines:
                t = ln.strip()
                if t and not (t.startswith("- ") or t.startswith("* ")):
                    btn_text = t
                    break
            for ln in lines:
                t = ln.strip()
                if t.startswith("- ") or t.startswith("* "):
                    pre_lines.append(t[2:])
            sections.append({
                "type": "cta_button",
                "text": btn_text,
                "pre_lines": pre_lines[:2],
                "post_lines": pre_lines[2:],
            })
        elif kind == "contact":
            sections.append({
                "type": "contact_inline",
                "text": body_text.replace("\n", " "),
            })
        else:
            # generic：当作 lead_paragraph
            sections.append({
                "type": "lead_paragraph",
                "panel_style": "frosted",
                "text": body_text.replace("\n", " "),
            })

    brief = {
        "_doc": "由 content_md_to_brief.py 自动生成；可继续手工微调。",
        "schema_version": 2,
        "scene": scene,
        "canvas": {
            "width": 1200,
            "format": "long-poster",
            "bg_strategy": "gradient-2",
            "bg_colors": ["#FFF8EE", "#FFE4B8"],
            "glow": False,
            "pattern": "none",
            "grain": False,
            "palette_strategy": palette,
        },
        "decoration_family": "ceremony-gold",
        "seed": 26,
        "logo_position": "top",
        "logo_align": "center",
        "logo_height": 96,
        "logos": ["assets/ieg_hr_color.png"],
        "sections": sections,
        "decorations": {"density": "none"},
    }
    if uploads_dir:
        brief["canvas"]["bg_image_path"] = f"{uploads_dir}/hero_kv.png"
        brief["canvas"].update({
            "bg_image_fit": "width",
            "bg_image_max_height": 520,
            "bg_image_height": 520,
            "bg_image_blend_h": 200,
            "bg_image_chroma_key": True,
            "bg_image_chroma_bg_kind": "dark",
            "bg_image_chroma_dark_max": 110,
            "bg_image_chroma_sat_max": 28,
            "bg_image_chroma_softness": 22,
        })
    return brief


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", required=True, help="content.md 路径")
    ap.add_argument("--out", required=True, help="输出 brief.json")
    ap.add_argument("--scene", default="S4")
    ap.add_argument("--palette", default="named:festival_red")
    ap.add_argument("--uploads", default="",
                    help="该场景的 uploads 目录，如 assets/uploads/lunar-new-year-2026")
    args = ap.parse_args()

    content = Path(args.content).read_text(encoding="utf-8")
    brief = md_to_brief(content, scene=args.scene,
                        palette=args.palette,
                        uploads_dir=args.uploads.rstrip("/"))
    Path(args.out).write_text(
        json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] {args.out} （{len(brief['sections'])} sections）")
    print("可用 scripts/compose_poster_v2.py --brief", args.out, "--out output/xxx.png 渲染")


if __name__ == "__main__":
    main()
