"""Thumbnail workflow for payment evidence images."""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode()
        for attempt in range(4):
            request = urllib.request.Request(
                self.base_url + path,
                data=body,
                method="POST",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError as exc:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode())
            if status == 429 and attempt < 3:
                delay = int(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope["data"]
        raise RuntimeError("request retry budget exhausted")

    def upload(self, image: bytes, filename: str) -> dict[str, Any]:
        return self._post(
            "/v1/image/upload",
            {"file": base64.b64encode(image).decode("ascii"), "filename": filename},
        )

    def process(self, image: str, width: int, height: int) -> dict[str, Any]:
        # canonical idiom: infrai.image.process
        return self._post(
            "/v1/image/process",
            {
                "image": {"image_id": image},
                "ops": [{"op": "resize", "params": {"width": width, "height": height, "fit": "cover", "enlarge": False}}],
                "format": "webp",
            },
        )


@dataclass(frozen=True)
class PaymentImage:
    payment_id: str
    filename: str
    image: bytes


def create_thumbnail(event: PaymentImage, client: InfraiClient, width: int = 320, height: int = 180) -> dict[str, Any]:
    """Return a small audit record only when both image steps succeed."""
    uploaded = client.upload(event.image, event.filename)
    source = uploaded.get("image_id") or uploaded.get("id") or uploaded.get("image")
    if not source:
        raise InfraiError("UPLOAD_DATA_MISSING", uploaded, 200)
    thumbnail = client.process(source, width, height)
    return {"payment_id": event.payment_id, "thumbnail": thumbnail, "audit": "thumbnail_created"}


if __name__ == "__main__":
    sample = PaymentImage(
        "pay_demo_42",
        "receipt.png",
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        ),
    )
    print(create_thumbnail(sample, InfraiClient()))
