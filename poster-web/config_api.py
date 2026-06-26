"""配置 API：读写 ~/.poster-web/config.json（deepseek key 等）。"""
from fastapi import APIRouter, HTTPException
import json
import tempfile
import pathlib
import urllib.error
import urllib.request

import llm_client
import image_client


router = APIRouter(prefix="/api")


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:3] + "*" * (len(key) - 7) + key[-4:]


@router.get("/config")
def get_config():
    """返回当前配置。API key 做掩码处理，只露末 4 位。"""
    s = llm_client.resolve_settings()
    raw_cfg = llm_client.load_config()
    return {
        "llm_provider": s["llm_provider"],
        "llm_api_key_masked": _mask_key(s["llm_api_key"]),
        "llm_api_key_set": bool(s["llm_api_key"]),
        "llm_base_url": s["llm_base_url"],
        "llm_model": s["llm_model"],
        "image_provider": s["image_provider"],
        "image_api_key_masked": _mask_key(s["image_api_key"]),
        "image_api_key_set": bool(s["image_api_key"]),
        "image_base_url": s["image_base_url"],
        "image_model": s["image_model"],
        "kb_provider": s["kb_provider"],
        "llm_presets": llm_client.LLM_PROVIDER_DEFAULTS,
        "image_presets": llm_client.IMAGE_PROVIDER_DEFAULTS,
        # backward-compatible aliases for old frontend checks
        "deepseek_api_key_masked": _mask_key(s["llm_api_key"]),
        "deepseek_api_key_set": bool(s["llm_api_key"]),
        "deepseek_base_url": s["llm_base_url"],
        "deepseek_model": s["llm_model"],
        # 是否被环境变量覆盖（前端提示用）
        "key_from_env": bool(__import__("os").environ.get("LLM_API_KEY") or __import__("os").environ.get("DEEPSEEK_API_KEY")),
        "image_key_from_env": bool(__import__("os").environ.get("IMAGE_API_KEY")),
        "config_path": str(llm_client.CONFIG_PATH),
        "raw_has_key": bool(raw_cfg.get("llm_api_key") or raw_cfg.get("deepseek_api_key")),
    }


@router.put("/config")
def update_config(payload: dict):
    """更新配置。允许字段：deepseek_api_key（明文，留空 = 不修改；'__clear__' = 清空）、
    deepseek_base_url、deepseek_model、kb_provider。"""
    cfg = llm_client.load_config()

    # LLM API key：空字符串 = 不变；__clear__ = 清空；其它 = 写入
    if "llm_api_key" in payload or "deepseek_api_key" in payload:
        new_key = payload.get("llm_api_key", payload.get("deepseek_api_key"))
        if new_key == "__clear__":
            cfg.pop("llm_api_key", None)
            cfg.pop("deepseek_api_key", None)
        elif new_key:
            cfg["llm_api_key"] = new_key
            cfg["deepseek_api_key"] = new_key

    # Image API key：空字符串 = 不变；__clear__ = 清空；其它 = 写入
    if "image_api_key" in payload:
        new_key = payload["image_api_key"]
        if new_key == "__clear__":
            cfg.pop("image_api_key", None)
        elif new_key:
            cfg["image_api_key"] = new_key

    for k in ("llm_provider", "llm_base_url", "llm_model", "image_provider", "image_base_url", "image_model", "kb_provider"):
        if k in payload and payload[k] is not None:
            cfg[k] = (payload[k] or "").strip() or cfg.get(k, "")

    # 兼容旧字段写入
    if "deepseek_base_url" in payload and payload["deepseek_base_url"] is not None:
        cfg["llm_base_url"] = (payload["deepseek_base_url"] or "").strip() or cfg.get("llm_base_url", "")
    if "deepseek_model" in payload and payload["deepseek_model"] is not None:
        cfg["llm_model"] = (payload["deepseek_model"] or "").strip() or cfg.get("llm_model", "")

    llm_client.save_config(cfg)
    return get_config()


@router.post("/config/test")
def test_config(payload: dict = None):
    """用当前配置（或 payload 覆盖）发一个 ping，返回连通性。"""
    payload = payload or {}
    try:
        client = llm_client.LLMClient(
            api_key=payload.get("llm_api_key") or payload.get("deepseek_api_key") or None,
            base_url=payload.get("llm_base_url") or payload.get("deepseek_base_url") or None,
            model=payload.get("llm_model") or payload.get("deepseek_model") or None,
        )
        if not client.is_configured:
            return {"ok": False, "error": "缺少 API key 或 base_url"}
        result = client.chat(
            messages=[
                {"role": "system", "content": "你是一个测试助手，回复必须简短。"},
                {"role": "user", "content": "请用一个字回答：通"},
            ],
            temperature=0.0,
            timeout=20,
        )
        reply = result.get("content") or ""
        return {"ok": True, "provider": getattr(client, "provider", "custom"), "model": client.model, "base_url": client.base_url, "reply": reply[:200]}
    except llm_client.LLMError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        raise HTTPException(500, f"测试失败：{e}")


@router.post("/config/image-test")
def test_image_config(payload: dict = None):
    """真实生图接口测试：按当前 Provider 调用真实生图 API。"""
    payload = payload or {}
    settings = llm_client.resolve_settings()
    provider = (payload.get("image_provider") or settings["image_provider"] or "").strip()
    base_url = (payload.get("image_base_url") or settings["image_base_url"] or "").strip().rstrip("/")
    model = (payload.get("image_model") or settings["image_model"] or "").strip()
    api_key = payload.get("image_api_key") or settings["image_api_key"]

    if provider == "hunyuan" and not base_url:
        base_url = "https://aiart.tencentcloudapi.com"
        model = model or "TextToImageLite"
    if not provider or not model:
        return {"ok": False, "provider": provider, "model": model, "base_url": base_url, "error": "缺少生图 Provider 或模型名"}
    if not base_url:
        return {"ok": False, "provider": provider, "model": model, "base_url": base_url, "error": "缺少生图 Base URL"}
    if provider != "comfyui" and not api_key:
        return {"ok": False, "provider": provider, "model": model, "base_url": base_url, "error": "缺少生图 API Key"}

    tmp_path = None
    try:
        client = image_client.ImageClient(api_key=api_key, base_url=base_url, model=model)
        client.provider = provider
        with tempfile.NamedTemporaryFile(prefix="poster_image_test_", suffix=".png", delete=False) as f:
            tmp_path = pathlib.Path(f.name)
        result = client.generate(
            "A clean blue and cyan abstract gradient background, no text, no logo, high quality.",
            tmp_path,
            1024,
            1024,
            purpose="config_test",
        )
        return {
            "ok": True,
            "provider": provider,
            "model": model,
            "base_url": base_url,
            "reply": f"真实生图成功：{result.width}x{result.height}",
            "note": "已真实调用生图接口并成功读取返回图片。",
        }
    except image_client.ImageGenerationError as e:
        return {"ok": False, "provider": provider, "model": model, "base_url": base_url, "error": str(e)}
    except Exception as e:
        return {"ok": False, "provider": provider, "model": model, "base_url": base_url, "error": f"真实生图测试失败：{e}"}
    finally:
        if tmp_path:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
