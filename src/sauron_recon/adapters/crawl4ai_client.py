from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable


class Crawl4AIError(RuntimeError):
    """A local Crawl4AI browser extraction failed."""


@dataclass
class Crawl4AIClient:
    """Minimal optional Crawl4AI client using normal Playwright defaults.

    The dependency is imported lazily so the core and Firecrawl-only installs do
    not require Chromium. No proxy, stealth, cookie, or anti-bot mode is used.
    """

    browser_factory: Callable[..., Any] | None = None

    def scrape(self, url: str) -> dict[str, Any]:
        try:
            return asyncio.run(self._scrape(url))
        except RuntimeError as exc:
            if "asyncio.run() cannot be called" in str(exc):
                raise Crawl4AIError("Crawl4AI sync adapter cannot run inside an active event loop") from exc
            raise
        except ImportError as exc:
            raise Crawl4AIError("Crawl4AI is not installed; install the crawler extra") from exc
        except Exception as exc:
            raise Crawl4AIError(f"Crawl4AI scrape failed: {type(exc).__name__}") from exc

    async def _scrape(self, url: str) -> dict[str, Any]:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig  # type: ignore[import-not-found]

        browser_config = BrowserConfig(headless=True, verbose=False)
        run_config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
        markdown = result.markdown
        if hasattr(markdown, "raw_markdown"):
            markdown = markdown.raw_markdown
        return {"success": True, "data": {"markdown": str(markdown or "")}}
