"""
Stage 1: 调用 Nano Banana / Image2 生成主视觉底图。
仅负责"画底图"，不处理任何文字、Logo。
"""
from __future__ import annotations
import os, sys, json, time, argparse, pathlib
from datetime import datetime

# 注意：实际 SDK 以厂商最新版本为准。此处用 requests 通用接口示意。
import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
REF = ROOT / "references"


def load_scene_prompt(scene_id: str) -> dict:
    """从 references/scene-prompts.md 中提取指定场景的 base prompt 与 negative。"""
    text = (REF / "scene-prompts.md").read_text(encoding="utf-8")
    # 简化：实际可以更严谨地按 markdown 段落解析
    blocks = text.split("\n## ")
    for b in blocks:
        if b.startswith(f"{scene_id} ") or b.startswith(f"{scene_id}\n") or b.startswith(f"{scene_id} ·"):
            base = _between(b, "**Base Prompt", "**Negative")
            negative = _between(b, "**Negative", "**色板锁定")
            return {
                "base_prompt": _strip_code(base),
                "negative_prompt": _strip_code(negative),
            }
    raise ValueError(f"Scene {scene_id} not found in scene-prompts.md")


def _between(s: str, a: str, b: str) -> str:
    i = s.find(a); j = s.find(b)
    return s[i:j] if i >= 0 and j > i else ""


def _strip_code(s: str) -> str:
    """提取 markdown 代码块内的纯 prompt 文本。"""
    if "```" in s:
        return s.split("```")[1].strip()
    # 退路：取冒号后整段
    return s.split("：", 1)[-1].strip().strip("`")


def build_prompt(scene_id: str, brief: dict) -> tuple[str, str]:
    sp = load_scene_prompt(scene_id)
    base = sp["base_prompt"]
    base = base.replace("{topic}", brief.get("title", "training event"))
    base = base.replace("{vibe_extras}", brief.get("extras", ""))

    common_tail = (
        "\n--composition_constraints\n"
        "Top 35% MUST remain visually quiet for title overlay. "
        "Bottom 25% low-saturation gradient for info overlay. "
        "NO text rendering anywhere.\n"
        "--quality\n"
        "8k, ultra detail, sharp focus, professional poster grade."
    )
    return base + common_tail, sp["negative_prompt"]


def call_api(prompt: str, negative: str, width: int, height: int,
             steps: int, guidance: float, n: int) -> list[bytes]:
    provider = os.getenv("IMAGE_PROVIDER", "nano_banana")
    if provider == "nano_banana":
        url = os.environ["NANO_BANANA_BASE_URL"].rstrip("/") + "/images/generations"
        headers = {"Authorization": f"Bearer {os.environ['NANO_BANANA_API_KEY']}"}
    else:
        url = os.environ["IMAGE2_BASE_URL"].rstrip("/") + "/generate"
        headers = {"Authorization": f"Bearer {os.environ['IMAGE2_API_KEY']}"}

    payload = {
        "prompt": prompt,
        "negative_prompt": negative,
        "width": width,
        "height": height,
        "steps": steps,
        "guidance_scale": guidance,
        "n": n,
        "response_format": "b64_json",
    }

    for attempt in range(3):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=120)
            if r.status_code == 429:
                time.sleep(2 ** attempt); continue
            r.raise_for_status()
            data = r.json()
            import base64
            return [base64.b64decode(item["b64_json"]) for item in data["data"]]
        except requests.RequestException as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True, help="path to brief.json")
    parser.add_argument("--out", default="output/")
    parser.add_argument("--n", type=int, default=4)
    args = parser.parse_args()

    brief = json.loads(pathlib.Path(args.brief).read_text(encoding="utf-8"))
    scene = brief["scene"]

    # 尺寸映射
    size_map = {
        "A3": (1024, 1536),
        "A4": (1024, 1448),
        "公众号头图": (1280, 720),
        "朋友圈": (1080, 1080),
    }
    w, h = size_map.get(brief.get("size", "A3"), (1024, 1536))

    params_map = {
        "S1": (7.0, 35), "S4": (7.0, 35),
        "S2": (8.0, 45), "S5": (8.0, 45),
        "S3": (7.5, 40), "S6": (7.5, 40),
    }
    g, s = params_map.get(scene, (7.5, 40))

    prompt, negative = build_prompt(scene, brief)
    images = call_api(prompt, negative, w, h, s, g, args.n)

    out_dir = pathlib.Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = []
    for i, img_bytes in enumerate(images):
        p = out_dir / f"{ts}_bg_{i+1}.png"
        p.write_bytes(img_bytes)
        paths.append(str(p))

    meta = {"timestamp": ts, "scene": scene, "brief": brief,
            "prompt": prompt, "negative": negative,
            "params": {"width": w, "height": h, "steps": s, "guidance_scale": g, "n": args.n},
            "outputs": paths}
    (out_dir / f"{ts}_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"timestamp": ts, "candidates": paths}, ensure_ascii=False))


if __name__ == "__main__":
    main()
