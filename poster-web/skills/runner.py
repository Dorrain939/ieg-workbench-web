"""SSE 流封装：调 skill.run() 流式回前端 + 落盘 artifact + 更新 project.json。

使用：
    POST /api/projects/{pid}/skills/{skill}
    body: {params: {...}}
    返回：text/event-stream 流，事件 data: {"type":"...","data":...}\\n\\n
"""
import json
import importlib
import datetime
import pathlib
import uuid
from typing import Iterator, Dict, Optional


def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _sse(payload: dict) -> bytes:
    """格式化为 SSE 行。"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")


def _gen_artifact_id() -> str:
    return f"art_{uuid.uuid4().hex[:10]}"


def _gen_ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def stream_skill(
    pid: str,
    skill: str,
    params: dict,
    project: dict,
    project_dir: pathlib.Path,
    llm,
    kb_module,
) -> Iterator[bytes]:
    """统一流：包 skill.run() + 落盘 artifact + 更新 project.json + SSE 输出。

    参数：
        pid: 项目 ID
        skill: skill 名称
        params: 表单参数
        project: 项目 JSON
        project_dir: 项目目录路径
        llm: LLMClient 实例
        kb_module: kb.index 模块（提供 search 函数）
    """
    # ---- 1. 校验 skill ----
    try:
        skill_mod = importlib.import_module(f"skills.{skill}")
    except ImportError as e:
        yield _sse({"type": "error", "data": f"skill 不存在: {skill}（{e}）"})
        return

    if not hasattr(skill_mod, "run"):
        yield _sse({"type": "error", "data": f"skill {skill} 缺少 run() 函数"})
        return

    yield _sse({"type": "started", "skill": skill, "ts": _now_iso()})

    # ---- 2. 调 skill ----
    full_text = ""
    output_json: Optional[dict] = None
    error_msg: Optional[str] = None
    extra_files: Dict[str, bytes] = {}  # 额外要落盘的文件 {filename: bytes}

    try:
        for ev in skill_mod.run(project, params, kb_module, llm):
            t = ev.get("type")
            if t == "token":
                full_text += ev.get("data", "")
                yield _sse(ev)
            elif t == "json":
                output_json = ev.get("data")
                yield _sse(ev)
            elif t == "file":
                # skill 主动要求落额外文件（如 PNG / brief.json）
                fname = ev.get("filename")
                content = ev.get("content")
                if fname and content is not None:
                    extra_files[fname] = content
                    # 不流回前端原始内容（可能是二进制）
                    yield _sse({"type": "progress", "data": f"已生成 {fname}"})
            elif t == "error":
                error_msg = ev.get("data", "未知错误")
                yield _sse(ev)
                break
            else:
                # progress / ask 等其他事件原样转发
                yield _sse(ev)
    except Exception as e:
        import traceback
        error_msg = f"skill 执行异常：{e}"
        yield _sse({"type": "error", "data": error_msg, "traceback": traceback.format_exc()[:2000]})

    if error_msg:
        return

    # ---- 3. 落盘 artifact ----
    aid = _gen_artifact_id()
    ts = _gen_ts()
    art_dir = project_dir / "artifacts" / skill / ts
    art_dir.mkdir(parents=True, exist_ok=True)

    files_written = []
    # 注意：如果 skill 通过 file 事件提供了 output.md（清洗后），优先用它
    if "output.md" not in extra_files and full_text.strip():
        (art_dir / "output.md").write_text(full_text, encoding="utf-8")
        files_written.append("output.md")
    if output_json is not None:
        (art_dir / "output.json").write_text(
            json.dumps(output_json, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        files_written.append("output.json")
    for fname, content in extra_files.items():
        target = art_dir / fname
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(str(content), encoding="utf-8")
        if fname not in files_written:
            files_written.append(fname)
    # 落盘参数（方便调试 + 复现）
    (art_dir / "params.json").write_text(
        json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    existing = project.get("artifacts") or []
    version_scope = {"poster_brief", "poster_copy_import"} if skill in {"poster_brief", "poster_copy_import"} else {skill}
    version_no = sum(1 for a in existing if a.get("skill") in version_scope) + 1
    version = f"v{version_no}"

    # ---- 4. 生成标题 ----
    title = _make_title(skill, params, full_text, output_json)
    if skill in {"poster_brief", "poster_copy_import"}:
        title = f"{title} · {version}"

    artifact = {
        "id": aid,
        "skill": skill,
        "title": title,
        "version": version,
        "path": f"artifacts/{skill}/{ts}/",
        "files": files_written,
        "created_at": _now_iso(),
        "params": params,
    }

    # ---- 5. 更新 project.json ----
    proj_fp = project_dir / "project.json"
    try:
        data = json.loads(proj_fp.read_text(encoding="utf-8"))
        data.setdefault("artifacts", []).insert(0, artifact)  # 最新放最前
        data["updated_at"] = _now_iso()
        # 原子写
        tmp = proj_fp.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(proj_fp)
    except Exception as e:
        yield _sse({"type": "error", "data": f"更新 project.json 失败: {e}"})
        return

    yield _sse({"type": "artifact", "data": artifact})
    yield _sse({"type": "done"})


def _make_title(skill: str, params: dict, text: str, json_out: Optional[dict]) -> str:
    """根据 skill 类型生成产物标题。"""
    if skill == "interview_outline":
        role = (params.get("role") or "受访者").strip()
        return f"{role} 访谈提纲"
    if skill == "copywriter":
        scene_map = {"S1": "招生宣传", "S2": "开营通知", "S3": "课程预告", "S4": "结业总结"}
        return f"{scene_map.get(params.get('scene'), '海报')}文案"
    if skill == "poster_brief":
        theme = (params.get("theme") or "海报").strip()[:20]
        return f"{theme} · brief"
    if skill == "poster_copy_import":
        return "上传文案识别成图"
    if skill == "ppt_outline":
        theme = (params.get("theme") or "PPT").strip()[:20]
        return f"{theme} · 大纲"
    return f"{skill} 产物"


def build_kb_context(project: dict, query: str, kb_module, top_k: int = 5) -> str:
    """通用 RAG 检索：只读当前项目知识库，避免平台/功能知识库串用。"""
    pid = project.get("id")
    docs = []
    if pid:
        docs = kb_module.search(
            query,
            scope="project",
            project_id=pid,
            top_k=top_k,
            include_global_when_project=False,
        )
    if not docs:
        return ""
    return "\n\n".join(
        f"【{d.get('filename', '?')}】\n{d.get('text', '').strip()}"
        for d in docs
    )


def build_function_kb_context(
    project: dict,
    query: str,
    kb_module,
    function_id: str,
    kb_type: str,
    top_k: int = 5,
) -> str:
    """功能级 RAG 检索：只读当前项目下指定功能/类型知识库。"""
    pid = project.get("id")
    if not pid or not function_id or not kb_type:
        return ""
    docs = kb_module.search(
        query,
        scope="function",
        project_id=pid,
        function_id=function_id,
        kb_type=kb_type,
        top_k=top_k,
    )
    if not docs:
        return ""
    return "\n\n".join(
        f"【{d.get('filename', '?')}】\n{d.get('text', '').strip()}"
        for d in docs
    )


def load_prompt(name: str) -> str:
    """读 prompts/<name>.txt。"""
    fp = pathlib.Path(__file__).resolve().parent.parent / "prompts" / f"{name}.txt"
    if not fp.exists():
        return ""
    return fp.read_text(encoding="utf-8")
