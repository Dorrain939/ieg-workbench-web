"""FastAPI 路由：海报拖拽编辑器后端。

会调用既有 skill 引擎 (compose_long_poster) 渲染海报。
skill 路径：当前工作包内 gaming-training-poster/
"""
import json
import os
import re
import sys
import uuid
import shutil
import time
import pathlib
import traceback
from typing import Optional

import urllib.request
import urllib.error

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse

# 项目根目录
from app_paths import WEB_ROOT, PACKAGE_ROOT, UPLOADS_DIR, OUTPUTS_DIR

# 让 Python import 当前工作包内的 skill 引擎，而不是 ~/.codebuddy 里的旧版本
SKILL_DIR = PACKAGE_ROOT / "gaming-training-poster"
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# 导入引擎
from compose_poster_v2 import compose_long_poster  # noqa: E402
UPLOAD_DIR = UPLOADS_DIR
OUTPUT_DIR = OUTPUTS_DIR
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# 模板目录（skill 自带的 brief_*.json）
TEMPLATE_DIR = SCRIPTS_DIR

import schemas  # 本项目的 schemas.py
import asset_types  # 视觉资产类型表

router = APIRouter(prefix="/api")


def _extract_json_object(text: str) -> dict:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except Exception:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        return json.loads(raw[start:end + 1])
    raise ValueError("no json object")


def _extract_home_assistant_fields(message: str) -> dict:
    """对 LLM 路由做确定性兜底，避免负责人/主题色这类明确信息漏填。"""
    text = message or ""
    out = {}
    owner_match = re.search(r"(?:负责人|owner|HRBP|hrbp)\s*[：:是为叫]?\s*([\u4e00-\u9fa5A-Za-z·]{2,12})", text, re.I)
    if owner_match:
        out["owner_name"] = owner_match.group(1).strip()
    type_match = re.search(r"([ABC])\s*(?:型|类|项目类型)?", text, re.I)
    if type_match:
        out["project_type"] = type_match.group(1).upper()
    color_map = {
        "紫": "#7C3AED",
        "紫色": "#7C3AED",
        "蓝": "#2563EB",
        "蓝色": "#2563EB",
        "绿色": "#059669",
        "绿": "#059669",
        "青": "#0891B2",
        "青色": "#0891B2",
        "珊瑚": "#F97316",
        "橙": "#F97316",
        "橙色": "#F97316",
        "红": "#DC2626",
        "红色": "#DC2626",
        "粉": "#DB2777",
        "粉色": "#DB2777",
        "黑": "#111827",
        "黑色": "#111827",
    }
    hex_match = re.search(r"#[0-9a-fA-F]{6}", text)
    if hex_match:
        out["theme_color"] = hex_match.group(0)
    else:
        for key, val in color_map.items():
            if f"主题色{key}" in text or f"主题色：{key}" in text or f"主题色为{key}" in text or key + "主题" in text:
                out["theme_color"] = val
                break
    name_match = re.search(r"(?:创建|新建|新增|建一个|开一个)\s*([^，。,.；;]+?)(?:项目|海报|文案|，|。|,|\.|；|;|$)", text)
    if name_match:
        out["project_name"] = name_match.group(1).strip()
    return out


# ============================================================
# 1. GET /api/schemas — 返回所有 section schema + canvas schema
# ============================================================
@router.get("/schemas")
def get_schemas():
    return {
        "canvas": schemas.get_canvas_schema(),
        "sections": {
            name: {
                "label": meta["label"],
                "icon": meta["icon"],
                "fields": meta["fields"],
            }
            for name, meta in schemas.SCHEMAS.items()
        },
        "section_types": schemas.all_section_types(),
        "asset_types": asset_types.ASSET_TYPES,
    }


