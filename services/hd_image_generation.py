# services/generate_hd_image.py
from typing import Dict, Any, Optional
import requests
import time

DEFAULT_TIMEOUT = 15  # seconds
RETRY_COUNT = 2
RETRY_BACKOFF = 1.5  # multiply sleep by this on each retry

def _mask_key(key: Optional[str]) -> str:
    if not key:
        return "<no-key>"
    return f"{key[:4]}...{key[-4:]}"

def generate_hd_image(
    prompt: str,
    api_key: str,
    model_version: str = "2.2",
    num_results: int = 1,
    aspect_ratio: str = "1:1",
    sync: bool = True,
    seed: Optional[int] = None,
    negative_prompt: Optional[str] = None,
    steps_num: Optional[int] = None,
    text_guidance_scale: Optional[float] = None,
    medium: Optional[str] = None,
    prompt_enhancement: bool = False,
    enhance_image: bool = False,
    content_moderation: bool = False,
    ip_signal: bool = False
) -> Dict[str, Any]:
    if not prompt:
        raise ValueError("Prompt is required for image generation")

    # prepare payload
    data = {
        "prompt": prompt,
        "num_results": max(1, min(num_results, 4)),
        "sync": bool(sync),
    }
    if negative_prompt:
        data["negative_prompt"] = negative_prompt
    if aspect_ratio:
        data["aspect_ratio"] = aspect_ratio
    if seed is not None:
        data["seed"] = int(seed)
    if steps_num is not None:
        data["steps_num"] = max(20, min(int(steps_num), 50))
    if text_guidance_scale is not None:
        data["text_guidance_scale"] = max(1.0, min(float(text_guidance_scale), 10.0))
    if medium:
        data["medium"] = medium
    if prompt_enhancement:
        data["prompt_enhancement"] = True
    if enhance_image:
        data["enhance_image"] = True
    if content_moderation:
        data["content_moderation"] = True
    if ip_signal:
        data["ip_signal"] = True

    url = f"https://engine.prod.bria-api.com/v1/text-to-image/hd/{model_version}"

    # Try headers many APIs accept either api_token or Authorization Bearer
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    # Prefer the provider-specific header if expected; keep Authorization as fallback
    if api_key:
        headers["api_token"] = api_key
        headers["Authorization"] = f"Bearer {api_key}"

    # minimal retry
    attempt = 0
    backoff = 1.0
    last_exc = None

    while attempt <= RETRY_COUNT:
        try:
            # Don't print the API key — only masked form for debug
            print(f"[generate_hd_image] Request to {url} attempt={attempt} api_key={_mask_key(api_key)}")
            resp = requests.post(url, headers=headers, json=data, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            # parse JSON (might raise)
            return resp.json()
        except requests.HTTPError as http_err:
            # For 4xx errors, don't retry except maybe 429
            status = getattr(http_err.response, "status_code", None)
            text = getattr(http_err.response, "text", "")
            if status and 400 <= status < 500 and status != 429:
                raise Exception(f"HD image generation failed (HTTP {status}): {text}")
            # else allow retry for 429/5xx/network
            last_exc = http_err
        except requests.RequestException as req_err:
            last_exc = req_err
        except ValueError as json_err:
            # JSON decode error
            raise Exception(f"HD image generation returned non-JSON response: {json_err}")

        # retry backoff
        attempt += 1
        if attempt <= RETRY_COUNT:
            sleep_time = backoff * (RETRY_BACKOFF ** attempt)
            print(f"[generate_hd_image] transient error: {last_exc}. Retrying in {sleep_time:.1f}s...")
            time.sleep(sleep_time)

    # all retries failed
    raise Exception(f"HD image generation failed after {RETRY_COUNT+1} attempts: {last_exc}")
