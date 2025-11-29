# services/erase_foreground.py
from typing import Dict, Any, Optional
import requests
import base64
import time

DEFAULT_TIMEOUT = 15
RETRY_COUNT = 2
RETRY_BACKOFF = 1.5

def _mask_key(key: Optional[str]) -> str:
    if not key:
        return "<no-key>"
    return f"{key[:4]}...{key[-4:]}"


def erase_foreground(
    api_key: str,
    image_data: Optional[bytes] = None,
    image_url: Optional[str] = None,
    content_moderation: bool = False
) -> Dict[str, Any]:
    """
    Erase the foreground from an image and generate the background behind it.
    
    Args:
        api_key: Bria AI API key
        image_data: Image bytes
        image_url: Public image URL
        content_moderation: Enable content moderation
    """
    
    if not api_key:
        raise ValueError("API key is missing")

    if not (image_data or image_url):
        raise ValueError("Either image_data or image_url must be provided")

    url = "https://engine.prod.bria-api.com/v1/erase_foreground"

    # Preferred header format + Authorization fallback
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "api_token": api_key,
        "Authorization": f"Bearer {api_key}"
    }

    # Build payload
    data = {
        "content_moderation": content_moderation
    }

    if image_url:
        data["image_url"] = image_url
    else:
        data["file"] = base64.b64encode(image_data).decode("utf-8")

    # Retry loop
    attempt = 0
    backoff = 1.0
    last_exc = None

    while attempt <= RETRY_COUNT:
        try:
            print(
                f"[erase_foreground] Request → {url} attempt={attempt} "
                f"api_key={_mask_key(api_key)}"
            )

            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=DEFAULT_TIMEOUT
            )

            # Raise for HTTP error
            response.raise_for_status()

            # Parse/validate JSON
            return response.json()

        except requests.HTTPError as http_err:
            status = getattr(http_err.response, "status_code", None)
            text = getattr(http_err.response, "text", "")

            # For non-retryable 4xx errors (except 429), break immediately
            if status and 400 <= status < 500 and status != 429:
                raise Exception(
                    f"Erase foreground failed (HTTP {status}): {text}"
                )

            last_exc = http_err

        except requests.RequestException as req_err:
            last_exc = req_err

        except ValueError as json_err:
            raise Exception(f"Non-JSON response: {json_err}")

        # Retry for network/5xx/429
        attempt += 1
        if attempt <= RETRY_COUNT:
            sleep_time = backoff * (RETRY_BACKOFF ** attempt)
            print(
                f"[erase_foreground] transient error: {last_exc}. "
                f"Retrying in {sleep_time:.1f}s..."
            )
            time.sleep(sleep_time)

    # All retries failed
    raise Exception(
        f"Erase foreground failed after {RETRY_COUNT + 1} attempts: {last_exc}"
    )


__all__ = ["erase_foreground"]