@router.post("/home-assistant/route")
def route_home_assistant(payload: dict):
    """首页 AI 助手：用 LLM 把自然语言解析成可控页面动作。"""
    message = str(payload.get("message") or "").strip()
    mode = str(payload.get("mode") or "project").strip() or "project"
    projects = payload.get("projects") or []
    attachments = payload.get("attachments") or []
    if not message:
        raise HTTPException(400, "消息为空")

    compact_projects = []
    if isinstance(projects, list):
        for p in projects[:80]:
            if isinstance(p, dict):
                compact_projects.append({
                    "id": str(p.get("id") or ""),
                    "name": str(p.get("name") or ""),
                    "status": str(p.get("status") or ""),
                    "owner": str((p.get("owner") or {}).get("name") or ""),
                    "updated_at": str(p.get("updated_at") or ""),
                })

    compact_attachments = []
    if isinstance(attachments, list):
        for item in attachments[:40]:
            if isinstance(item, dict):
                compact_attachments.append({
                    "filename": str(item.get("filename") or ""),
                    "format": str(item.get("format") or ""),
                    "size": int(item.get("size") or 0),
                })

    import llm_client
    try:
        llm = llm_client.LLMClient()
        if not llm.is_configured:
            raise HTTPException(503, "LLM 未配置：请先在设置抽屉配置大语言模型")
    except llm_client.LLMError as e:
        raise HTTPException(503, str(e))

    prompt = f"""
你是“IEG 人才发展项目管理 AI 工作台”的首页路由助手。
你的任务是把用户自然语言解析成一个安全、可控的页面动作 JSON。

当前助手模式：{mode}
用户输入：{message}

可选动作 intent：
- create_project：用户要创建/新增一个上层项目
- open_project_function：用户要进入某个已有项目的某个功能
- filter_recent：用户要看最近/本周更新项目
- open_project：用户只想打开某个已有项目概览
- ask_clarify：信息不足，需要追问

可选 target_function：
- overview：项目概览
- copywriter：海报 > 文案
- poster_brief：海报 > 生图
- interview_outline：访谈 > 访谈提纲
- ppt_outline：PPT > 大纲
- kb：项目知识库
- report：研究报告场景（当前还没有独立页面，前端会先进入概览）

已有项目列表：
{json.dumps(compact_projects, ensure_ascii=False)}

本轮首页助手附件列表（前端会在确定项目后放入对应项目/功能知识库，严禁理解成平台全局资料）：
{json.dumps(compact_attachments, ensure_ascii=False)}

规则：
1. 必须只返回严格 JSON，不要 markdown。
2. 如果用户说“海报文案/写海报文案/文案”，target_function=copywriter。
3. 如果用户说“海报生图/出图/生成海报/做海报图”，target_function=poster_brief。
4. 如果用户说 PPT/课件/幻灯片，target_function=ppt_outline。
5. 如果用户说访谈，target_function=interview_outline。
6. 如果用户说研究报告/报告，target_function=report。
7. 如果能从已有项目列表匹配项目，返回 target_project_id。
8. 如果要创建项目，从用户输入里提取 project_name；没有就留空并 ask_clarify。
9. 如果用户提到负责人/owner/HRBP，提取 owner_name。
10. 如果用户提到蓝色、紫色、绿色、珊瑚色等主题色，转换成合适的十六进制 theme_color。
11. 如果能判断项目类型，返回 project_type=A/B/C；不能判断则留空，不要乱猜。
12. 不要编造不存在的 target_project_id。
13. 如果用户只上传文档且没有明确功能，优先根据文件名/用户话判断：文案资料进入 copywriter，图片/视觉素材进入 poster_brief，普通项目资料进入 kb。

返回格式：
{{
  "intent": "create_project|open_project_function|filter_recent|open_project|ask_clarify",
  "target_project_id": "已有项目 id 或空字符串",
  "target_function": "overview|copywriter|poster_brief|interview_outline|ppt_outline|kb|report",
  "project_name": "新建项目标题或空字符串",
  "owner_name": "负责人姓名或空字符串",
  "project_type": "A|B|C 或空字符串",
  "theme_color": "#RRGGBB 或空字符串",
  "reply": "给用户看的简短说明"
}}
"""
    try:
        resp = llm.chat(
            [
                {"role": "system", "content": "你只输出合法 JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            timeout=60,
        )
        parsed = _extract_json_object(resp.get("content") or "")
    except llm_client.LLMError as e:
        raise HTTPException(502, f"LLM 调用失败：{e}")
    except Exception as e:
        raise HTTPException(502, f"LLM 未返回合法动作 JSON：{e}")

    allowed_intents = {"create_project", "open_project_function", "filter_recent", "open_project", "ask_clarify"}
    allowed_functions = {"overview", "copywriter", "poster_brief", "interview_outline", "ppt_outline", "kb", "report"}
    intent = parsed.get("intent") if parsed.get("intent") in allowed_intents else "ask_clarify"
    target_function = parsed.get("target_function") if parsed.get("target_function") in allowed_functions else "overview"
    target_project_id = str(parsed.get("target_project_id") or "")
    if target_project_id and not any(p["id"] == target_project_id for p in compact_projects):
        target_project_id = ""
    fallback = _extract_home_assistant_fields(message)
    owner_name = str(parsed.get("owner_name") or fallback.get("owner_name") or "")[:40]
    project_type = parsed.get("project_type") if parsed.get("project_type") in {"A", "B", "C"} else fallback.get("project_type", "")
    theme_color = str(parsed.get("theme_color") or fallback.get("theme_color") or "")
    if not re.match(r"^#[0-9a-fA-F]{6}$", theme_color):
        theme_color = ""
    project_name = str(parsed.get("project_name") or fallback.get("project_name") or "")[:80]
    return {
        "intent": intent,
        "target_project_id": target_project_id,
        "target_function": target_function,
        "project_name": project_name,
        "owner_name": owner_name,
        "project_type": project_type,
        "theme_color": theme_color,
        "reply": str(parsed.get("reply") or "我已经理解你的需求。")[:300],
    }


# ============================================================
# 2. GET /api/templates — 列出现有 brief 模板
# ============================================================
@router.get("/templates")
def list_templates():
    items = []
    for f in sorted(TEMPLATE_DIR.glob("brief_*.json")):
        items.append({
            "name": f.stem,           # brief_vfx-bootcamp-2026
            "label": f.stem.replace("brief_", "").replace("-", " ").replace("_", " "),
            "path": str(f),
        })
    return {"templates": items}


# ============================================================
# 3. GET /api/template/{name} — 返回某个 brief 内容
# ============================================================
@router.get("/template/{name}")
def get_template(name: str):
    # 安全：只允许 brief_* 文件名
    if not name.startswith("brief_"):
        name = "brief_" + name
    fp = TEMPLATE_DIR / f"{name}.json"
    if not fp.exists():
        raise HTTPException(404, f"模板不存在: {name}")
    with open(fp, "r", encoding="utf-8") as f:
        brief = json.load(f)
    return {"name": name, "brief": brief}


# ============================================================
# 4. POST /api/upload — 上传素材
# ============================================================
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    asset_type: Optional[str] = Form(None),
    asset_label: Optional[str] = Form(None),
    related_name: Optional[str] = Form(None),
    related_title: Optional[str] = Form(None),
    variant: Optional[str] = Form(None),
):
    if not session_id:
        session_id = "default"
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(exist_ok=True)

    # 文件名清洗：保留扩展名，加时间戳前缀避免覆盖
    safe_name = pathlib.Path(file.filename).name
    ts = int(time.time() * 1000)
    target = session_dir / f"{ts}_{safe_name}"

    with open(target, "wb") as f:
        shutil.copyfileobj(file.file, f)

    normalized_type = asset_types.infer_asset_type(safe_name, asset_type)
    meta = {
        "filename": safe_name,
        "path": str(target.absolute()),
        "url": f"/api/asset/{session_id}/{target.name}",
        "size": target.stat().st_size,
        "asset_type": normalized_type,
        "asset_type_label": asset_types.asset_type_label(normalized_type),
        "asset_label": (asset_label or "").strip(),
        "related_name": (related_name or "").strip(),
        "related_title": (related_title or "").strip(),
        "variant": (variant or "").strip(),
        "uploaded_at": ts,
    }
    meta_path = target.with_suffix(target.suffix + ".meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


# ============================================================
# 5. GET /api/asset/{session_id}/{filename} — 预览/获取上传素材
# ============================================================
@router.get("/asset/{session_id}/{filename}")
def get_asset(session_id: str, filename: str):
    fp = UPLOAD_DIR / session_id / filename
    if not fp.exists():
        raise HTTPException(404)
    return FileResponse(fp)


# ============================================================
# 6. GET /api/skill-asset?path=... — 访问 skill 内现有素材
#    （安全：只允许 skill 目录下的路径）
# ============================================================
@router.get("/skill-asset")
def get_skill_asset(path: str):
    abs_path = pathlib.Path(path).expanduser().resolve()
    allowed_roots = [
        SKILL_DIR.resolve(),
        UPLOAD_DIR.resolve(),
        (WEB_ROOT / "projects").resolve(),
        pathlib.Path.home() / ".codebuddy" / "skills" / "gaming-training-poster" / "assets" / "uploads",
        pathlib.Path.home() / "Desktop" / "poster-web-backup-20260607-194209" / "poster-web" / "uploads",
        pathlib.Path.home() / "Desktop" / "IEG人才发展项目管理AI工作台-完整源码-20260625" / "poster-web" / "uploads",
    ]
    ok = False
    for root in allowed_roots:
        try:
            abs_path.relative_to(root.resolve())
            ok = True
            break
        except Exception:
            continue
    if not ok:
        raise HTTPException(403, "禁止访问素材白名单外的文件")
    if not abs_path.exists():
        raise HTTPException(404)
    return FileResponse(abs_path)


# ============================================================
# 7. GET /api/skill-uploads — 列出 skill 已有的素材库（按场景分组）
# ============================================================
@router.get("/skill-uploads")
def list_skill_uploads():
    base = SKILL_DIR / "assets" / "uploads"
    if not base.exists():
        return {"scenes": []}

    scenes = []
    for scene_dir in sorted(base.iterdir()):
        if not scene_dir.is_dir():
            continue
        files = []
        for f in sorted(scene_dir.glob("*")):
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                meta = {}
                meta_fp = f.with_suffix(f.suffix + ".meta.json")
                if meta_fp.exists():
                    try:
                        meta = json.loads(meta_fp.read_text(encoding="utf-8"))
                    except Exception:
                        meta = {}
                typ = asset_types.infer_asset_type(f.name, meta.get("asset_type"))
                files.append({
                    "name": f.name,
                    "path": str(f.absolute()),
                    "url": f"/api/skill-asset?path={f.absolute()}",
                    "asset_type": typ,
                    "asset_type_label": asset_types.asset_type_label(typ),
                    "asset_label": meta.get("asset_label") or "",
                    "related_name": meta.get("related_name") or "",
                    "related_title": meta.get("related_title") or "",
                })
        if files:
            scenes.append({
                "scene": scene_dir.name,
                "files": files,
            })
    return {"scenes": scenes}


# ============================================================
# 8. POST /api/render — 渲染海报
# ============================================================
@router.post("/render")
async def render_poster(payload: dict):
    """payload: { brief: dict, session_id: str, preview?: bool }

    preview=true 时：
      - 仍按 1440 渲染（保证文字布局正确）
      - 渲染完用 PIL 缩到 720 宽，存为 thumb.jpg
      - 不输出 PDF（节省时间）
      - 返回缩略图 URL
    """
    brief = payload.get("brief")
    session_id = payload.get("session_id", "default")
    is_preview = bool(payload.get("preview", False))
    if not brief or not isinstance(brief, dict):
        raise HTTPException(400, "缺少 brief")

    # 输出文件
    job_id = uuid.uuid4().hex[:12]
    job_dir = OUTPUT_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    out_png = job_dir / "poster.png"

    # 落盘 brief 方便调试
    with open(job_dir / "brief.json", "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)

    t0 = time.time()
    try:
        result = compose_long_poster(brief, str(out_png))
        dt = time.time() - t0
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": tb}
        )

    png_path, pdf_path = result if isinstance(result, tuple) else (str(out_png), None)

    # 预览模式：缩到 720 宽 + JPG 压缩，速度更快
    if is_preview:
        try:
            from PIL import Image
            full = Image.open(out_png)
            target_w = 720
            ratio = target_w / full.width
            thumb = full.resize((target_w, int(full.height * ratio)), Image.LANCZOS)
            thumb_path = job_dir / "thumb.jpg"
            thumb.convert("RGB").save(thumb_path, "JPEG", quality=82, optimize=True)
            # 删掉大图节省空间（预览不保留 1440 原图）
            try:
                out_png.unlink()
                if pdf_path and pathlib.Path(pdf_path).exists():
                    pathlib.Path(pdf_path).unlink()
            except Exception:
                pass
            dt_total = time.time() - t0
            _cleanup_old_outputs()
            return {
                "preview": True,
                "job_id": job_id,
                "duration_sec": round(dt_total, 2),
                "png_url": f"/api/preview/{job_id}/thumb.jpg",
                "thumb_size": list(thumb.size),
            }
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"缩略图生成失败: {e}"}
            )

    _cleanup_old_outputs(keep_recent=50)
    return {
        "job_id": job_id,
        "duration_sec": round(dt, 2),
        "png_url": f"/api/preview/{job_id}/poster.png",
        "pdf_url": f"/api/preview/{job_id}/poster.pdf" if pdf_path else None,
    }


