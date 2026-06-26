"""
Prompt 拼装器 + 统一图像生成接口。

职责：
1. 从 references/scene-prompts.md 解析出指定场景的 base / negative
2. 注入 brief 字段，拼装最终 prompt
3. 统一封装 Nano Banana / Image2 两个 provider
"""
from __future__ import annotations
import os, re, time, base64, pathlib
from typing import List, Tuple
import requests

REF_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "references"


# --- Prompt 解析 ----------------------------------------------------------
def parse_scene_prompts(scene_id: str) -> dict:
    text = (REF_DIR / "scene-prompts.md").read_text(encoding="utf-8")
    # 用 ## 切块
    blocks = re.split(r"\n##\s+", "\n" + text)
    for b in blocks:
        head = b.splitlines()[0] if b else ""
        if head.startswith(f"{scene_id} ") or head.startswith(f"{scene_id}\n") or head.startswith(f"{scene_id}·"):
            return {
                "base_prompt": _extract_code_block(b, "Base Prompt"),
                "negative_prompt": _extract_after(b, "**Negative：**"),
            }
    raise ValueError(f"Scene {scene_id} not found in scene-prompts.md")


def _extract_code_block(block: str, anchor: str) -> str:
    idx = block.find(anchor)
    if idx < 0:
        return ""
    rest = block[idx:]
    fence_start = rest.find("```")
    if fence_start < 0:
        return ""
    fence_end = rest.find("```", fence_start + 3)
    return rest[fence_start + 3:fence_end].strip()


def _extract_after(block: str, anchor: str) -> str:
    idx = block.find(anchor)
    if idx < 0:
        return ""
    line = block[idx + len(anchor):].split("\n", 1)[0]
    return line.strip().strip("`").strip()


COMMON_TAIL = (
    "\n--composition_constraints\n"
    "Top 35% MUST remain visually quiet for title overlay. "
    "Bottom 25% low-saturation gradient for info overlay. "
    "NO text rendering anywhere.\n"
    "--quality\n"
    "8k, ultra detail, sharp focus, professional poster grade."
)


def build_prompt(scene_id: str, brief: dict) -> Tuple[str, str]:
    sp = parse_scene_prompts(scene_id)
    base = sp["base_prompt"]
    base = base.replace("{topic}", brief.get("title", "training event"))
    base = base.replace("{vibe_extras}", brief.get("extras", ""))
    return base + COMMON_TAIL, sp["negative_prompt"]


# --- Provider 封装 --------------------------------------------------------
def generate_image(prompt: str, negative_prompt: str, *,
                   width: int = 1024, height: int = 1536,
                   steps: int = 40, guidance_scale: float = 7.5,
                   seed: int | None = None, n: int = 4,
                   out_dir: str = "output/") -> List[str]:
    """统一图像生成入口，返回保存到本地的文件路径列表。"""
    provider = os.getenv("IMAGE_PROVIDER", "nano_banana")
    if provider == "nano_banana":
        url = os.environ["NANO_BANANA_BASE_URL"].rstrip("/") + "/images/generations"
        headers = {"Authorization": f"Bearer {os.environ['NANO_BANANA_API_KEY']}"}
    else:
        url = os.environ["IMAGE2_BASE_URL"].rstrip("/") + "/generate"
        headers = {"Authorization": f"Bearer {os.environ['IMAGE2_API_KEY']}"}

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width, "height": height,
        "steps": steps, "guidance_scale": guidance_scale,
        "n": n, "response_format": "b64_json",
    }
    if seed is not None:
        payload["seed"] = seed

    last_err: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=120)
            if r.status_code == 429:
                time.sleep(2 ** attempt); continue
            r.raise_for_status()
            data = r.json()
            out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
            paths = []
            ts = time.strftime("%Y%m%d_%H%M%S")
            for i, item in enumerate(data["data"]):
                p = out / f"{ts}_bg_{i+1}.png"
                p.write_bytes(base64.b64decode(item["b64_json"]))
                paths.append(str(p))
            return paths
        except requests.RequestException as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"image generation failed: {last_err}")
