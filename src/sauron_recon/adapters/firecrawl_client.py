from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class FirecrawlError(RuntimeError):
    """An upstream Firecrawl request failed after bounded retries."""


@dataclass(frozen=True)
class FirecrawlClient:
    base_url: str
    api_key: str | None = None
    timeout_seconds: float = 30.0
    max_attempts: int = 3
    backoff_seconds: float = 0.25
    opener: Callable[..., Any] = urlopen
    sleeper: Callable[[float], None] = time.sleep

    def __post_init__(self) -> None:
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("Firecrawl base_url must use http or https")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        payload = self._post("/v1/search", {"query": query, "limit": limit})
        data = payload.get("data", [])
        if not isinstance(data, list):
            raise FirecrawlError("Firecrawl search response data is not a list")
        return [item for item in data if isinstance(item, dict) and isinstance(item.get("url"), str)]

    def scrape(self, url: str) -> dict[str, Any]:
        return self._post("/v1/scrape", {"url": url, "formats": ["markdown"]})

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            f"{self.base_url.rstrip('/')}{path}",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                with self.opener(request, timeout=self.timeout_seconds) as response:
                    raw = response.read()
                parsed = json.loads(raw.decode("utf-8"))
                if not isinstance(parsed, dict) or parsed.get("success") is False:
                    raise FirecrawlError("Firecrawl returned an unsuccessful response")
                return parsed
            except HTTPError as exc:
                last_error = exc
                if exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                    break
            except (URLError, TimeoutError, json.JSONDecodeError, FirecrawlError) as exc:
                last_error = exc
            if attempt + 1 < self.max_attempts:
                self.sleeper(self.backoff_seconds * (2**attempt))
        raise FirecrawlError(f"Firecrawl request failed: {last_error}") from last_error
