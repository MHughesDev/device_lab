"""
Browser-specific MCP tools.
These tools are only meaningful for family='browser' devices.
They expose Playwright capabilities that have no desktop equivalent.
"""
from __future__ import annotations

from app.mcp.gateway import mcp


def _get_page(device_id: str):
    """Return the Playwright page for this browser device, or None."""
    from app.adapters.browser.adapter import _sessions
    session = _sessions.get(device_id)
    if session and session._page is not None:
        return session._page
    return None


def _get_context(device_id: str):
    """Return the Playwright browser context, or None."""
    from app.adapters.browser.adapter import _sessions
    session = _sessions.get(device_id)
    if session and session._browser is not None:
        return getattr(session._browser, "_impl_obj", session._browser)
    return None


@mcp.tool()
def navigate(device_id: str, url: str) -> dict:
    """Navigate the browser to a URL. Essential first step for browser devices."""
    import asyncio
    page = _get_page(device_id)
    if not page:
        return {"success": False, "error": "No active browser session"}
    asyncio.get_event_loop().run_until_complete(page.goto(url))
    return {"success": True, "url": url}


@mcp.tool()
def new_tab(device_id: str, url: str = "about:blank") -> dict:
    """Open a new browser tab and optionally navigate to a URL."""
    import asyncio
    from app.adapters.browser.adapter import _sessions
    session = _sessions.get(device_id)
    if not session or session._browser is None:
        return {"success": False, "error": "No active browser session"}
    async def _new():
        page = await session._browser.new_page()
        if url != "about:blank":
            await page.goto(url)
        return page
    asyncio.get_event_loop().run_until_complete(_new())
    return {"success": True, "url": url}


@mcp.tool()
def close_tab(device_id: str) -> dict:
    """Close the currently active tab."""
    import asyncio
    page = _get_page(device_id)
    if not page:
        return {"success": False, "error": "No active browser session"}
    asyncio.get_event_loop().run_until_complete(page.close())
    return {"success": True}


@mcp.tool()
def list_tabs(device_id: str) -> dict:
    """List all open browser tabs with their URLs and titles."""
    import asyncio
    from app.adapters.browser.adapter import _sessions
    session = _sessions.get(device_id)
    if not session or session._browser is None:
        return {"success": False, "error": "No active browser session"}
    async def _list():
        pages = session._browser.pages
        return [{"index": i, "url": p.url, "title": await p.title()} for i, p in enumerate(pages)]
    tabs = asyncio.get_event_loop().run_until_complete(_list())
    return {"success": True, "tabs": tabs, "count": len(tabs)}


@mcp.tool()
def switch_tab(device_id: str, index: int) -> dict:
    """Switch to a browser tab by its index (from list_tabs)."""
    import asyncio
    from app.adapters.browser.adapter import _sessions, BrowserAdapter
    session = _sessions.get(device_id)
    if not session or session._browser is None:
        return {"success": False, "error": "No active browser session"}
    pages = session._browser.pages
    if index >= len(pages):
        return {"success": False, "error": f"Tab index {index} out of range (have {len(pages)})"}
    async def _switch():
        await pages[index].bring_to_front()
        session._page = pages[index]
    asyncio.get_event_loop().run_until_complete(_switch())
    return {"success": True, "index": index, "url": pages[index].url}


@mcp.tool()
def get_console_logs(device_id: str, level: str = "all") -> dict:
    """
    Return browser console messages captured since session start.
    level: all | log | warn | error
    Note: messages are accumulated in session._console_msgs if the session
    was started with console listener enabled.
    """
    from app.adapters.browser.adapter import _sessions
    session = _sessions.get(device_id)
    if not session:
        return {"success": False, "error": "No active browser session"}
    msgs = getattr(session, "_console_msgs", [])
    if level != "all":
        msgs = [m for m in msgs if m.get("type") == level]
    return {"success": True, "messages": msgs, "count": len(msgs)}


@mcp.tool()
def get_network_requests(device_id: str) -> dict:
    """
    Return network requests captured since session start.
    Returns list of {url, method, status, resource_type}.
    """
    from app.adapters.browser.adapter import _sessions
    session = _sessions.get(device_id)
    if not session:
        return {"success": False, "error": "No active browser session"}
    reqs = getattr(session, "_network_requests", [])
    return {"success": True, "requests": reqs, "count": len(reqs)}


@mcp.tool()
def handle_dialog(device_id: str, accept: bool = True, text: str = "") -> dict:
    """
    Accept or dismiss the next browser dialog (alert, confirm, prompt).
    For prompt dialogs, text is used as the input value.
    """
    from app.adapters.browser.adapter import _sessions
    session = _sessions.get(device_id)
    if not session or session._page is None:
        return {"success": False, "error": "No active browser session"}

    async def _handler(dialog):
        if accept:
            await dialog.accept(text or dialog.default_value)
        else:
            await dialog.dismiss()

    session._page.once("dialog", _handler)
    return {"success": True, "configured": True, "accept": accept}
