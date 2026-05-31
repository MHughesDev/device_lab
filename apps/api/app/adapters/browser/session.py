"""
Browser session lifecycle — pattern ported from browser-use/browser_use/browser/context.py.
Phase 02: local Chromium via Playwright. Cloud remote browser is Phase 06.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

BROWSER_CAPABILITY = {
    "observe": ["ax_tree", "screenshot"],
    "interact": ["click", "type", "navigate", "fill_form"],
    "streaming": False,
}


@dataclass
class BrowserSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    closed_at: datetime | None = None
    current_url: str = "about:blank"
    _browser: object | None = field(default=None, repr=False)
    _page: object | None = field(default=None, repr=False)

    @classmethod
    async def create(cls, device_id: str) -> "BrowserSession":
        session = cls(device_id=device_id)
        try:
            from playwright.async_api import async_playwright  # type: ignore[import]
            pw = await async_playwright().__aenter__()
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            session._browser = browser
            session._page = page
        except ImportError:
            # Playwright not installed; session is a stub
            pass
        return session

    async def navigate(self, url: str) -> None:
        if self._page is not None:
            await self._page.goto(url)  # type: ignore[attr-defined]
            self.current_url = url

    async def screenshot(self) -> bytes | None:
        if self._page is not None:
            return await self._page.screenshot()  # type: ignore[attr-defined]
        return None

    async def close(self) -> None:
        try:
            if self._browser is not None:
                await self._browser.close()  # type: ignore[attr-defined]
        except Exception:
            pass
        self.closed_at = datetime.now(UTC)

    @property
    def is_active(self) -> bool:
        return self.closed_at is None