# ============================================================
# 8b. 自动清理旧 preview 产物（防磁盘膨胀）
# ============================================================
def _cleanup_old_outputs(keep_recent: int = 30):
    """保留最近 N 个 job 目录，其余删掉。"""
    try:
        dirs = sorted(OUTPUT_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        for d in dirs[keep_recent:]:
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
    except Exception:
        pass


# ============================================================
# 9. GET /api/preview/{job_id}/{filename} — 下载/预览渲染产物
# ============================================================
@router.get("/preview/{job_id}/{filename}")
def get_preview(job_id: str, filename: str):
    fp = OUTPUT_DIR / job_id / filename
    if not fp.exists():
        raise HTTPException(404, f"产物不存在: {filename}")
    return FileResponse(fp)


# ============================================================
# 10. POST /api/new-session — 创建新会话 ID
# ============================================================
@router.post("/new-session")
def new_session():
    sid = uuid.uuid4().hex[:8]
    (UPLOAD_DIR / sid).mkdir(exist_ok=True)
    return {"session_id": sid}


# ============================================================
# 11. POST /api/chat — LLM 对话端点（deepseek 主路径，ollama 兜底）
# ============================================================
import llm_tools  # noqa: E402
import llm_client  # noqa: E402

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "deepseek").lower()  # 'deepseek' | 'ollama'

