"""LLM 客户端：OpenAI 兼容协议，主用 deepseek。

规范：
- chat(): 非流式，返回归一化结构 {content, tool_calls: [{name, arguments(dict)}]}
- chat_stream(): SSE 流，yield {type: 'token'|'tool_call'|'done'|'error', data: ...}

配置来源（优先级从高到低）：
1. 环境变量 DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL（适合命令行调试）
2. ~/.poster-web/config.json（前端设置抽屉写入）
3. 内置默认值（base_url=https://api.deepseek.com/v1, model=deepseek-chat）
"""
import json
import os
import pathlib
import urllib.request
import urllib.error
from typing import Iterator, Optional


CONFIG_DIR = pathlib.Path.home() / ".poster-web"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"

LLM_PROVIDER_DEFAULTS = {
    "deepseek": {"label": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "openai": {"label": "OpenAI", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "siliconflow": {"label": "SiliconFlow", "base_url": "https://api.siliconflow.cn/v1", "model": "deepseek-ai/DeepSeek-V3"},
    "dashscope": {"label": "通义千问 / DashScope", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "moonshot": {"label": "月之暗面 Kimi", "base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "zhipu": {"label": "智谱 GLM", "base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    "volcengine": {"label": "火山方舟", "base_url": "https://ark.cn-beijing.volces.com/api/v3", "model": "doubao-1-5-pro-32k"},
    "hunyuan": {"label": "腾讯混元", "base_url": "https://api.hunyuan.cloud.tencent.com/v1", "model": "hunyuan-turbo"},
    "custom": {"label": "自定义 OpenAI 兼容", "base_url": "", "model": ""},
}

IMAGE_PROVIDER_DEFAULTS = {
    "openai": {"label": "OpenAI Images", "base_url": "https://api.openai.com/v1", "model": "gpt-image-1"},
    "hunyuan": {"label": "腾讯混元生图", "base_url": "https://aiart.tencentcloudapi.com", "model": "TextToImageLite"},
    "volcengine": {"label": "火山方舟 / 即梦", "base_url": "", "model": "doubao-seedream"},
    "dashscope": {"label": "通义万相", "base_url": "", "model": "wanx2.1-t2i-turbo"},
    "siliconflow": {"label": "SiliconFlow Images", "base_url": "https://api.siliconflow.cn/v1", "model": "Kwai-Kolors/Kolors"},
    "stability": {"label": "Stability AI", "base_url": "https://api.stability.ai", "model": "stable-image-core"},
    "comfyui": {"label": "本地 ComfyUI", "base_url": "http://127.0.0.1:8188", "model": "workflow"},
    "custom": {"label": "自定义生图接口", "base_url": "", "model": ""},
}


class LLMError(Exception):
    pass


def load_config() -> dict:
    """加载配置文件（容错，不存在或损坏返回空 dict）。"""
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(data: dict) -> dict:
    """保存配置，文件权限 0600。"""
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except Exception:
        pass
    return data


def resolve_settings() -> dict:
    """合并环境变量 + 配置文件 + 默认值，返回当前生效的模型配置。

    兼容旧字段 deepseek_*：老调用方继续读这些字段，也会指向当前 LLM 配置。
    """
    cfg = load_config()
    llm_provider = (os.environ.get("LLM_PROVIDER") or cfg.get("llm_provider") or cfg.get("deepseek_provider") or "deepseek").strip()
    llm_defaults = LLM_PROVIDER_DEFAULTS.get(llm_provider, LLM_PROVIDER_DEFAULTS["custom"])
    llm_api_key = (
        os.environ.get("LLM_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
        or cfg.get("llm_api_key")
        or cfg.get("deepseek_api_key")
        or ""
    )
    llm_base_url = (
        os.environ.get("LLM_BASE_URL")
        or os.environ.get("DEEPSEEK_BASE_URL")
        or cfg.get("llm_base_url")
        or cfg.get("deepseek_base_url")
        or llm_defaults.get("base_url")
        or DEFAULT_BASE_URL
    )
    llm_model = (
        os.environ.get("LLM_MODEL")
        or os.environ.get("DEEPSEEK_MODEL")
        or cfg.get("llm_model")
        or cfg.get("deepseek_model")
        or llm_defaults.get("model")
        or DEFAULT_MODEL
    )

    image_provider = (os.environ.get("IMAGE_PROVIDER") or cfg.get("image_provider") or "openai").strip()
    image_defaults = IMAGE_PROVIDER_DEFAULTS.get(image_provider, IMAGE_PROVIDER_DEFAULTS["custom"])
    image_api_key = os.environ.get("IMAGE_API_KEY") or cfg.get("image_api_key") or ""
    image_base_url = os.environ.get("IMAGE_BASE_URL") or cfg.get("image_base_url") or image_defaults.get("base_url") or ""
    image_model = os.environ.get("IMAGE_MODEL") or cfg.get("image_model") or image_defaults.get("model") or ""

    return {
        "llm_provider": llm_provider,
        "llm_api_key": llm_api_key,
        "llm_base_url": llm_base_url,
        "llm_model": llm_model,
        "image_provider": image_provider,
        "image_api_key": image_api_key,
        "image_base_url": image_base_url,
        "image_model": image_model,
        "kb_provider": cfg.get("kb_provider") or "noop",
        # backward-compatible aliases
        "deepseek_api_key": llm_api_key,
        "deepseek_base_url": llm_base_url,
        "deepseek_model": llm_model,
    }


# ============================================================
# OpenAI 兼容 HTTP 客户端
# ============================================================
class LLMClient:
    """OpenAI Chat Completions 兼容客户端（deepseek 主用）。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        s = resolve_settings()
        self.api_key = api_key if api_key is not None else s["llm_api_key"]
        self.base_url = (base_url or s["llm_base_url"]).rstrip("/")
        self.model = model or s["llm_model"]
        self.provider = s.get("llm_provider", "custom")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) and bool(self.base_url) and bool(self.model)

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    # ------------ 非流式 ------------
    def chat(
        self,
        messages: list,
        tools: Optional[list] = None,
        temperature: float = 0.2,
        timeout: int = 120,
    ) -> dict:
        """返回归一化 dict：{content, tool_calls:[{name,arguments(dict)}], raw}"""
        if not self.is_configured:
            raise LLMError("LLM 未配置：请在前端设置抽屉填入当前模型的 API Key")

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if tools:
            body["tools"] = tools

        url = f"{self.base_url}/chat/completions"
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=self._headers(),
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            raise LLMError(f"HTTP {e.code} {e.reason}: {err_body}") from e
        except urllib.error.URLError as e:
            raise LLMError(f"无法连接 {self.base_url}：{e}") from e

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        content = (msg.get("content") or "").strip()
        tcs = msg.get("tool_calls") or []
        norm_calls = []
        for tc in tcs:
            fn = tc.get("function") or {}
            name = fn.get("name")
            args = fn.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            if name:
                norm_calls.append({"name": name, "arguments": args or {}})
        return {"content": content, "tool_calls": norm_calls, "raw": data}

    # ------------ 流式 ------------
    def chat_stream(
        self,
        messages: list,
        tools: Optional[list] = None,
        temperature: float = 0.7,
        timeout: int = 300,
    ) -> Iterator[dict]:
        """SSE 流式输出。yield 事件：
        - {"type": "token", "data": "..."}              逐字 token
        - {"type": "tool_call", "data": {name, arguments(dict)}}  完整工具调用
        - {"type": "done"}                              流结束
        """
        if not self.is_configured:
            yield {"type": "error", "data": "LLM 未配置：请在前端设置抽屉填入当前模型的 API Key"}
            return

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            body["tools"] = tools

        url = f"{self.base_url}/chat/completions"
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=self._headers(),
        )

        # 累积 tool_call 分片（OpenAI 流式协议会把 arguments 切成多块 delta）
        tool_acc: dict = {}  # idx -> {id, name, arguments_str}

        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                for raw in r:
                    line = raw.decode("utf-8", errors="replace").rstrip("\n").rstrip("\r")
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if not payload:
                        continue
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except Exception:
                        continue
                    choice = (chunk.get("choices") or [{}])[0]
                    delta = choice.get("delta") or {}
                    # 文本 token
                    txt = delta.get("content")
                    if txt:
                        yield {"type": "token", "data": txt}
                    # tool_call 分片
                    for tc in delta.get("tool_calls") or []:
                        idx = tc.get("index", 0)
                        slot = tool_acc.setdefault(idx, {"id": "", "name": "", "args_str": ""})
                        if tc.get("id"):
                            slot["id"] = tc["id"]
                        fn = tc.get("function") or {}
                        if fn.get("name"):
                            slot["name"] = fn["name"]
                        if fn.get("arguments") is not None:
                            slot["args_str"] += fn["arguments"]
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            yield {"type": "error", "data": f"HTTP {e.code}: {err_body}"}
            return
        except urllib.error.URLError as e:
            yield {"type": "error", "data": f"无法连接 {self.base_url}：{e}"}
            return

        # 流结束后，把累积的 tool_calls 全部吐出
        for slot in tool_acc.values():
            if not slot.get("name"):
                continue
            args = {}
            if slot.get("args_str"):
                try:
                    args = json.loads(slot["args_str"])
                except Exception:
                    args = {}
            yield {"type": "tool_call", "data": {"name": slot["name"], "arguments": args}}
        yield {"type": "done"}
