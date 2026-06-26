"""Image generation client for poster visual assets.

The platform stores image-model settings in the same config drawer as LLMs.
This client intentionally speaks an OpenAI-compatible images endpoint first,
which covers most hosted image gateways and custom proxy services.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import pathlib
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from llm_client import resolve_settings


class ImageGenerationError(Exception):
    pass


@dataclass
class GeneratedImage:
    path: pathlib.Path
    width: int
    height: int


def normalize_bearer_api_key(raw: str) -> str:
    """Accept common pasted API key forms and return the bearer token only."""
    value = str(raw or "").strip()
    if not value:
        return ""
    # Most OpenAI-compatible gateways use sk-...; extract it even if the user
    # pasted Chinese labels, markdown, JSON, env lines, or surrounding text.
    m = re.search(r"sk-[A-Za-z0-9_\-]+", value)
    if m:
        return m.group(0)
    if value.startswith("{"):
        try:
            data = json.loads(value)
            value = str(
                data.get("api_key")
                or data.get("apikey")
                or data.get("key")
                or data.get("token")
                or data.get("access_token")
                or data.get("Authorization")
                or data.get("authorization")
                or value
            ).strip()
        except Exception:
            pass
    value = value.strip().strip('"').strip("'").strip()
    prefixes = [
        "Authorization: Bearer ", "authorization: bearer ", "Bearer ", "bearer ",
        "OPENAI_API_KEY=", "IMAGE_API_KEY=", "API_KEY=", "api_key=", "key=", "token=",
        "API Key:", "api key:", "Key:", "key:", "Token:", "token:",
        "API Key：", "api key：", "Key：", "key：", "Token：", "token：",
    ]
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if value.startswith(prefix):
                value = value[len(prefix):].strip().strip('"').strip("'").strip()
                changed = True
    if "\n" in value:
        value = next((line.strip() for line in value.splitlines() if line.strip()), value)
    if value.lower().startswith("bearer "):
        value = value[7:].strip()
    try:
        value.encode("latin-1")
    except UnicodeEncodeError:
        # Header values cannot contain CJK/full-width text. If there is no token
        # pattern to extract, return empty so the real request fails as missing auth
        # instead of crashing in urllib before it reaches the endpoint.
        return ""
    return value


class ImageClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        s = resolve_settings()
        self.provider = s.get("image_provider") or "custom"
        raw_key = api_key if api_key is not None else s.get("image_api_key", "")
        self.api_key = raw_key if self.provider == "hunyuan" else normalize_bearer_api_key(raw_key)
        self.base_url = (base_url if base_url is not None else s.get("image_base_url", "")).rstrip("/")
        self.model = model if model is not None else s.get("image_model", "")

    @property
    def is_configured(self) -> bool:
        if self.provider == "comfyui":
            return bool(self.base_url)
        return bool(self.api_key) and bool(self.base_url) and bool(self.model)

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        key = normalize_bearer_api_key(self.api_key)
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def generate(self, prompt: str, out_path: pathlib.Path, width: int, height: int, *, purpose: str = "poster") -> GeneratedImage:
        """Generate one image and save it to out_path.

        Providers are expected to expose POST /images/generations with an
        OpenAI-compatible response: data[0].b64_json or data[0].url.
        """
        if not self.is_configured:
            raise ImageGenerationError("生图模型未配置：请在右侧设置里配置生图 Provider / Base URL / Model / API Key，并测试连通")
        if self.provider == "comfyui":
            raise ImageGenerationError("本地 ComfyUI 已作为配置项预留，但自动工作流执行器尚未接入；请先使用 OpenAI 兼容生图接口")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # 腾讯云官方 aiart endpoint 走 TC3 签名；其它 Base URL 一律按用户填写的
        # OpenAI-compatible /images/generations 真实尝试，不做主观拦截。
        if self.provider == "hunyuan" and "aiart.tencentcloudapi.com" in self.base_url:
            return self._generate_hunyuan_lite(prompt, out_path, width, height, purpose=purpose)

        body = {
            "model": self.model,
            "prompt": prompt,
            "size": f"{width}x{height}",
            "n": 1,
            "response_format": "b64_json",
        }
        def _candidate_generation_urls() -> list[str]:
            base = self.base_url.rstrip("/")
            urls = [f"{base}/images/generations"]
            if not base.endswith("/v1"):
                urls.append(f"{base}/v1/images/generations")
            return urls

        last_error = None
        payload = None
        for url in _candidate_generation_urls():
            def _post(payload_body: dict) -> dict:
                req = urllib.request.Request(url, data=json.dumps(payload_body).encode("utf-8"), headers=self._headers())
                with urllib.request.urlopen(req, timeout=240) as r:
                    return json.loads(r.read().decode("utf-8"))
            try:
                payload = _post(body)
                break
            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8", errors="replace")[:800]
                except Exception:
                    pass
                # Some OpenAI-compatible image gateways always return b64_json and reject response_format.
                if e.code in (400, 422) and "response_format" in detail:
                    retry_body = dict(body)
                    retry_body.pop("response_format", None)
                    try:
                        payload = _post(retry_body)
                        break
                    except urllib.error.HTTPError as e2:
                        detail2 = ""
                        try:
                            detail2 = e2.read().decode("utf-8", errors="replace")[:800]
                        except Exception:
                            pass
                        last_error = ImageGenerationError(f"生图接口 HTTP {e2.code}：{detail2 or e2.reason}")
                else:
                    last_error = ImageGenerationError(f"生图接口 HTTP {e.code}：{detail or e.reason}")
                # Try /v1 fallback on 404, otherwise the endpoint did answer and that is the real result.
                if e.code != 404:
                    break
            except Exception as e:
                last_error = ImageGenerationError(f"生图接口调用失败：{e}")
                break
        if payload is None:
            raise last_error or ImageGenerationError("生图接口未返回结果")

        data = (payload.get("data") or [{}])[0]
        if data.get("b64_json"):
            raw = base64.b64decode(data["b64_json"])
            out_path.write_bytes(raw)
        elif data.get("url"):
            self._download(data["url"], out_path)
        else:
            raise ImageGenerationError("生图接口未返回 data[0].b64_json 或 data[0].url")

        self._normalize_size(out_path, width, height, purpose=purpose)
        from PIL import Image
        with Image.open(out_path) as img:
            return GeneratedImage(out_path, img.width, img.height)

    def _split_tencent_secret(self) -> tuple[str, str]:
        raw = (self.api_key or "").strip()
        if not raw:
            raise ImageGenerationError("混元生图需要腾讯云 SecretId:SecretKey，请在生图 API Key 中按这个格式填写")

        def clean(v) -> str:
            v = str(v or "").strip().strip('"').strip("'").strip()
            for label in ("SecretId", "secret_id", "secretId", "ID", "id", "SecretKey", "secret_key", "secretKey", "Key", "key"):
                for sep in (":", "：", "="):
                    prefix = label + sep
                    if v.startswith(prefix):
                        v = v[len(prefix):].strip()
            return v

        sid = skey = ""
        normalized = raw.replace("：", ":")
        if normalized.startswith("{"):
            try:
                data = json.loads(normalized)
                sid = clean(data.get("SecretId") or data.get("secret_id") or data.get("secretId") or data.get("id"))
                skey = clean(data.get("SecretKey") or data.get("secret_key") or data.get("secretKey") or data.get("key"))
            except Exception:
                sid = skey = ""
        if not (sid and skey):
            pairs = {}
            for line in normalized.replace(";", "\n").replace(",", "\n").splitlines():
                line = line.strip()
                if not line:
                    continue
                for sep in ("=", ":"):
                    if sep in line:
                        k, v = line.split(sep, 1)
                        pairs[k.strip().lower().replace("_", "")] = clean(v)
                        break
            sid = pairs.get("secretid") or pairs.get("id") or ""
            skey = pairs.get("secretkey") or pairs.get("key") or ""
        if not (sid and skey):
            for sep in (":", "|", ",", "\n"):
                if sep in normalized:
                    left, right = normalized.split(sep, 1)
                    sid, skey = clean(left), clean(right)
                    break
        if not (sid and skey):
            if normalized.strip().startswith("sk-"):
                raise ImageGenerationError("你填的是 OpenAI 兼容 sk-... Key。混元官方接口需要 SecretId + SecretKey；如果这是网关 Key，请把 Provider 改成“自定义生图接口”并填写该网关 Base URL/Model。")
            if normalized.strip().startswith("AKID"):
                raise ImageGenerationError("你只填了腾讯云 SecretId，缺少 SecretKey。请填写 SecretId:SecretKey，例如 AKIDxxxx:yyyy。")
            raise ImageGenerationError("混元生图 API Key 格式不对：请填写 SecretId:SecretKey；也支持 JSON 或 SecretId/SecretKey 多行粘贴。")
        try:
            sid.encode("ascii")
            skey.encode("ascii")
        except UnicodeEncodeError:
            raise ImageGenerationError("混元 SecretId/SecretKey 里包含中文或全角字符。请只粘贴腾讯云控制台里的英文数字密钥，不要带中文说明文字。")
        if any(ch.isspace() for ch in sid + skey):
            raise ImageGenerationError("混元 SecretId/SecretKey 里包含空格或换行，请按 SecretId:SecretKey 单行填写")
        return sid, skey

    def _hunyuan_resolution(self, width: int, height: int, purpose: str) -> str:
        """Return only TextToImageLite-supported fixed ratios.

        Tencent's official TextToImageLite Resolution accepts fixed aspect
        ratios only: 1:1, 3:4, 4:3, 9:16, 16:9. We request the nearest legal
        ratio, then normalize locally to the exact poster-layer size.
        """
        if purpose == "wordart":
            # 1440x400 is too wide for official Resolution; use 16:9 and letterbox
            # onto a black 1440x400 canvas during _normalize_size().
            return "1024:576"
        ratio = width / max(1, height)
        candidates = [
            (1.0, "1024:1024"),
            (3 / 4, "768:1024"),
            (4 / 3, "1024:768"),
            (9 / 16, "768:1365"),
            (16 / 9, "1365:768"),
        ]
        return min(candidates, key=lambda x: abs(x[0] - ratio))[1]

    def _tc3_headers(self, *, secret_id: str, secret_key: str, host: str, action: str, payload: str, region: str = "ap-guangzhou") -> dict:
        algorithm = "TC3-HMAC-SHA256"
        service = "aiart"
        version = "2022-12-29"
        timestamp = int(time.time())
        date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))
        http_request_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        canonical_headers = f"content-type:application/json; charset=utf-8\nhost:{host}\nx-tc-action:{action.lower()}\n"
        signed_headers = "content-type;host;x-tc-action"
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = "\n".join([
            http_request_method,
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            hashed_request_payload,
        ])
        credential_scope = f"{date}/{service}/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = "\n".join([algorithm, str(timestamp), credential_scope, hashed_canonical_request])

        def sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
        secret_service = sign(secret_date, service)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        authorization = (
            f"{algorithm} Credential={secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        return {
            "Authorization": authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Host": host,
            "X-TC-Action": action,
            "X-TC-Version": version,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Region": region,
        }

    def _generate_hunyuan_lite(self, prompt: str, out_path: pathlib.Path, width: int, height: int, *, purpose: str) -> GeneratedImage:
        secret_id, secret_key = self._split_tencent_secret()
        endpoint = (self.base_url or "https://aiart.tencentcloudapi.com").rstrip("/")
        host = endpoint.replace("https://", "").replace("http://", "").split("/")[0]
        action = "TextToImageLite"
        body = {
            "Prompt": prompt[:1024],
            "NegativePrompt": "文字水印, logo, extra text, blurry, low quality, distorted",
            # 不传 Resolution：混元官方服务会使用默认 1024:1024。
            # 返回后再由 _normalize_size 本地裁切/补边到海报层目标尺寸，
            # 避免不同账号/版本对 Resolution 枚举校验不一致。
            "RspImgType": "base64",
            "LogoAdd": 0,
        }
        payload = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        headers = self._tc3_headers(secret_id=secret_id, secret_key=secret_key, host=host, action=action, payload=payload)
        req = urllib.request.Request(endpoint + "/", data=payload.encode("utf-8"), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                data = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", errors="replace")[:800]
            except Exception:
                pass
            raise ImageGenerationError(f"混元生图 HTTP {e.code}：{detail or e.reason}") from e
        except Exception as e:
            raise ImageGenerationError(f"混元生图调用失败：{e}") from e
        resp = data.get("Response") or {}
        if resp.get("Error"):
            err = resp["Error"]
            raise ImageGenerationError(f"混元生图失败：{err.get('Code')} {err.get('Message')}")
        result = resp.get("ResultImage") or ""
        if result.startswith("http://") or result.startswith("https://"):
            self._download(result, out_path)
        elif result:
            out_path.write_bytes(base64.b64decode(result))
        else:
            raise ImageGenerationError(f"混元生图未返回 ResultImage：{str(data)[:500]}")
        self._normalize_size(out_path, width, height, purpose=purpose)
        from PIL import Image
        with Image.open(out_path) as img:
            return GeneratedImage(out_path, img.width, img.height)

    def _download(self, url: str, out_path: pathlib.Path):
        req = urllib.request.Request(url, headers={"User-Agent": "poster-web/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                out_path.write_bytes(r.read())
        except Exception as e:
            raise ImageGenerationError(f"下载生图结果失败：{e}") from e

    def _normalize_size(self, path: pathlib.Path, width: int, height: int, *, purpose: str):
        """Keep the skill's required dimensions stable before brief insertion."""
        from PIL import Image
        with Image.open(path) as src:
            img = src.convert("RGBA")
            if img.size == (width, height):
                img.save(path)
                return
            if purpose == "wordart":
                canvas = Image.new("RGBA", (width, height), (0, 0, 0, 255))
                ratio = min(width / img.width, height / img.height)
                nw, nh = max(1, int(img.width * ratio)), max(1, int(img.height * ratio))
                resized = img.resize((nw, nh), Image.LANCZOS)
                canvas.alpha_composite(resized, ((width - nw) // 2, (height - nh) // 2))
                canvas.convert("RGB").save(path)
                return
            ratio = max(width / img.width, height / img.height)
            nw, nh = max(1, int(img.width * ratio)), max(1, int(img.height * ratio))
            resized = img.resize((nw, nh), Image.LANCZOS)
            left = max(0, (nw - width) // 2)
            top = max(0, (nh - height) // 2)
            resized.crop((left, top, left + width, top + height)).save(path)