# ollama 兜底配置（仅当 LLM_PROVIDER=ollama 时启用，UI 不暴露）
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:14b")


@router.get("/chat/health")
def chat_health():
    """检查当前 LLM 是否可用。"""
    if LLM_PROVIDER == "ollama":
        try:
            with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=2) as r:
                data = json.loads(r.read())
            models = [m["name"] for m in data.get("models", [])]
            ready = any(OLLAMA_MODEL in m or OLLAMA_MODEL.split(":")[0] in m for m in models)
            return {
                "provider": "ollama",
                "ollama_running": True,
                "model_ready": ready,
                "current_model": OLLAMA_MODEL,
                "available_models": models,
            }
        except Exception as e:
            return {
                "provider": "ollama",
                "ollama_running": False,
                "model_ready": False,
                "current_model": OLLAMA_MODEL,
                "error": str(e),
            }

    # 默认 deepseek
    s = llm_client.resolve_settings()
    return {
        "provider": "deepseek",
        "model_ready": bool(s["deepseek_api_key"]),
        "current_model": s["deepseek_model"],
        "base_url": s["deepseek_base_url"],
        "key_set": bool(s["deepseek_api_key"]),
    }


@router.post("/chat")
async def chat(payload: dict):
    """
    payload: {
        brief: dict,           # 当前 brief
        message: str,          # 用户消息
        history: list,         # 可选，先前的对话（[{role, content}]）
    }
    返回 { actions: [...], reply: str }
    """
    brief = payload.get("brief") or {}
    user_msg = (payload.get("message") or "").strip()
    history = payload.get("history") or []

    if not user_msg:
        raise HTTPException(400, "缺少 message")

    # 构造 messages
    messages = [{"role": "system", "content": llm_tools.SYSTEM_PROMPT}]
    for h in history[-6:]:  # 最近 3 轮
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({
        "role": "user",
        "content": llm_tools.build_user_context(brief, user_msg),
    })

    t0 = time.time()

    # ----- 走 deepseek（默认） -----
    if LLM_PROVIDER != "ollama":
        try:
            client = llm_client.LLMClient()
            result = client.chat(
                messages=messages,
                tools=llm_tools.TOOLS,
                temperature=0.2,
                timeout=120,
            )
        except llm_client.LLMError as e:
            return JSONResponse(status_code=503, content={"error": str(e)})
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"LLM 调用失败：{e}", "traceback": traceback.format_exc()},
            )
        dt = time.time() - t0
        actions = [{"name": tc["name"], "args": tc["arguments"]} for tc in result["tool_calls"]]
        text_reply = result["content"]
        if not actions and text_reply:
            actions.append({"name": "answer", "args": {"text": text_reply}})
        return {
            "actions": actions,
            "reply": text_reply,
            "duration_sec": round(dt, 2),
            "raw": result.get("raw"),
        }

    # ----- 兜底：走 ollama（环境变量启用，UI 不暴露） -----
    body = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "tools": llm_tools.TOOLS,
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }
    try:
        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/chat",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
    except urllib.error.URLError as e:
        return JSONResponse(
            status_code=503,
            content={"error": f"无法连接 Ollama 服务（{OLLAMA_HOST}）：{e}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"LLM 调用失败：{e}", "traceback": traceback.format_exc()}
        )
    dt = time.time() - t0
    msg = data.get("message", {})
    tool_calls = msg.get("tool_calls", []) or []
    text_reply = (msg.get("content") or "").strip()
    actions = []
    for tc in tool_calls:
        fn = tc.get("function", {})
        name = fn.get("name")
        args = fn.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        if name:
            actions.append({"name": name, "args": args or {}})
    if not actions and text_reply:
        actions.append({"name": "answer", "args": {"text": text_reply}})
    return {
        "actions": actions,
        "reply": text_reply,
        "duration_sec": round(dt, 2),
        "raw": data,
    }
